"""Website -> real disposable Backend, including CSRF and zero-history setup."""
import requests
import pytest
from flask.testing import FlaskClient
from .test_canonical_garage import backend, client, csrf, backend_auth, connection
import app as website


def synthetic_car(backend, fuel='CNG'):
    r=requests.post(backend['url']+'/api/garage/cars', headers=backend_auth(backend),json={
        'brand':'Synthetic','model':'Zero-service XL6 equivalent','fuel_type':fuel,
        'transmission':'MANUAL' if fuel=='CNG' else 'UNKNOWN','registration_year':2020,'current_odometer_km':10000})
    assert r.status_code==201,r.json()
    return r.json()['car']['id']


def configuration(backend,cid):
    r=requests.get(backend['url']+f'/api/garage/cars/{cid}/configuration',headers=backend_auth(backend))
    assert r.status_code==200
    return r.json()['configuration']


def test_zero_service_cng_web_save_refresh_and_restart(client, backend):
    cid=synthetic_car(backend)
    url=f'/edit-car/{cid}'
    page=client.get(url);assert page.status_code==200
    text=page.get_data(as_text=True)
    assert 'Vehicle Configuration' in text and 'CNG installation use engine-coolant hoses' in text
    assert 'Diesel particulate filter fitted' not in text and 'Electric drive thermal' not in text
    assert configuration(backend,cid)['revision']==0
    result=client.post(url,data={'section':'configuration','setup_revision':'0',
        'setup.cng_kit_verified':'true','setup.bifuel_verified':'true','setup.cng_coolant_hoses_present':'true'},headers=csrf(client))
    assert result.status_code==302
    page=client.get(result.location);assert page.status_code==200
    text=page.get_data(as_text=True)
    assert text.count('data-checklist-item')==22
    assert 'Confirm your last main-service KM/date' in text and 'Confirmation needed' in text
    with connection(backend) as conn:
        for table in ('service_record','odometer_confirmation','running_profile_history','mileage_prompt_state'):
            assert conn.execute(f'SELECT COUNT(*) FROM {table} WHERE car_id=?',(cid,)).fetchone()[0]==0
    backend['restart']();website.app.config['AMPYAN_API_BASE_URL']=backend['url']
    assert client.get(f'/my-car-health?car_id={cid}').get_data(as_text=True).count('data-checklist-item')==22


def test_unknown_noop_cancel_and_stale_retains_selection(client,backend):
    cid=synthetic_car(backend)
    url=f'/edit-car/{cid}'
    client.get(url);client.get(f'/my-car-health?car_id={cid}')
    assert configuration(backend,cid)['revision']==0
    r=client.post(url,data={'section':'configuration','setup_revision':'0','setup.cng_kit_verified':'unknown'},headers=csrf(client))
    assert r.status_code==302 and configuration(backend,cid)['revision']==0
    h=backend_auth(backend)
    r=requests.patch(backend['url']+f'/api/garage/cars/{cid}/configuration',headers=h,
        json={'revision':0,'changes':{'cng_kit_verified':True}});assert r.status_code==200
    r=client.post(url,data={'section':'configuration','setup_revision':'0','setup.bifuel_verified':'true'},headers=csrf(client))
    assert r.status_code==409
    assert 'Your selections are retained' in r.get_data(as_text=True)
    assert '<option value="true" selected>Yes</option>' in r.get_data(as_text=True)
    r=client.post(url,data={'section':'configuration','setup_revision':'1','setup.cng_kit_verified':'unknown'},headers=csrf(client))
    assert r.status_code==302
    assert configuration(backend,cid)['context']['cng_kit_verified'] is None


def test_csrf_ownership_and_unsupported_fields(client,backend):
    cid=synthetic_car(backend)
    raw=FlaskClient(website.app,website.app.response_class)
    with client.session_transaction() as saved,raw.session_transaction() as target:target.update(saved)
    payload={'section':'configuration','setup_revision':'0','setup.cng_kit_verified':'true'}
    assert raw.post(f'/edit-car/{cid}',data=payload).status_code==400
    assert configuration(backend,cid)['revision']==0
    assert client.post('/edit-car/301',data=payload,headers=csrf(client)).status_code==404
    assert client.post(f'/edit-car/{cid}',data={**payload,'setup.unsupported':'true'},headers=csrf(client)).status_code==400
    with raw.session_transaction() as saved:saved.clear()
    assert raw.get(f'/edit-car/{cid}').status_code==302


@pytest.mark.parametrize('fuel,wanted,unwanted',[
 ('Petrol','Engine air supply','CNG system confirmed'),
 ('Diesel','Diesel particulate filter fitted','CNG system confirmed'),
 ('EV','Electric drive thermal / cooling system fitted','Engine air supply')])
def test_powertrain_aware_questions(client,backend,fuel,wanted,unwanted):
    cid=synthetic_car(backend,fuel)
    page=client.get(f'/edit-car/{cid}').get_data(as_text=True)
    assert wanted in page and unwanted not in page


@pytest.mark.parametrize('architecture,key,wanted,unwanted',[
 ('MILD_HYBRID','mild_isg_verified','Integrated starter generator fitted','Hybrid inverter cooling fitted'),
 ('HEV','hev_inverter_cooling_verified','Hybrid inverter cooling fitted','Integrated starter generator fitted')])
def test_hybrid_questions_require_explicit_architecture(client,backend,architecture,key,wanted,unwanted):
    cid=synthetic_car(backend,'Petrol')
    url=f'/edit-car/{cid}'
    initial=client.get(url).get_data(as_text=True)
    assert wanted not in initial and unwanted not in initial
    saved=client.post(url,data={'section':'configuration','setup_revision':'0',
        'setup.electrification_architecture':architecture},headers=csrf(client))
    assert saved.status_code==302
    page=client.get(url).get_data(as_text=True)
    assert wanted in page and unwanted not in page
    saved=client.post(url,data={'section':'configuration','setup_revision':'1','setup.'+key:'true'},headers=csrf(client))
    assert saved.status_code==302
    assert configuration(backend,cid)['context'][key] is True
    with connection(backend) as conn:
        assert conn.execute('SELECT COUNT(*) FROM service_record WHERE car_id=?',(cid,)).fetchone()[0]==0
