"""Disposable integration server. Explicit frozen checkout and new test DB only."""
import os,sys
from pathlib import Path
from werkzeug.serving import make_server
root=Path(sys.argv[1]).resolve()
backend=Path(sys.argv[2]).resolve()
if not str(root).startswith(('/private/tmp/','/tmp/')):
    raise SystemExit('Synthetic state must be disposable')
sys.path.insert(0,str(backend))
for key in list(os.environ):
    if any(part in key for part in ('DATABASE_URL','POSTGRES','PGHOST','PGUSER','PGPASSWORD','PGDATABASE','PGPORT')):
        os.environ.pop(key,None)
os.environ.update(ENV='test',RENDER='false',AMPYAN_SCHEMA_MANAGED_EXTERNALLY='1',
 DATABASE_URL='sqlite:///'+str(root/'backend.sqlite'),
 AUTH_SIGNING_KEY='synthetic-website-integration-key-only-not-for-real-accounts',
 SECRET_KEY='synthetic-backend-test-key')
meta_path=os.environ.get('AMPYAN_WEBSITE_TEST_PG_META')
if meta_path:
    import json,psycopg2
    meta=json.loads(Path(meta_path).read_text())
    assert Path(meta['data']).resolve().is_relative_to(Path('/tmp').resolve())
    assert Path(meta['socket']).resolve().is_relative_to(Path('/tmp').resolve())
    assert meta['database']=='ampyan_website_synthetic'
    conn=psycopg2.connect(host=meta['socket'],port=meta['port'],user=meta['user'],dbname=meta['database'])
    with conn.cursor() as q:
        q.execute("SELECT current_setting('data_directory'),current_setting('listen_addresses'),inet_server_addr()")
        proof=q.fetchone()
        assert Path(proof[0]).resolve()==Path(meta['data']).resolve() and proof[1]=='' and proof[2] is None
    conn.close()
    os.environ['DATABASE_URL']=f"postgresql+psycopg2://{meta['user']}@/{meta['database']}?host={meta['socket']}&port={meta['port']}"
import app as a
from tests.support.fixture_factory import seed
with a.app.app_context():
    if a.db.engine.dialect.name == 'sqlite':
        from sqlalchemy import event
        @event.listens_for(a.db.engine, 'connect')
        def sqlite_foreign_keys(connection, record):
            connection.execute('PRAGMA foreign_keys=ON')
    a.db.create_all()
    if not a.db.session.get(a.User,9001):
        seed(a)
        import bcrypt
        for uid in (9001,9901):
            a.db.session.get(a.User,uid).password=bcrypt.hashpw(b'local-test-only-123',bcrypt.gensalt()).decode()
        # A vehicle belonging to a different account, with no shared numeric website ID.
        a.db.session.add(a.Vehicle(id=301,user_id=9901,brand='Synthetic',model='Other owner',fuel_type='Petrol',
            transmission='UNKNOWN',year='2020',mileage=100,running_per_day=0,current_odometer_km=100))
        a.db.session.commit()
        if meta_path:
            from sqlalchemy import text
            for table in ('user','vehicle','service_record','odometer_confirmation','running_profile_history','mileage_prompt_state'):
                a.db.session.execute(text("SELECT setval(pg_get_serial_sequence(:name, 'id'),COALESCE((SELECT MAX(id) FROM \""+table+"\"),1),EXISTS(SELECT 1 FROM \""+table+"\"))"),{'name':table})
            a.db.session.commit()
server=make_server('127.0.0.1',0,a.app,threaded=True)
(root/'port').write_text(str(server.server_port))
server.serve_forever()
