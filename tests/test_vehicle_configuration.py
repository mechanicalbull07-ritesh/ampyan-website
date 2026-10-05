"""App-owned inputs and read-only Website reflection on a real disposable API."""
from datetime import datetime, timezone
from pathlib import Path
import requests
import pytest
from flask.testing import FlaskClient
from .test_canonical_garage import backend, client, csrf, backend_auth, connection, snapshot
import app as website
from services import canonical_garage_client as api


def synthetic_car(backend, fuel='CNG'):
    r=requests.post(backend['url']+'/api/garage/cars',headers=backend_auth(backend),json={
        'brand':'Maruti','model':'XL6','fuel_type':fuel,'transmission':'MANUAL' if fuel=='CNG' else 'UNKNOWN',
        'registration_year':2020,'current_odometer_km':10000})
    assert r.status_code==201,r.text
    return r.json()['car']['id']


def configuration(backend,cid):
    r=requests.get(backend['url']+f'/api/garage/cars/{cid}/configuration',headers=backend_auth(backend))
    assert r.status_code==200
    return r.json()['configuration']


def app_patch(backend,cid,changes):
    config=configuration(backend,cid)
    r=requests.patch(backend['url']+f'/api/garage/cars/{cid}/configuration',headers=backend_auth(backend),
        json={'revision':config['revision'],'changes':changes})
    assert r.status_code==200,r.text
    return r.json()['configuration']


def view_without_writes(client,backend,cid):
    before=snapshot(backend)
    r=client.get(f'/my-car-health?car_id={cid}')
    assert r.status_code==200
    assert snapshot(backend)==before
    text=r.get_data(as_text=True)
    for forbidden in ('name="section"','name="actual_km"','name="setup.','>Edit</a>','UNKNOWN','MASTER_V1'):
        assert forbidden not in text
    return text


def test_xl6_app_configuration_service_mi_and_restart(client,backend):
    cid=synthetic_car(backend)
    initial=view_without_writes(client,backend,cid)
    assert 'Maruti XL6' in initial and 'CNG • Manual' in initial
    for label in ('Service history needed','More driving information needed','Vehicle setup incomplete'):
        assert label in initial
    assert initial.count('data-checklist-item')==0
    app_patch(backend,cid,dict(cng_kit_verified=True,bifuel_verified=True,cng_coolant_hoses_present=True))
    configured=view_without_writes(client,backend,cid)
    assert configured.count('data-checklist-item')==22
    assert 'Service history needed' in configured and 'More driving information needed' in configured
    with connection(backend) as conn:
        for table in ('service_record','odometer_confirmation','running_profile_history','mileage_prompt_state'):
            assert conn.execute(f'SELECT COUNT(*) FROM {table} WHERE car_id=?',(cid,)).fetchone()[0]==0
    now=datetime.now(timezone.utc)
    h=backend_auth(backend);base=backend['url']+f'/api/garage/cars/{cid}'
    r=requests.post(base+'/service-records',headers=h,json=dict(service_type='Periodic service',
        qualifying_main_service=True,service_date=now.date().isoformat(),odometer_km=10000,parts_replaced=[]))
    assert r.status_code==201,r.text
    serviced=view_without_writes(client,backend,cid)
    assert 'Service history needed' not in serviced and 'More driving information needed' in serviced
    r=requests.post(base+'/mileage/confirmations',headers=h,json=dict(source='MANUAL',actual_km=10000,
        user_confirmed=True,observed_at=now.isoformat(),timezone='UTC',idempotency_key='p10-'+str(cid)))
    assert r.status_code==200,r.text
    r=requests.post(base+'/mileage/profiles',headers=h,json=dict(effective_date=now.date().isoformat(),
        timezone='UTC',weekday_km=20,weekend_km=10,provenance='USER_PROVIDED',idempotency_key='p10-running-'+str(cid)))
    assert r.status_code==200,r.text
    complete=view_without_writes(client,backend,cid)
    assert complete.count('data-checklist-item')==22
    assert 'More driving information needed' not in complete
    # Real App/API state is durable; Website refresh performs only GETs.
    backend['restart']();website.app.config['AMPYAN_API_BASE_URL']=backend['url']
    assert view_without_writes(client,backend,cid).count('data-checklist-item')==22
    assert configuration(backend,cid)['context']['cng_kit_verified'] is True


@pytest.mark.parametrize('route,method',[
 ('/add-car','POST'),('/edit-car/201','POST'),('/delete-car/201','POST'),
 ('/api/cars','POST'),('/api/cars/201','PUT'),('/api/cars/201','PATCH'),('/api/cars/201','DELETE'),
 ('/garage/cars/201/services','POST'),('/api/cars/201/configuration','PATCH'),
 ('/garage/cars/201/mileage/confirmations','POST'),('/garage/cars/201/mileage/profiles','POST')])
def test_retired_web_mutations_cannot_reach_backend(client,backend,monkeypatch,route,method):
    before=snapshot(backend)
    def forbidden(*a,**k):pytest.fail('A retired Website mutation reached the Backend')
    monkeypatch.setattr(api.requests,'request',forbidden)
    response=client.open(route,method=method,json={'revision':0,'changes':{'cng_kit_verified':True},
        'qualifying_main_service':True,'actual_km':1,'transmission':'MANUAL'},headers=csrf(client))
    assert response.status_code in (404,405)
    assert snapshot(backend)==before


@pytest.mark.parametrize('endpoint,method',[
 ('/api/garage/cars','POST'),('/api/garage/cars/201','PUT'),('/api/garage/cars/201','DELETE'),
 ('/api/garage/cars/201/configuration','PATCH'),('/api/garage/cars/201/service-records','POST'),
 ('/api/garage/cars/201/mileage/profiles','POST'),('/api/garage/cars/201/mileage/confirmations','POST'),
 ('/api/garage/cars/201/health','GET'),('/api/garage/cars/201/service-plan','GET')])
def test_client_boundary_rejects_writes_and_unsafe_reads(monkeypatch,endpoint,method):
    def forbidden(*a,**k):pytest.fail('Forbidden network request')
    monkeypatch.setattr(api.requests,'request',forbidden)
    with website.app.test_request_context(),pytest.raises(api.GarageError) as exc:
        api.call(endpoint,method,{'synthetic':True})
    assert exc.value.status==405


@pytest.mark.parametrize('route',['/my-car-health?car_id=301','/edit-car/301','/garage/cars/301/services','/api/cars/301'])
def test_read_ownership_is_preserved(client,backend,route):
    before=snapshot(backend)
    assert client.get(route,headers={'X-AMPYAN-USER-ID':'9901'}).status_code==404
    assert snapshot(backend)==before


def test_unknown_preserved_by_app_and_web_is_readonly(client,backend):
    cid=synthetic_car(backend)
    saved=app_patch(backend,cid,{'cng_kit_verified':None})
    assert saved['context']['cng_kit_verified'] is None
    assert view_without_writes(client,backend,cid).count('data-checklist-item')==0
    before=snapshot(backend)
    assert client.get(f'/edit-car/{cid}').status_code==302
    assert snapshot(backend)==before


@pytest.mark.parametrize('route',['/garage','/my-car-health','/garage-dashboard','/add-car'])
def test_no_garage_onboarding_without_backend_access(client,monkeypatch,route):
    with client.session_transaction() as saved:saved.pop('garage_credentials',None)
    monkeypatch.setattr(api.requests,'request',lambda *a,**k:pytest.fail('No Garage state must not call Backend'))
    r=client.get(route)
    assert r.status_code==200
    assert b'Your Car Health starts in the AMPYAN App' in r.data
    assert r.get_data(as_text=True).count('data-preview-card')==4
    assert b'https://play.google.com/store/apps/details?id=com.ampyan.app' in r.data


def test_refresh_switch_logout_login_and_service_reads_no_write(client,backend):
    before=snapshot(backend)
    for _ in range(2):
        for route in ('/garage','/my-car-health?car_id=201','/my-car-health?car_id=203',
                      '/garage/cars/203/services','/api/cars','/api/cars/201'):
            assert client.get(route).status_code==200
    assert client.post('/set-default-car/207',headers=csrf(client)).status_code==302
    assert client.get('/my-car-health').status_code==200
    assert client.post('/logout',headers=csrf(client)).status_code==302
    assert client.post('/login',data={'username':'web41','password':'local-test-only-123'},headers=csrf(client)).status_code==302
    assert client.get('/my-car-health?car_id=203').status_code==200
    assert snapshot(backend)==before


def test_app_cta_matches_existing_homepage_and_all_variants(client):
    from flask import render_template
    url='https://play.google.com/store/apps/details?id=com.ampyan.app'
    assert url in (Path(website.app.root_path)/'templates/home.html').read_text()
    with website.app.test_request_context():
        text=render_template('canonical_garage.html',view='health',cars=[{'id':1}],
            car={'id':1,'brand':'Synthetic','model':'Preview','transmission':'UNKNOWN'},
            health={},mileage={},configuration={},rows=[])
    for variant in ('open','setup','service','running'):
        assert f'data-app-cta="{variant}"' in text
    assert 'UNKNOWN' not in text
    assert 'href="/edit-car/' not in text and 'href="/add-car"' not in text


def test_mileage_outage_preserves_available_health(client,backend,monkeypatch):
    original=api.requests.request
    def flaky(method,url,**kwargs):
        if url.endswith('/mileage'):raise requests.ConnectionError('Synthetic mileage outage')
        return original(method,url,**kwargs)
    before=snapshot(backend)
    monkeypatch.setattr(api.requests,'request',flaky)
    r=client.get('/my-car-health?car_id=203')
    assert r.status_code==200
    assert r.get_data(as_text=True).count('data-checklist-item')==22
    assert b'Garage is temporarily unavailable' in r.data
    assert b'More driving information needed' not in r.data
    assert snapshot(backend)==before


@pytest.mark.parametrize('stage',['cars','health'])
def test_malformed_api_payload_fails_without_estimate(client,monkeypatch,stage):
    original=api.requests.request
    class Invalid:
        status_code=200
        def json(self):return {'success':True,'cars':{} } if stage=='cars' else {'success':True,'car':{'id':201},'health':[]}
    def bad(method,url,**kwargs):
        if (stage=='cars' and url.endswith('/cars')) or (stage=='health' and '/health?' in url):return Invalid()
        return original(method,url,**kwargs)
    monkeypatch.setattr(api.requests,'request',bad)
    r=client.get('/my-car-health?car_id=201')
    assert r.status_code==503 and b'data-checklist-item' not in r.data


def test_no_vehicle_connected_garage_onboarding(client,monkeypatch):
    from routes import canonical_garage_routes as routes
    monkeypatch.setattr(routes,'call',lambda *a,**k:{'success':True,'cars':[]})
    for path in ('/garage','/my-car-health'):
        r=client.get(path)
        assert r.status_code==200 and b'Your Car Health starts in the AMPYAN App' in r.data


def test_csrf_remains_required_for_auth_and_session_selection(client,backend):
    # These are legitimate Website-session mutations, not vehicle-data writes.
    before=snapshot(backend)
    for target in ('/set-default-car/201','/api/cars/201/default','/garage/connect','/logout'):
        assert client.post(target).status_code==400
        assert client.post(target,headers={'X-CSRFToken':'forged'}).status_code==400
    assert snapshot(backend)==before
