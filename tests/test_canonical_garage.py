"""HTTP integration with the immutable P4B backend; all records are synthetic."""
import json,os,sqlite3,subprocess,sys,time
from pathlib import Path
from uuid import uuid4
import pytest,requests
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash
import app as website
from models.models import db,User,Car
from services import canonical_garage_client as api

RC=os.environ.get('AMPYAN_BACKEND_RC_SHA','e73bbb53f95f16897c74375d1432bd4e563f6427')

@pytest.fixture(scope='module')
def backend(tmp_path_factory):
    source=os.environ.get('AMPYAN_BACKEND_RC_PATH')
    if not source:
        pytest.fail('Set AMPYAN_BACKEND_RC_PATH to the frozen P4B checkout for required integration tests')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==RC
    state=tmp_path_factory.mktemp('canonical-backend')
    python=os.environ.get('AMPYAN_BACKEND_TEST_PYTHON',sys.executable)
    log=(state/'server.log').open('w')
    process=None
    def start():
        nonlocal process
        (state/'port').unlink(missing_ok=True)
        process=subprocess.Popen([python,str(Path(__file__).with_name('backend_contract_server.py')),str(state),source],
                                 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=log,stderr=log)
        for _ in range(150):
            if (state/'port').exists():return 'http://127.0.0.1:'+(state/'port').read_text()
            if process.poll() is not None:pytest.fail((state/'server.log').read_text())
            time.sleep(.05)
        pytest.fail('Disposable backend failed to start')
    value={'url':start(),'state':state,'pg':os.environ.get('AMPYAN_WEBSITE_TEST_PG_META'),'client_uses':0}
    def restart():
        process.terminate();process.wait(timeout=10)
        value['url']=start()
        value['client_uses']=0
    value['restart']=restart
    try:yield value
    finally:
        if process and process.poll() is None:process.terminate();process.wait(timeout=10)
        log.close()

def csrf(client):
    with client.session_transaction() as saved:
        with website.app.test_request_context():
            from flask import session
            session.update(saved);token=generate_csrf();saved['csrf_token']=session['csrf_token']
    return {'X-CSRFToken':token}

@pytest.fixture
def client(backend,monkeypatch):
    # Keep the production rate limiter intact. Independent test clients use
    # bounded server lifetimes, retaining the same synthetic database. A test
    # can perform several login exchanges, so counting ten clients is not
    # a reliable budget for the real 30/minute login limiter. Each independent
    # client starts a new server lifetime; explicit restart tests remain intact.
    if backend['client_uses'] >= 1:
        backend['restart']()
    backend['client_uses'] += 1
    monkeypatch.setitem(website.app.config,'AMPYAN_API_BASE_URL',backend['url'])
    monkeypatch.setenv('ANALYTICS_ENABLED','false')
    monkeypatch.setattr(website,'safe_track_page_visit',lambda:False)
    with website.app.app_context():
        db.create_all()
        for uid,backendid in ((41,9001),(42,9901)):
            if not db.session.get(User,uid):
                db.session.add(User(id=uid,username=f'web{uid}',email=f'acceptance-{backendid}@example.invalid',
                    password=generate_password_hash('local-test-only-123'),role='user',is_banned=False,email_verified=True))
        db.session.commit()
    website.rate_limit_hits.clear()
    c=FlaskClient(website.app,website.app.response_class)
    response=c.post('/login',data={'username':'web41','password':'local-test-only-123'},headers=csrf(c))
    assert response.status_code==302
    with c.session_transaction() as saved:assert (saved.get('garage_credentials') or {}).get('website_user')=='41', {'api_base_matches':website.app.config.get('AMPYAN_API_BASE_URL')==backend['url'],'website_authenticated':saved.get('_user_id')=='41'}
    return c

def backend_auth(backend,user=9001):
    r=requests.post(backend['url']+'/login',json={'email':f'acceptance-{user}@example.invalid','password':'local-test-only-123'})
    assert r.status_code==200
    return {'Authorization':'Bearer '+r.json()['access_token']}

from contextlib import contextmanager
@contextmanager
def connection(backend):
    if not backend.get('pg'):
        with sqlite3.connect(backend['state']/'backend.sqlite') as conn:yield conn
        return
    import psycopg2
    meta=json.loads(Path(backend['pg']).read_text())
    assert Path(meta['socket']).resolve().is_relative_to(Path('/tmp').resolve())
    raw=psycopg2.connect(host=meta['socket'],port=meta['port'],user=meta['user'],dbname=meta['database'])
    class Connection:
        def execute(self,sql,args=()):
            cursor=raw.cursor();cursor.execute(sql.replace('?','%s'),args);return cursor
        def commit(self):raw.commit()
    try:
        yield Connection()
        raw.commit()
    finally:raw.close()

def snapshot(backend):
    with connection(backend) as conn:
        query="SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename" if backend.get('pg') else "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        tables=[r[0] for r in conn.execute(query)]
        return {t:sorted(conn.execute('SELECT * FROM "'+t+'"').fetchall(),key=repr) for t in tables}

@pytest.mark.parametrize('car,target,count',[(201,19240.91,18),(202,105000,18),(203,35000,22),(204,65000,24),(205,45000,19),(206,55000,25),(207,75000,25)])
def test_canonical_matrix_readonly_and_labels(client,backend,car,target,count):
    before=snapshot(backend)
    r=client.get(f'/garage-dashboard?car_id={car}')
    assert r.status_code==200
    html=r.get_data(as_text=True)
    assert html.count('data-checklist-item')==count
    assert f'{target:,.2f}'.rstrip('0').rstrip('.') in html
    assert 'Service Item' not in html and 'Parts Watchlist' not in html and 'MASTER_V1' not in html
    assert 'pdf_page' not in html and 'Component Health' not in html
    if car==207:assert 'e-CVT' in html and 'Engine Oil' in html
    assert snapshot(backend)==before


@pytest.mark.parametrize('route', ['/garage','/garage-dashboard?car_id=201','/edit-car/201','/garage/cars/201/services','/api/cars/201'])
def test_unauthenticated_forged_owner_rejected(backend,route):
    c=FlaskClient(website.app,website.app.response_class)
    r=c.get(route,headers={'X-AMPYAN-USER-ID':'9001'})
    assert r.status_code in (302,401)


def test_forged_header_cannot_change_authenticated_identity(client):
    r=client.get('/api/cars',headers={'X-AMPYAN-USER-ID':'9901'})
    assert r.status_code==200
    assert 201 in [c['id'] for c in r.json['cars']]
    assert 301 not in [c['id'] for c in r.json['cars']]


@pytest.mark.parametrize('token',['invalid','expired.invalid.signature'])
def test_invalid_credentials_fail_explicitly(client,token):
    with client.session_transaction() as saved:saved['garage_credentials']['token']=token;saved.modified=True
    r=client.get('/garage-dashboard?car_id=201')
    assert r.status_code==401 and b'Sign in to Garage again' in r.data
    assert b'data-checklist-item' not in r.data


@pytest.mark.parametrize('status',[401,403,404,409,400,422,503])
def test_upstream_errors_never_fallback(client,monkeypatch,status):
    class Response:
        status_code=status
    monkeypatch.setattr(api.requests,'request',lambda *a,**k:Response())
    r=client.get('/garage-dashboard?car_id=201')
    assert r.status_code==status
    assert b'data-checklist-item' not in r.data


def test_restart_same_matrix(client,backend,monkeypatch):
    before=client.get('/garage-dashboard?car_id=207').get_data(as_text=True)
    backend['restart']()
    monkeypatch.setitem(website.app.config,'AMPYAN_API_BASE_URL',backend['url'])
    after=client.get('/garage-dashboard?car_id=207').get_data(as_text=True)
    assert before.count('data-checklist-item')==after.count('data-checklist-item')==25
    assert '75,000' in before and '75,000' in after


def test_auth_expiry_with_valid_signature(client):
    from itsdangerous import URLSafeTimedSerializer,TimestampSigner
    key='synthetic-website-integration-key-only-not-for-real-accounts'
    codec=URLSafeTimedSerializer(key,salt='ampyan-access-v1')
    class ExpiredSigner(TimestampSigner):
        def get_timestamp(self):return 1
    with client.session_transaction() as saved:
        claims=codec.loads(saved['garage_credentials']['token'])
        saved['garage_credentials']['token']=URLSafeTimedSerializer(key,salt='ampyan-access-v1',signer=ExpiredSigner).dumps(claims)
        saved.modified=True
    assert client.get('/garage').status_code==401


def test_profile_sync_uses_only_bearer(client,backend):
    headers=backend_auth(backend)
    r=client.post('/api/profile',json={'mobile':'0000000000','user_id':9901},headers=csrf(client))
    assert r.status_code==200
    # Inspect only these synthetic accounts to ensure the forged owner did not redirect the write.
    with connection(backend) as conn:
        assert conn.execute('SELECT phone FROM "user" WHERE id=9001').fetchone()[0]=='0000000000'
        assert conn.execute('SELECT phone FROM "user" WHERE id=9901').fetchone()[0]!='0000000000'


def test_backend_unavailable_does_not_use_legacy_car(client,monkeypatch):
    def unavailable(*args,**kwargs):raise requests.ConnectionError('synthetic outage')
    monkeypatch.setattr(api.requests,'request',unavailable)
    response=client.get('/garage-dashboard?car_id=201')
    assert response.status_code==503
    assert b'No local health estimate has been substituted' in response.data
    assert b'data-checklist-item' not in response.data


def test_explicit_new_garage_registration_does_not_claim_existing_account(client,backend):
    with website.app.app_context():
        user=User(username='new-'+uuid4().hex[:12],email=uuid4().hex+'@example.invalid',
            password=generate_password_hash('local-test-only-123'),role='user',is_banned=False,email_verified=True)
        db.session.add(user);db.session.commit();uid=user.id
    with client.session_transaction() as saved:
        saved['_user_id']=str(uid);saved.pop('garage_credentials',None)
    assert client.get('/garage').status_code==200
    assert client.post('/garage/connect',headers=csrf(client),data={'password':'local-test-only-123','create_account':'yes'}).status_code==302
    assert client.get('/api/cars').json['cars']==[]
    before=snapshot(backend)
    # A second registration attempt must not overwrite or adopt an existing account.
    assert client.post('/garage/connect',headers=csrf(client),data={'password':'another-password-123','create_account':'yes'}).status_code==400
    assert snapshot(backend)==before


def test_session_binding_rejects_another_website_user(client,backend):
    with client.session_transaction() as saved:saved['_user_id']='42'
    before=snapshot(backend)
    assert client.get('/api/cars').status_code==401
    assert snapshot(backend)==before


def test_logout_clears_bearer_and_selected_car(client):
    assert client.post('/set-default-car/201',headers=csrf(client)).status_code==302
    with client.session_transaction() as saved:assert saved['garage_selected']==201
    assert client.post('/logout',headers=csrf(client)).status_code==302
    with client.session_transaction() as saved:
        assert 'garage_credentials' not in saved and 'garage_selected' not in saved
    assert client.get('/api/cars').status_code==401
