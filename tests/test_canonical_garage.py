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

RC='df045fc46b89d0a56819c67d4279821a1f6f8466'

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
    # bounded server lifetimes, retaining the same synthetic database.
    if backend['client_uses'] >= 10:
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
    with c.session_transaction() as saved:assert saved['garage_credentials']['website_user']=='41'
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

@pytest.mark.parametrize('route,method', [('/garage-dashboard?car_id=301','GET'),('/edit-car/301','GET'),('/garage/cars/301/services','GET'),('/delete-car/301','POST'),('/api/cars/301','DELETE')])
def test_cross_account(client,backend,route,method):
    before=snapshot(backend)
    r=client.open(route,method=method,headers={**csrf(client),'X-AMPYAN-USER-ID':'9901'})
    assert r.status_code==404
    assert snapshot(backend)==before

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

def test_csrf_and_no_mutation_get(client,backend):
    before=snapshot(backend)
    for url in ('/delete-car/201','/set-default-car/201','/logout','/admin/news/delete/1','/admin/delete-user/1','/upvote/1'):
        assert client.get(url).status_code==405
    assert client.post('/delete-car/201').status_code==400
    assert client.post('/delete-car/201',headers={'X-CSRFToken':'forged'}).status_code==400
    assert client.post('/api/cars/201',headers={'Authorization':'Bearer forged'}).status_code in (400,405)
    assert snapshot(backend)==before
    r=client.post('/set-default-car/201',headers=csrf(client))
    assert r.status_code==302

def create_car(client):
    r=client.post('/add-car',headers=csrf(client),data={'brand':'Synthetic','model':'Website test','fuel_type':'Petrol',
        'registration_year':'2020','current_odometer_km':'1000'})
    assert r.status_code==302
    return max(c['id'] for c in client.get('/api/cars').json['cars'])

def test_legacy_unknown_and_protected_inputs(client,backend):
    cid=create_car(client)
    data=client.get(f'/api/cars/{cid}').json['car']
    assert data['transmission']=='UNKNOWN'
    before=snapshot(backend)
    assert client.get(f'/edit-car/{cid}').status_code==200
    assert snapshot(backend)==before
    r=client.get(f'/garage-dashboard?car_id={cid}')
    assert b'Baseline' in r.data or b'baseline' in r.data
    r=client.patch(f'/api/cars/{cid}',headers=csrf(client),json={'user_id':9901,'main_service_baseline_confirmed':True})
    assert r.status_code==400
    assert snapshot(backend)==before

def test_inputs_driving_and_mi_protections(client,backend):
    cid=create_car(client)
    url=f'/edit-car/{cid}'
    for tx in ('AMT','UNKNOWN'):
        r=client.post(url,headers=csrf(client),data={'section':'inputs','transmission':tx})
        assert r.status_code==302
        assert client.get(f'/api/cars/{cid}').json['car']['transmission']==tx
    r=client.post(url,headers=csrf(client),data={'section':'driving','driving_state':'KNOWN','city_percent':'50','highway_percent':'50'})
    assert r.status_code==302
    assert client.get(f'/api/cars/{cid}').json['car']['driving_input']['state']=='KNOWN'
    r=client.post(url,headers=csrf(client),data={'section':'running','weekday_km':'20','weekend_km':'10','effective_date':'2026-01-01','idempotency_key':str(uuid4())})
    assert r.status_code==302
    from datetime import datetime,timezone
    payload={'section':'odometer','actual_km':'1000','user_confirmed':'yes','observed_at':datetime.now(timezone.utc).isoformat(),'idempotency_key':str(uuid4())}
    assert client.post(url,headers=csrf(client),data=payload).status_code==302
    payload.update(actual_km='50000',idempotency_key=str(uuid4()),observed_at=datetime.now(timezone.utc).isoformat())
    assert client.post(url,headers=csrf(client),data=payload).status_code==400
    payload['jump_acknowledged']='yes'
    assert client.post(url,headers=csrf(client),data=payload).status_code==302

def test_service_semantics_and_complete_history_deletion(client,backend):
    cid=create_car(client)
    from datetime import datetime,timezone,date
    now=datetime.now(timezone.utc)
    headers=backend_auth(backend)
    base=backend['url']+f'/api/garage/cars/{cid}'
    for kind,payload in [('confirmations',{'actual_km':1000,'observed_at':now.isoformat(),'source':'MANUAL','user_confirmed':True,'timezone':'UTC','idempotency_key':str(uuid4())}),
        ('profiles',{'weekday_km':20,'weekend_km':10,'effective_date':date.today().isoformat(),'timezone':'UTC','provenance':'USER_PROVIDED','idempotency_key':str(uuid4())}),
        ('prompt',{'action':'LATER'})]:
        assert requests.post(base+'/mileage/'+kind,headers=headers,json=payload).status_code==200
    service={'service_type':'Periodic service','service_date':date.today().isoformat(),'odometer_km':'500','qualifying_main_service':'yes'}
    assert client.post(f'/garage/cars/{cid}/services',headers=csrf(client),data=service).status_code==302
    target=requests.get(base+'/health?read_only=1',headers=headers).json()['health']['next_service_km']
    service.update(service_type='Brake work',odometer_km='600');service.pop('qualifying_main_service')
    assert client.post(f'/garage/cars/{cid}/services',headers=csrf(client),data=service).status_code==302
    health=requests.get(base+'/health?read_only=1',headers=headers).json()
    assert health['health']['next_service_km']==target
    assert health['car']['current_odometer_km']==1000
    before=snapshot(backend)
    assert client.post(f'/delete-car/{cid}',headers=csrf(client)).status_code==302
    after=snapshot(backend)
    for table in ('odometer_confirmation','running_profile_history','mileage_prompt_state','service_record','car_health_snapshot'):
        with connection(backend) as conn:
            assert conn.execute(f'SELECT count(*) FROM {table} WHERE car_id=?',(cid,)).fetchone()[0]==0
    assert requests.get(base,headers=headers).status_code==404
    # Frozen acceptance fixtures still exist and have identical per-car history.
    for table in ('vehicle','odometer_confirmation','running_profile_history','mileage_prompt_state','service_record','car_health_snapshot'):
        with connection(backend) as conn:
            columns=[d[0] for d in conn.execute('SELECT * FROM "'+table+'" LIMIT 0').description]
        owner_index=columns.index('id' if table=='vehicle' else 'car_id')
        assert [row for row in before[table] if row[owner_index]!=cid] == after[table]
    assert client.get('/garage-dashboard?car_id=207').get_data(as_text=True).count('data-checklist-item')==25

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

@pytest.mark.parametrize('route,data',[('/garage/cars/301/services',{'service_type':'Periodic service','service_date':'2026-01-01','odometer_km':'0'}),
 ('/edit-car/301',{'section':'odometer','actual_km':'0','user_confirmed':'yes'}),
 ('/edit-car/301',{'section':'running','weekday_km':'10','weekend_km':'10'})])
def test_cross_account_writes_rejected(client,backend,route,data):
    before=snapshot(backend)
    assert client.post(route,headers={**csrf(client),'X-AMPYAN-USER-ID':'9901'},data=data).status_code==404
    assert snapshot(backend)==before

def test_backend_409_delete_preserves_all_rows(client,backend):
    cid=create_car(client)
    # Deliberately inconsistent synthetic owner reference; no real database is used.
    with connection(backend) as conn:
        conn.execute('INSERT INTO service_record(user_id,car_id,service_date,odometer_km,service_type,parts_replaced,labour_cost,parts_cost,total_cost,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                     (9901,cid,'2026-01-01',100,'Brake work','[]',0,0,0,'2026-01-01','2026-01-01'));conn.commit()
    before=snapshot(backend)
    r=client.post(f'/delete-car/{cid}',headers=csrf(client))
    assert r.status_code==409 and b'Conflicting records' in r.data
    assert snapshot(backend)==before

def test_profile_sync_uses_only_bearer(client,backend):
    headers=backend_auth(backend)
    r=client.post('/api/profile',json={'mobile':'0000000000','user_id':9901},headers=csrf(client))
    assert r.status_code==200
    # Inspect only these synthetic accounts to ensure the forged owner did not redirect the write.
    with connection(backend) as conn:
        assert conn.execute('SELECT phone FROM "user" WHERE id=9001').fetchone()[0]=='0000000000'
        assert conn.execute('SELECT phone FROM "user" WHERE id=9901').fetchone()[0]!='0000000000'

def test_component_work_cannot_qualify(client,backend):
    cid=create_car(client);before=snapshot(backend)
    r=client.post(f'/garage/cars/{cid}/services',headers=csrf(client),data={'service_type':'Brake work',
        'service_date':'2026-01-01','odometer_km':'500','qualifying_main_service':'yes'})
    assert r.status_code==400 and snapshot(backend)==before

@pytest.mark.parametrize('tx,expected,excluded',[
 ('AMT','AMT System',['CVT','e-CVT','DCT']),('CVT','CVT',['AMT System','e-CVT','DCT']),
 ('DCT','DCT',['AMT System','e-CVT','CVT']),('TORQUE_CONVERTER_AT','Torque-converter AT',['AMT System','e-CVT','DCT']),
 ('UNKNOWN',None,['AMT System','CVT','e-CVT','DCT']),('OTHER',None,['AMT System','CVT','e-CVT','DCT'])])
def test_overlay_rendering_from_canonical_membership(client,backend,tx,expected,excluded):
    cid=create_car(client)
    assert client.post(f'/edit-car/{cid}',headers=csrf(client),data={'section':'inputs','transmission':tx}).status_code==302
    # The frozen API enables these overlays from explicitly confirmed configuration
    # evidence, not from a display identity alone. Seed that evidence through its API.
    response=requests.post(backend['url']+f'/api/garage/cars/{cid}/service-records',headers=backend_auth(backend),json={
        'service_type':'Other','service_date':'2026-01-01','odometer_km':0,'parts_replaced':[],
        'component_maintenance':{'context':{'configuration':{'transmission':tx}},'context_confirmed':True,'work':[]}})
    assert response.status_code==201
    html=client.get(f'/garage-dashboard?car_id={cid}').get_data(as_text=True)
    if expected:assert f'<h3>{expected}</h3>' in html
    for label in excluded:assert f'<h3>{label}</h3>' not in html

def test_transmission_conflict_fails_closed(client,backend):
    headers=backend_auth(backend)
    base=backend['url']+'/api/garage/cars/207'
    try:
        assert client.post('/edit-car/207',headers=csrf(client),data={'section':'inputs','transmission':'CVT'}).status_code==302
        health=requests.get(base+'/health?read_only=1',headers=headers).json()['health']
        components={r['component'] for r in health['service_checklist']['items']}
        assert 'cvt_transmission' not in components and 'hev_edrive' not in components
        assert '<h3>CVT</h3>' not in client.get('/garage-dashboard?car_id=207').get_data(as_text=True)
    finally:
        assert client.post('/edit-car/207',headers=csrf(client),data={'section':'inputs','transmission':'E_CVT'}).status_code==302
    assert client.get('/garage-dashboard?car_id=207').get_data(as_text=True).count('data-checklist-item')==25

def test_all_active_post_forms_include_csrf(client):
    from html.parser import HTMLParser
    class Forms(HTMLParser):
        def __init__(self):super().__init__();self.forms=[];self.current=None
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='form':self.current=[attrs.get('method','get').lower(),False]
            if tag=='input' and self.current is not None and attrs.get('name')=='csrf_token':self.current[1]=True
        def handle_endtag(self,tag):
            if tag=='form' and self.current is not None:self.forms.append(self.current);self.current=None
    for url in ('/garage','/garage/connect','/edit-car/201','/garage/cars/201/services','/add-car','/login','/register'):
        response=client.get(url)
        assert response.status_code==200
        parser=Forms();parser.feed(response.get_data(as_text=True))
        assert all(token for method,token in parser.forms if method=='post')

def test_equipment_and_turbo_labels_use_canonical_evidence(client,backend):
    cid=create_car(client)
    response=requests.post(backend['url']+f'/api/garage/cars/{cid}/service-records',headers=backend_auth(backend),json={
        'service_type':'Other','service_date':'2026-01-01','odometer_km':0,'parts_replaced':[],
        'component_maintenance':{'context':{'configuration':{'induction':'TURBO','drivetrain':'2WD'},
            'rear_differential_verified':True},'context_confirmed':True,'work':[]}})
    assert response.status_code==201
    html=client.get(f'/garage-dashboard?car_id={cid}').get_data(as_text=True)
    assert '<h3>Turbo / Boost System</h3>' in html and '<h3>Rear Differential</h3>' in html
    assert '<h3>Transfer Case</h3>' not in html

def test_safety_warning_and_no_component_percentages(client):
    cid=create_car(client)
    assert client.post(f'/edit-car/{cid}',headers=csrf(client),data={'section':'inputs','brake_failure':'true'}).status_code==302
    html=client.get(f'/garage-dashboard?car_id={cid}').get_data(as_text=True)
    assert 'role="alert"' in html and 'brake' in html.lower()
    assert 'Parts Watchlist' not in html and 'Brake Health:' not in html

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
    assert client.get('/garage').status_code==401
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
