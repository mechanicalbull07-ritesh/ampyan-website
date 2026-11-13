"""Opt-in, disposable Unix-socket PostgreSQL coverage of the shared ID types.

The runner supplies a newly initialized local cluster. Never accepts a production
URL, reads production data, or changes the application's model/schema contract.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from flask import g
from sqlalchemy import MetaData, String, create_engine, event, text
from sqlalchemy.engine import URL

import app as website
from models.models import db, User, AnalyticsEvent, WebsiteVisit, TrafficMetric
from routes.admin_routes import ADMIN_EMAILS
from services.admin_analytics_v2 import build_summary, window

NOW = datetime(2026, 11, 13, 1, 0)


@pytest.fixture
def pg_room():
    path = os.environ.get('AMPYAN_V2_DISPOSABLE_PG_META')
    if not path:
        pytest.skip('Requires owned disposable PostgreSQL metadata')
    meta_path = Path(path).resolve()
    assert str(meta_path).startswith('/private/tmp/ampyan-v2-sql-pg-')
    meta = json.loads(meta_path.read_text())
    root = meta_path.parent
    socket = Path(meta['socket']).resolve()
    assert socket.is_relative_to(root) and socket.is_dir()
    assert meta['database'] == 'ampyan_v2_sql_fixture'
    assert meta['user'] == 'ampyan_v2_fixture'
    engine = create_engine(URL.create('postgresql+psycopg2', username=meta['user'],
        database=meta['database'], query={'host': str(socket), 'port': str(meta['port'])}))
    with engine.connect() as conn:
        identity = conn.execute(text("SELECT current_database(),current_user,current_setting('data_directory'),current_setting('listen_addresses'),inet_server_addr()" )).one()
        assert identity[0:2] == (meta['database'], meta['user'])
        assert Path(identity[2]).resolve() == root / 'data'
        assert identity[3] == '' and identity[4] is None

    # Clone only fixture metadata. The deployed ORM and production schema stay untouched.
    fixture_schema = MetaData()
    for table in (User.__table__, AnalyticsEvent.__table__, WebsiteVisit.__table__, TrafficMetric.__table__):
        table.to_metadata(fixture_schema)
    events = fixture_schema.tables['analytics_event']
    for constraint in list(events.foreign_key_constraints):
        if any(fk.parent.name == 'user_id' for fk in constraint.elements):
            events.constraints.remove(constraint)
            for fk in constraint.elements:
                events.foreign_keys.discard(fk)
                events.c.user_id.foreign_keys.discard(fk)
    events.c.user_id.type = String()
    fixture_schema.create_all(engine)
    with engine.connect() as conn:
        types = dict(conn.execute(text("SELECT table_name||'.'||column_name,data_type FROM information_schema.columns WHERE table_schema='public' AND ((table_name='user' AND column_name='id') OR (table_name IN ('analytics_event','website_visit') AND column_name='user_id'))")).all())
        assert types == {'user.id': 'integer', 'analytics_event.user_id': 'character varying', 'website_visit.user_id': 'integer'}
    with website.app.app_context():
        db.session.remove()
        previous = db.engines[None]
        db.engines[None] = engine
        try:
            for uid, role, managed in [(1, 'admin', False), (2, 'user', False),
                    (3, 'user', True), (4, 'user', False), (5, 'user', False), (6, 'admin', False)]:
                db.session.add(User(id=uid, username=f'fixture-{uid}',
                    email=ADMIN_EMAILS[0] if uid == 1 else f'fixture-{uid}@example.invalid',
                    password='synthetic', role=role, is_managed_persona=managed,
                    email_verified=True, is_banned=False))
            db.session.commit()
            yield engine
        finally:
            db.session.remove()
            db.engines[None] = previous
            fixture_schema.drop_all(engine)
            engine.dispose()


def action(uid='2', kind='diagnosis_completed', at=None, channel='web', **flags):
    values = dict(uid=uid, kind=kind, at=at or NOW-timedelta(minutes=1), channel=channel,
                  bot=False, internal=False, admin=False)
    values.update(flags)
    db.session.execute(text("INSERT INTO analytics_event (created_at,event_type,status,user_id,traffic_type,is_bot,is_internal,is_admin,source) VALUES (:at,:kind,'stored',:uid,:channel,:bot,:internal,:admin,'google')"), values)


def visit(uid=None, **flags):
    values = dict(uid=uid, at=NOW-timedelta(minutes=1), bot=False, internal=False, admin=False)
    values.update(flags)
    db.session.execute(text("INSERT INTO website_visit (visit_time,user_id,is_page_view,is_bot,is_internal,is_admin) VALUES (:at,:uid,true,:bot,:internal,:admin)"), values)


def test_pg_active_accounts_and_event_rows_do_not_multiply(pg_room):
    for _ in range(3):
        action('2')
    action('4', 'vehicle_added', channel='app')
    action('5', 'login')
    action('5', 'sign_up')
    for uid in (None, '', 'opaque-id', '999999', '005'):
        action(uid)
    for uid in ('1', '3', '6'):
        action(uid)  # Admin, persona and separate administrator must stay excluded.
    for flags in ({'bot': True}, {'internal': True}, {'admin': True}, {'bot': None}):
        action('2', **flags)
    db.session.commit()
    result = build_summary('7d', now=NOW)
    assert result['registered'] == 3
    assert result['active'] == 2  # Repeated actions are not repeated accounts.
    assert result['counts']['diagnosis_completed']['web'] == 8
    assert result['counts']['vehicle_added']['app'] == 1
    assert result['event_records'] == 11  # Every eligible action row counts exactly once.


@pytest.mark.parametrize('period,records,active,web,app,vehicles', [
    ('today', 1, 1, 1, 0, 0), ('7d', 3, 2, 2, 1, 0), ('30d', 5, 2, 3, 1, 1),
])
def test_pg_period_boundaries_and_channels(pg_room, period, records, active, web, app, vehicles):
    today_start = datetime(2026, 11, 12, 18, 30)
    action('2')
    action('4', at=today_start-timedelta(seconds=1), channel='app')
    action('4', 'vehicle_added', at=NOW-timedelta(days=8))
    action('5', at=NOW-timedelta(days=31))
    action('5', at=NOW)
    action('5', at=NOW+timedelta(days=1))
    action('2', at=NOW-timedelta(days=7))
    action('4', at=NOW-timedelta(days=30))
    db.session.commit()
    for section in ('overview', 'traffic', 'engagement', 'acquisition', 'conversions'):
        result = build_summary(period, section, now=NOW)
        assert result['active'] == active
        assert result['event_records'] == records
        assert result['counts']['diagnosis_completed']['web'] == web
        assert result['counts']['diagnosis_completed']['app'] == app
        assert result['counts'].get('vehicle_added', {}).get('web', 0) == vehicles
    assert window('today', NOW)[0] == today_start


def test_pg_integer_visits_and_separate_sources_are_preserved(pg_room):
    for uid in (2, 4, None):
        visit(uid)
    for uid in (1, 3, 6):
        visit(uid)
    visit(2, bot=True)
    action(None)
    for quality, count in [('human_like', 7), ('likely_bot', 2), ('unknown', 3)]:
        db.session.add(TrafficMetric(hour_start_utc=datetime(2026, 11, 12, 19), quality=quality, count=count))
    db.session.commit()
    statements = []
    def collect(conn, cursor, sql, params, context, many):
        statements.append(sql)
    event.listen(pg_room, 'before_cursor_execute', collect)
    try:
        result = build_summary('today', now=NOW)
    finally:
        event.remove(pg_room, 'before_cursor_execute', collect)
    assert result['website_views'] == 3
    assert result['traffic_total'] == 12
    assert result['event_records'] == 1 and result['active'] == 0
    assert len(statements) == 6 and all(s.lstrip().upper().startswith('SELECT') for s in statements)


def test_pg_whitelisted_account_is_excluded_even_without_admin_role(pg_room):
    db.session.get(User, 1).role = 'user'
    action('1')
    action('3')
    db.session.commit()
    result = build_summary('30d', now=NOW)
    assert result['registered'] == 3 and result['active'] == 0
    assert result['event_records'] == 0


def test_pg_routes_and_consent_remain_readonly(pg_room):
    from services import analytics_service
    g.pop('_login_user', None)
    assert website.app.test_client().get('/admin/analytics-v2').status_code == 302
    regular = website.app.test_client()
    with regular.session_transaction() as saved:
        saved['_user_id'] = '2'
        saved['_fresh'] = True
    g.pop('_login_user', None)
    assert regular.get('/admin/analytics-v2').status_code == 403
    client = website.app.test_client()
    with client.session_transaction() as saved:
        saved['_user_id'] = '1'
        saved['_fresh'] = True
    statements = []
    def collect(conn, cursor, sql, params, context, many):
        statements.append(sql)
    event.listen(pg_room, 'before_cursor_execute', collect)
    try:
        for section in ('overview', 'traffic', 'engagement', 'acquisition', 'conversions'):
            g.pop('_login_user', None)
            response = client.get('/admin/analytics-v2/'+section+'?range=7d')
            assert response.status_code == 200
            assert response.headers['Cache-Control'] == 'private, no-store'
            assert b'We couldn\xe2\x80\x99t load this view' not in response.data
        with website.app.test_request_context('/admin/analytics-v2/overview'):
            assert not analytics_service.analytics_consent_granted()
            assert not analytics_service.safe_track_page_visit()
        assert all(s.lstrip().upper().startswith('SELECT') for s in statements)
    finally:
        event.remove(pg_room, 'before_cursor_execute', collect)
    assert db.session.query(AnalyticsEvent).count() == 0
