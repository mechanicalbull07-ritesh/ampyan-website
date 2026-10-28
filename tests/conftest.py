"""Tests use newly created local state and cannot connect to remote services."""
import os,socket,tempfile,json
from pathlib import Path
import pytest
ROOT=Path(tempfile.mkdtemp(prefix='ampyan-website-tests-'))
for key in list(os.environ):
    if any(part in key for part in ('DATABASE_URL','PGHOST','PGPASSWORD','PGUSER','PGDATABASE')):
        os.environ.pop(key,None)
# Rebuild only the explicitly proven disposable traffic URL after sanitizing inherited URLs.
if os.environ.get('AMPYAN_WEBSITE_TEST_PG_META'):
    meta_path=Path(os.environ['AMPYAN_WEBSITE_TEST_PG_META']).resolve()
    assert str(meta_path).startswith('/private/tmp/ampyan-traffic-quality-pg')
    meta=json.loads(meta_path.read_text())
    local_socket=Path(meta['socket']).resolve()
    assert local_socket.is_relative_to(meta_path.parent) and local_socket.is_dir()
    assert meta['user']=='ampyan_website_test' and meta['port']==55459
    os.environ['TRAFFIC_TEST_DATABASE_URL']=f"postgresql+psycopg2://{meta['user']}@/ampyan_traffic_quality_test?host={local_socket}&port={meta['port']}"
os.environ.update(ENV='test',RENDER='false',DATABASE_URL='sqlite:///'+str(ROOT/'website.sqlite'),
 SECRET_KEY='synthetic-website-test-session-key',ENABLE_BACKGROUND_DB_INIT='false',ENABLE_REQUEST_DB_INIT='false',
 ENABLE_MANAGED_PERSONA_MIGRATION='false',ANALYTICS_ENABLED='false',AMPYAN_API_BASE_URL='http://127.0.0.1:1',
 ANALYTICS_FALLBACK_LOG=str(ROOT/'analytics.log'))
original_connect=socket.socket.connect
original_connect_ex=socket.socket.connect_ex
def guarded_connect(self,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','::1','localhost'):
        raise OSError('Test blocked a non-local connection')
    return original_connect(self,address)
def guarded_connect_ex(self,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','::1','localhost'):
        raise OSError('Test blocked a non-local connection')
    return original_connect_ex(self,address)
socket.socket.connect=guarded_connect
socket.socket.connect_ex=guarded_connect_ex

@pytest.fixture(autouse=True)
def website_test_isolation(monkeypatch):
    import app as website
    from flask.testing import FlaskClient
    from flask_wtf.csrf import generate_csrf
    class CsrfClient(FlaskClient):
        def open(self,*args,**kwargs):
            if kwargs.get('method','GET').upper() not in ('GET','HEAD','OPTIONS'):
                with self.session_transaction() as saved:
                    with website.app.test_request_context():
                        from flask import session
                        session.update(saved)
                        token=generate_csrf()
                        saved['csrf_token']=session['csrf_token']
                headers=dict(kwargs.get('headers') or {})
                headers.setdefault('X-CSRFToken',token)
                kwargs['headers']=headers
            return super().open(*args,**kwargs)
    monkeypatch.setattr(website.app,'test_client_class',CsrfClient)
    monkeypatch.setitem(website.app.config,'TESTING',True)
    monkeypatch.setitem(website.app.config,'WTF_CSRF_ENABLED',True)
    monkeypatch.setitem(website.app.config,'AMPYAN_API_BASE_URL','http://127.0.0.1:1')
