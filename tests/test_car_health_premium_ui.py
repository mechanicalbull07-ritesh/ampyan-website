"""Presentation and read-only integration; all accounts and API data are synthetic."""
from pathlib import Path
from urllib.parse import urlsplit
from flask import render_template
import app as website
from .test_canonical_garage import backend,client,snapshot
from .test_account_deletion_discovery import Document

PLAY='https://play.google.com/store/apps/details?id=com.ampyan.app'

def test_health_dashboard_readonly_refresh_switch_and_brand(client,backend):
    before=snapshot(backend)
    for cid in (201,201,202):
        r=client.get('/my-car-health?car_id='+str(cid));assert r.status_code==200
        doc=Document(r.data)
        assert doc.select_one('.ch-hero')
        assert [n.get_text(strip=True) for n in doc.nodes if n.tag=='h1']==['My Car Health']
        assert doc.select_one('.ch-vehicle') and doc.select_one('.ch-help a[href="/help"]')
        for section in ('forecast','mileage','checklist','safety'):
            assert doc.select_one('[data-section="'+section+'"]')
        main=doc.select_one('main');links=doc.select('main a')
        primary=[a for a in links if a.get_text(strip=True)=='Open in AMPYAN App']
        assert len(primary)==1 and primary[0]['href']==PLAY
        assert len(doc.select('.ch-toon'))==1
        assert 'App Store — Coming Soon' in main.get_text()
        for a in links:
            if 'App Store' in a.get_text():raise AssertionError('Fake Apple link')
            assert all(secret not in a['href'] for secret in ('token=','password=','user_id=','owner_id='))
        assert not doc.select('main input') and not doc.select('main textarea')
        assert all(f.attrs.get('method','get')=='get' for f in doc.select('main form'))
        assert all(s.attrs.get('name')=='car_id' for s in doc.select('main select'))
        assert doc.select_one('a[href="/garage/cars/'+str(cid)+'/services"]')
        for im in doc.select('main img'):
            assert im.attrs.get('alt') and im.attrs.get('width') and im.attrs.get('height')
        assert 'complete setup' not in main.get_text().lower() or doc.select('main a[data-app-cta="setup"]')
    assert snapshot(backend)==before
    assert client.get('/my-car-health?car_id=301').status_code==404
    assert snapshot(backend)==before


def render_health(**changes):
    context=dict(view='health',cars=[dict(id=201,brand='Example',model='Vehicle')],car=dict(id=201,brand='Example',model='Vehicle',current_odometer_km=None),health={'service_due':{}},mileage={},rows=[],configuration={'setup_incomplete':True},mileage_error=None)
    context.update(changes)
    with website.app.test_request_context('/my-car-health'):
        return render_template('canonical_garage.html',**context)


def test_missing_states_no_fabricated_estimates_and_unknown_remains_unknown():
    html=render_health(rows=[dict(title='Workshop check',action='INSPECT',timing='At next service',guidance='Confirm in App.',status='UNKNOWN')])
    assert 'Service history needed' in html and 'More driving information needed' in html
    assert 'Complete your vehicle setup in the AMPYAN App to unlock applicable service checks.' in html
    assert '>UNKNOWN</span>' in html and 'Not yet confirmed' in html and 'Not yet available' in html
    assert '10,000 km' not in html


def test_available_forecast_mileage_and_api_error_semantics():
    html=render_health(health={'service_due':{'next_service_km':42000,'next_service_date':'2027-01-01','primary_due_label':'Overdue'},'last_qualifying_main_service_km':32000,'last_qualifying_main_service_date':'2026-01-01'},mileage={'last_confirmed_odometer':33000,'estimated_odometer':35000,'odometer_confidence':'HIGH','estimated_service_due_date':'2027-01-01'},configuration={'setup_incomplete':False})
    for value in ('42,000 km','32,000 km','33,000 km','35,000 km','High','Overdue','2027-01-01'):assert value in html
    assert 'Service history needed' not in html and 'More driving information needed' not in html
    error=render_health(mileage_error='Mileage is temporarily unavailable.')
    assert 'role="alert">Mileage is temporarily unavailable.' in error
    assert 'Estimated odometer' not in error


def test_ui_assets_and_no_new_scripts_or_external_brand_requests():
    root=Path(__file__).resolve().parents[1]
    partial=(root/'templates/components/car_health_dashboard.html').read_text()
    assert '<script' not in partial and '<input' not in partial
    assert 'loading="lazy"' in partial and 'width="480"' in partial
    for name in ('ampyan-wordmark.webp','ampyan-toon-phone.webp'):
        assert (root/'static/images/car-health'/name).stat().st_size<100000
    css=(root/'static/css/car_health_dashboard.css').read_text()
    assert ':focus-visible' in css and 'prefers-reduced-motion' in css and 'body.light' in css
