"""Local-only regression, privacy, completeness and query-shape checks."""
from datetime import datetime, timedelta
import pytest
from sqlalchemy import event
import app as website
from models.models import db, User, WebsiteVisit, AnalyticsEvent, TrafficMetric
from routes.admin_routes import ADMIN_EMAILS, _build_admin_analytics_context
from services import analytics_service
from services.admin_analytics_v2 import build_summary, window, MEANINGFUL_EVENTS


@pytest.fixture
def fixture(monkeypatch):
    monkeypatch.setattr(website, 'safe_track_page_visit', lambda: False)
    monkeypatch.setenv('ANALYTICS_ENABLED', 'false')
    website.rate_limit_hits.clear()
    with website.app.app_context():
        db.drop_all(); db.create_all()
        db.session.add_all([
            User(id=1, username='admin-fixture', email=ADMIN_EMAILS[0], password='synthetic', role='admin'),
            User(id=2, username='regular-fixture', email='private-person@example.invalid', password='synthetic', role='user'),
            User(id=3, username='persona-fixture', email='persona@example.invalid', password='synthetic', role='user', is_managed_persona=True),
            User(id=4, username='quiet-fixture', email='quiet@example.invalid', password='synthetic', role='user'),
        ]); db.session.commit()
        yield
        db.session.rollback(); db.drop_all(); db.create_all()


def record(kind='diagnosis_completed', **kwargs):
    values=dict(created_at=datetime.utcnow()-timedelta(minutes=1), event_type=kind, user_id=2,
                traffic_type='web', is_bot=False, is_internal=False, is_admin=False,
                source='google', ip_address='192.0.2.123', metadata_json='{"private":"DO-NOT-EXPOSE"}')
    values.update(kwargs)
    db.session.add(AnalyticsEvent(**values))


def signed_client(uid):
    from flask import g
    g.pop('_login_user', None)
    client=website.app.test_client()
    with client.session_transaction() as session:
        session['_user_id']=str(uid); session['_fresh']=True
    return client


def test_authorization_and_no_private_values(fixture):
    record();db.session.commit()
    assert website.app.test_client().get('/admin/analytics-v2').status_code==302
    assert signed_client(2).get('/admin/analytics-v2').status_code==403
    client=signed_client(1)
    for section in ['overview','traffic','engagement','acquisition','conversions']:
        response=client.get('/admin/analytics-v2/'+section)
        assert response.status_code==200
        assert response.headers['Cache-Control']=='private, no-store'
        assert 'Cookie' in response.headers.get('Vary','')
        for private in ['private-person@example.invalid','192.0.2.123','DO-NOT-EXPOSE','regular-fixture']:
            assert private.encode() not in response.data
        assert b'<script' not in response.data
    assert client.get('/admin/analytics-v2/overview?range=all').status_code==400
    assert client.get('/admin/analytics-v2/not-a-section').status_code==400


def test_windows_ist_and_explicit_bounds():
    now=datetime(2026,11,13,1,0)
    assert window('today',now)==(datetime(2026,11,12,18,30),now)
    assert window('7d',now)[0]==now-timedelta(days=7)
    assert window('30d',now)[0]==now-timedelta(days=30)
    with pytest.raises(ValueError):window('all',now)


def test_distinct_meaningful_accounts_and_exclusions(fixture):
    for _ in range(4):record()
    record(user_id=1);record(user_id=3);record(user_id=None)
    record('login',user_id=4);record('sign_up',user_id=4)
    record(is_bot=True);record(is_internal=True);record(is_admin=True)
    record(created_at=datetime.utcnow()+timedelta(days=1))
    record(created_at=datetime.utcnow()-timedelta(days=40))
    record(source='email-identifier@example.invalid')
    db.session.commit()
    result=build_summary('7d')
    assert result['registered']==2
    assert result['active']==1
    assert result['counts']['diagnosis_completed']['web']==6
    assert 'login' not in MEANINGFUL_EVENTS and 'sign_up' not in MEANINGFUL_EVENTS
    result=build_summary('7d','acquisition')
    assert any(row['label']=='Other recorded labels' for row in result['sources'])
    assert 'email-identifier' not in str(result)


def test_traffic_and_website_sources_are_never_added(fixture):
    now=datetime(2026,11,13,1,0)
    for hour,count in [(datetime(2026,11,12,18),999),(datetime(2026,11,12,19),7),(datetime(2026,11,13,1),999)]:
        db.session.add(TrafficMetric(hour_start_utc=hour,quality='human_like',count=count))
    db.session.add(TrafficMetric(hour_start_utc=datetime(2026,11,12,19),quality='unknown',count=3))
    db.session.add(WebsiteVisit(visit_time=now-timedelta(minutes=1),is_page_view=True,is_bot=False,is_internal=False,is_admin=False))
    record(created_at=now-timedelta(minutes=1))
    db.session.commit()
    result=build_summary('today',now=now)
    assert result['traffic_total']==10 and result['website_views']==1 and result['event_records']==1
    assert result['traffic_start']==datetime(2026,11,12,19)
    assert len(result['trend'])<=2


def test_legacy_parity_where_definitions_match(fixture):
    for _ in range(4):record('vehicle_added')
    record('page_view',traffic_type='app')
    for i in range(3):
        db.session.add(WebsiteVisit(visit_time=datetime.utcnow()-timedelta(minutes=2),user_id=2,is_page_view=True,is_bot=False,is_internal=False,is_admin=False))
    for quality,count in [('human_like',8),('likely_bot',5),('unknown',2)]:
        db.session.add(TrafficMetric(hour_start_utc=datetime.utcnow().replace(minute=0,second=0,microsecond=0),quality=quality,count=count))
    db.session.commit()
    with website.app.test_request_context('/admin/analytics/overview'):
        analytics_service._live_cache['expires_at']=0
        old=_build_admin_analytics_context('overview')
        new=build_summary('7d')
    assert old['visit_count']==new['website_views']==3
    assert old['traffic_quality']['total']==new['traffic_total']==15
    assert old['live_analytics']['feature_usage_24h']['vehicle_added']==new['counts']['vehicle_added']['web']==4
    assert old['live_analytics']['page_views_24h']==new['counts']['page_view']['app']==1


def test_no_sampling_cap_no_n_plus_one_no_writes(fixture):
    db.session.execute(AnalyticsEvent.__table__.insert(),[dict(created_at=datetime.utcnow()-timedelta(minutes=1),event_type='diagnosis_completed',user_id=2,traffic_type='web',is_bot=False,is_internal=False,is_admin=False) for _ in range(5201)])
    db.session.commit()
    statements=[]
    def collect(conn,cursor,statement,params,ctx,many):statements.append(statement)
    event.listen(db.engine,'before_cursor_execute',collect)
    try:
        first=build_summary('30d')
        assert first['counts']['diagnosis_completed']['web']==5201
        assert len(statements)==6
        assert all(s.lstrip().upper().startswith('SELECT') for s in statements)
    finally:event.remove(db.engine,'before_cursor_execute',collect)
    # Growing the account table cannot add per-account queries.
    db.session.execute(User.__table__.insert(),[dict(id=i,username=f'load-{i}',email=f'load-{i}@example.invalid',password='synthetic',role='user') for i in range(10,110)])
    db.session.commit();statements.clear();event.listen(db.engine,'before_cursor_execute',collect)
    try:build_summary('30d');assert len(statements)==6
    finally:event.remove(db.engine,'before_cursor_execute',collect)


def test_unavailable_is_not_zero(fixture,monkeypatch):
    import services.admin_analytics_v2 as service
    def failed(*args,**kwargs):raise RuntimeError('sensitive-database-error')
    monkeypatch.setattr(service,'build_summary',failed)
    response=signed_client(1).get('/admin/analytics-v2')
    assert b'unavailable, not zero' in response.data
    assert b'sensitive-database-error' not in response.data
    assert b'class="metrics"' not in response.data


def test_null_flags_follow_source_definitions(fixture):
    db.session.execute(db.text("INSERT INTO analytics_event (created_at,event_type,status,is_bot,is_internal,is_admin) VALUES (:time,'vehicle_added','stored',NULL,NULL,NULL)"),{'time':datetime.utcnow()-timedelta(minutes=1)})
    db.session.execute(db.text("INSERT INTO website_visit (visit_time,is_page_view,is_bot,is_internal,is_admin) VALUES (:time,1,NULL,NULL,NULL)"),{'time':datetime.utcnow()-timedelta(minutes=1)})
    db.session.commit()
    summary=build_summary()
    assert summary['website_views']==1 and summary['event_records']==0
