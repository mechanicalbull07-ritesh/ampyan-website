"""Owned disposable PostgreSQL only: contention, deletion protocol, metric parity."""
import ast
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
import time

import pytest
from flask import abort, g
from flask_login import current_user, login_required
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import TimeoutError
from sqlalchemy.orm import Session as PlainSession

import app as website
from models.models import db, User, Car, WebsiteVisit, WebsiteEvent
import routes.admin_routes as admin
from services import analytics_service as analytics

EVIDENCE = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / 'fixtures/backend_stability'
MEASUREMENTS = {}
WRITE_ACTION = lambda: 'ok'

@login_required
def write_view():
    return WRITE_ACTION()
website.app.add_url_rule('/__stability/write', 'stability_write', write_view, methods=['POST'])
website.app.add_url_rule('/api/__stability/write', 'stability_api_write', write_view, methods=['POST'])

def original(path, name, globals_):
    tree = ast.parse((BASELINE / path).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []
    namespace = dict(globals_)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<verified-baseline>', 'exec'), namespace)
    return namespace[name]

@pytest.fixture
def pg(monkeypatch):
    path = Path(os.environ.get('AMPYAN_V2_DISPOSABLE_PG_META', '/missing')).resolve()
    if not path.exists(): pytest.skip('Requires owned disposable PostgreSQL metadata')
    assert str(path).startswith('/private/tmp/ampyan-v2-sql-pg-')
    meta = json.loads(path.read_text()); sock = Path(meta['socket']).resolve()
    assert sock.is_relative_to(path.parent) and sock.is_dir()
    assert meta['database'] == 'ampyan_v2_sql_fixture' and meta['user'] == 'ampyan_v2_fixture'
    engine = create_engine(URL.create('postgresql+psycopg2', username=meta['user'], database=meta['database'],
        query={'host':str(sock), 'port':str(meta['port'])}), pool_size=2, max_overflow=0, pool_timeout=2, pool_pre_ping=True)
    with engine.connect() as conn:
        identity = conn.execute(text("SELECT current_database(),current_user,current_setting('data_directory'),current_setting('listen_addresses'),inet_server_addr()" )).one()
        assert identity[:2] == (meta['database'], meta['user'])
        assert Path(identity[2]).resolve() == path.parent/'data' and identity[3] == '' and identity[4] is None
    with website.app.app_context():
        db.session.remove(); previous = db.engines[None]; db.engines[None] = engine; db.create_all()
        db.session.add_all([User(id=i, username=f'fixture-{i}', email=admin.ADMIN_EMAILS[0] if i == 1 else f'fixture-{i}@example.invalid',
            password='synthetic', role='admin' if i == 1 else 'user', email_verified=True,
            is_banned=False, ai_last_reset=datetime.utcnow()) for i in range(1,5)])
        db.session.commit()
    monkeypatch.setenv('ACCOUNT_DELETION_ENABLED','true'); monkeypatch.setenv('ANALYTICS_ENABLED','false')
    try: yield engine
    finally:
        with website.app.app_context():
            db.session.remove(); db.drop_all(); db.engines[None] = previous
        assert engine.pool.checkedout() == 0
        engine.dispose()

def client_for(uid=2):
    client = website.app.test_client()
    with client.session_transaction() as saved:
        saved['_user_id'] = str(uid); saved['_fresh'] = True
    return client

def no_locks(engine):
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND classid=16603")).scalar() == 0

def action(monkeypatch, fn):
    monkeypatch.setattr(__import__(__name__, fromlist=['WRITE_ACTION']), 'WRITE_ACTION', fn)

def test_baseline_second_checkout_timeout(pg):
    fence = original('app.py','account_deletion_write_fence',vars(website))
    with pg.connect() as occupied, website.app.test_request_context('/__stability/write',method='POST'):
        with PlainSession(pg) as session:
            g._login_user = session.get(User,2)
            start = time.perf_counter()
            with pytest.raises(TimeoutError): fence()
            elapsed = time.perf_counter()-start
            assert 1.9 <= elapsed < 3
            MEASUREMENTS['baseline_checkout_timeout_seconds'] = elapsed

@pytest.mark.parametrize('tracking',[False,True])
def test_authenticated_post_with_one_available_slot(pg,monkeypatch,tracking):
    monkeypatch.setenv('ANALYTICS_ENABLED','true' if tracking else 'false')
    queued=[]; monkeypatch.setattr(analytics,'_enqueue',lambda item: queued.append(item) or True)
    client=client_for();client.set_cookie('ampyan_analytics_consent','granted')
    def write():
        db.session.execute(text('UPDATE "user" SET mobile=\'local-write\' WHERE id=2'));db.session.commit()
        assert db.session.execute(text('SELECT mobile FROM "user" WHERE id=2')).scalar()=='local-write'
        return 'ok'
    action(monkeypatch,write)
    with pg.connect() as occupied:
        checkout_times = []
        pool_connect = pg.pool.connect
        def measured_checkout():
            began = time.perf_counter()
            try:
                return pool_connect()
            finally:
                checkout_times.append(time.perf_counter() - began)
        monkeypatch.setattr(pg.pool, 'connect', measured_checkout)
        start=time.perf_counter()
        response=client.post('/api/track-event',json={'event_type':'page_view'}) if tracking else client.post('/__stability/write')
        assert response.status_code==(202 if tracking else 200)
        if tracking: assert queued
        elapsed=time.perf_counter()-start;assert elapsed<1.5
        MEASUREMENTS['track_event_seconds' if tracking else 'authenticated_post_seconds']=elapsed
        assert len(checkout_times) == 1
        MEASUREMENTS['track_event_pool' if tracking else 'authenticated_post_pool'] = {
            'checkouts': len(checkout_times), 'max_checkout_seconds': max(checkout_times)}
    no_locks(pg)

def test_two_simultaneous_writers_fit_pool_two(pg,monkeypatch):
    barrier=threading.Barrier(2);pids=[]
    def write():
        pid=db.session.execute(text('SELECT pg_backend_pid()')).scalar_one();db.session.commit()
        barrier.wait(timeout=3)
        assert db.session.execute(text('SELECT pg_backend_pid()')).scalar_one()==pid
        pids.append(pid);db.session.commit();return 'ok'
    action(monkeypatch,write)
    with ThreadPoolExecutor(2) as executor:
        results=list(executor.map(lambda uid:client_for(uid).post('/__stability/write').status_code,[2,3]))
    assert results==[200,200] and len(set(pids))==2
    no_locks(pg)

def test_deletion_waits_through_commits_and_rollback(pg,monkeypatch):
    committed=threading.Event();started=threading.Event();done=threading.Event();finished=threading.Event()
    def write():
        pid=db.session.execute(text('SELECT pg_backend_pid()')).scalar_one()
        db.session.execute(text('UPDATE "user" SET mobile=\'first\' WHERE id=2'));db.session.commit();committed.set()
        assert started.wait(3) and not done.wait(.15)
        assert db.session.execute(text('SELECT pg_backend_pid()')).scalar_one()==pid
        db.session.rollback();assert not done.wait(.15)
        db.session.execute(text('UPDATE "user" SET mobile=\'second\' WHERE id=2'));db.session.commit();finished.set();return 'ok'
    def deletion():
        assert committed.wait(3)
        with pg.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout='4000'"));started.set()
            conn.execute(text('SELECT pg_advisory_xact_lock(16603,2)'))
            assert finished.is_set()
            assert conn.execute(text('SELECT mobile FROM "user" WHERE id=2')).scalar_one()=='second'
            conn.execute(text('UPDATE "user" SET is_banned=true,mobile=NULL WHERE id=2'))
        done.set()
    action(monkeypatch,write)
    with ThreadPoolExecutor(2) as executor:
        future=executor.submit(deletion)
        assert client_for().post('/__stability/write').status_code==200
        future.result(timeout=5)
    assert done.is_set() and client_for().post('/__stability/write').status_code==302
    no_locks(pg)

def test_deletion_first_rechecks_ban(pg,monkeypatch):
    waiting=threading.Event()
    action(monkeypatch,lambda:pytest.fail('Fenced write reached handler'))
    def observe(conn,cursor,sql,params,context,many):
        if 'pg_advisory_lock_shared' in sql: waiting.set()
    event.listen(pg,'before_cursor_execute',observe)
    try:
        with ThreadPoolExecutor(1) as executor:
            with pg.begin() as conn:
                conn.execute(text('SELECT pg_advisory_xact_lock(16603,2)'))
                future=executor.submit(lambda:client_for().post('/__stability/write'))
                assert waiting.wait(3)
                conn.execute(text('UPDATE "user" SET is_banned=true WHERE id=2'))
            response=future.result(timeout=4)
        assert response.status_code==403
    finally: event.remove(pg,'before_cursor_execute',observe)
    no_locks(pg)

def test_error_rolls_back_and_releases_fence(pg,monkeypatch):
    def write():
        db.session.execute(text('UPDATE "user" SET mobile=\'must-rollback\' WHERE id=2'))
        raise ValueError('injected failure')
    action(monkeypatch,write);monkeypatch.setitem(website.app.config,'PROPAGATE_EXCEPTIONS',False)
    assert client_for().post('/__stability/write').status_code==500
    with pg.connect() as conn: assert conn.execute(text('SELECT mobile FROM "user" WHERE id=2')).scalar() is None
    no_locks(pg)

def missing_columns(engine):
    with engine.begin() as conn:
        for name in ('area','latitude','longitude','image_url','listing_status','source'):
            conn.execute(text('ALTER TABLE mechanic_profile DROP COLUMN '+name))
        conn.execute(text("INSERT INTO mechanic_profile (id,business_name,owner_name,phone,city,is_verified,is_featured) VALUES (1,'Local Garage','Owner','synthetic','Pune',false,false)"))

def test_mechanic_six_missing_columns_and_one_free_slot(pg):
    missing_columns(pg)
    with pg.connect() as occupied,website.app.test_request_context('/admin'):
        db.session.execute(text('SELECT 1'));start=time.perf_counter()
        rows,columns=admin._admin_mechanic_payloads()
        assert rows[0]['business_name']=='Local Garage' and 'area' not in columns
        assert admin._admin_mechanic_count(columns,'is_verified',False)==1
        assert admin._admin_mechanic_count(columns)==1 and time.perf_counter()-start<1
    response=client_for(1).get('/admin')
    assert response.status_code==200 and b'Local Garage' in response.data
    assert b'Garage information temporarily unavailable' not in response.data
    assert client_for(2).get('/admin').status_code==403
    assert website.app.test_client().get('/admin').status_code==302

def test_inspection_failure_never_selects_mechanic_columns(pg,monkeypatch):
    missing_columns(pg)
    def fail(_): raise RuntimeError('injected inspection failure')
    monkeypatch.setattr(admin,'sqlalchemy_inspect',fail);statements=[]
    def collect(conn,cursor,sql,params,context,many): statements.append(sql)
    event.listen(pg,'before_cursor_execute',collect)
    try:
        response=client_for(1).get('/admin')
        assert response.status_code==200 and b'Garage information temporarily unavailable' in response.data
        assert not any('mechanic_profile' in sql.lower() for sql in statements)
    finally: event.remove(pg,'before_cursor_execute',collect)

class FrozenDatetime(datetime):
    @classmethod
    def utcnow(cls): return cls(2026,11,14,1,0)

def normalized(value):
    if isinstance(value,dict): return {k:normalized(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [normalized(v) for v in value]
    state=inspect(value,raiseerr=False)
    if state is not None and hasattr(state,'mapper'):
        return {col.key:normalized(getattr(value,col.key)) for col in state.mapper.column_attrs}
    if isinstance(value,datetime): return value.isoformat()
    if hasattr(value,'_mapping'): return list(value)
    return value

def seed_metrics():
    now=FrozenDatetime.utcnow()
    db.session.add_all([User(id=i,username=f'fixture-{i}',email=f'fixture-{i}@example.invalid',password='synthetic',role='user',is_banned=False) for i in range(5,45)])
    db.session.flush()
    for uid in range(1,45):
        db.session.add(Car(owner_id=uid,brand='Local',model='Fixture',is_default=True,created_at=now-timedelta(days=uid),current_km=1000,next_service_km=900 if uid%2 else 1200))
        for offset in ((400,900) if uid == 44 else (0,2,8,40,400)):
            db.session.add(WebsiteVisit(user_id=uid,visit_time=now-timedelta(days=offset,minutes=uid),visitor_id=f'v-{uid}',path='/tools',is_page_view=True,is_authenticated=True,is_admin=uid==1,is_bot=uid%7==0,is_internal=uid%11==0))
        for kind in ('click','security'):
            db.session.add(WebsiteEvent(user_id=uid,event_type=kind,event_time=now-timedelta(minutes=uid),path='/tools',label='fixture',ip_address='synthetic'))
    db.session.add_all([WebsiteVisit(user_id=2,visit_time=now-timedelta(seconds=i+1),visitor_id='repeated',path='/community',is_page_view=True,is_bot=False,is_internal=False,is_admin=False) for i in range(1005)])
    db.session.add(WebsiteVisit(user_id=3,visit_time=now-timedelta(days=900),path='/old',is_page_view=True))
    db.session.add(WebsiteVisit(user_id=4,visit_time=now,path='/not-page',is_page_view=False))
    db.session.execute(text("INSERT INTO website_visit (user_id,visit_time,path,is_page_view,is_bot,is_internal,is_admin) VALUES (3,NULL,'/null-time',true,NULL,NULL,NULL)"))
    db.session.add(WebsiteVisit(user_id=None,visit_time=now,visitor_id='anonymous',path='/',is_page_view=True,is_bot=False,is_internal=False,is_admin=False))
    db.session.commit()

@pytest.mark.parametrize('frequency',['24h','7d','30d','90d','all'])
def test_legacy_full_metric_parity_and_release(pg,monkeypatch,frequency):
    baseline=original('routes/admin_routes.py','_build_admin_analytics_context',vars(admin))
    monkeypatch.setattr(admin,'datetime',FrozenDatetime)
    monkeypatch.setattr(admin,'safe_live_summary',lambda:{'fixture':'unchanged summary'})
    monkeypatch.setattr(admin,'traffic_quality_summary',lambda:{'fixture':12})
    baseline.__globals__.update(datetime=FrozenDatetime,safe_live_summary=admin.safe_live_summary,traffic_quality_summary=admin.traffic_quality_summary)
    with website.app.app_context(): seed_metrics()
    statements=[];holds=[]
    def query(conn,cursor,sql,params,context,many): statements.append(sql)
    def checkout(conn,record,proxy): record.info['stability_checkout']=time.perf_counter()
    def checkin(conn,record): holds.append(time.perf_counter()-record.info.pop('stability_checkout',time.perf_counter()))
    event.listen(pg,'before_cursor_execute',query);event.listen(pg,'checkout',checkout);event.listen(pg,'checkin',checkin)
    try:
        with website.app.test_request_context('/admin/analytics/users?frequency='+frequency):
            start=time.perf_counter();before=normalized(baseline('users'));before_seconds=time.perf_counter()-start;before_queries=len(statements)
            assert db.session().in_transaction();db.session.remove();before_hold=sum(holds)
        statements.clear();holds.clear()
        with website.app.test_request_context('/admin/analytics/users?frequency='+frequency):
            visitor_key=admin._visitor_key
            def assert_released(visit):
                assert not db.session().in_transaction() and pg.pool.checkedout()==0
                return visitor_key(visit)
            monkeypatch.setattr(admin,'_visitor_key',assert_released)
            start=time.perf_counter();after=normalized(admin._build_admin_analytics_context('users'));after_seconds=time.perf_counter()-start;after_queries=len(statements)
            assert not db.session().in_transaction() and pg.pool.checkedout()==0
        assert before==after
        assert after_queries<=25 and before_queries>after_queries*5
        MEASUREMENTS['legacy_'+frequency]=dict(before_queries=before_queries,after_queries=after_queries,before_seconds=before_seconds,after_seconds=after_seconds,before_checkout_hold_seconds=before_hold,after_checkout_hold_seconds=sum(holds),users=len(after['user_rows']),full_context_parity=True)
    finally:
        event.remove(pg,'before_cursor_execute',query);event.remove(pg,'checkout',checkout);event.remove(pg,'checkin',checkin)

def test_legacy_render_all_sections(pg):
    with website.app.app_context(): seed_metrics()
    for section in ('overview','traffic','engagement','users','safety','vehicles'):
        response=client_for(1).get('/admin/analytics/'+section)
        assert response.status_code==200 and b'Analytics temporarily unavailable' not in response.data

def test_save_measurements():
    if MEASUREMENTS: (EVIDENCE/'performance-results.json').write_text(json.dumps(MEASUREMENTS,indent=2))

def test_failed_unlock_discards_physical_connection(pg,monkeypatch):
    def fail_unlock(conn,cursor,sql,params,context,many):
        if 'pg_advisory_unlock_shared' in sql: raise RuntimeError('injected unlock failure')
    event.listen(pg,'before_cursor_execute',fail_unlock)
    try:
        with pytest.raises(RuntimeError,match='injected unlock failure'):
            client_for().post('/__stability/write')
    finally: event.remove(pg,'before_cursor_execute',fail_unlock)
    assert pg.pool.checkedout()==0
    no_locks(pg)

def test_invalidated_writer_cannot_reconnect_without_fence(pg):
    with website.app.test_request_context('/__stability/write', method='POST'):
        g._login_user = db.session.get(User, 2)
        website.account_deletion_write_fence()
        db.session.connection().invalidate()
        db.session.rollback()
        with pytest.raises(RuntimeError, match='invalidated'):
            db.session.execute(text('SELECT 1'))
    no_locks(pg)


@pytest.mark.parametrize('path,accept', [
    ('/__stability/write', 'text/html'),
    ('/__stability/write', 'application/json'),
    ('/api/__stability/write', 'application/json'),
])
@pytest.mark.parametrize('outcome', ['exception', '500', '503', '404', '403', 'success', 'redirect'])
def test_invalidated_fence_full_http_recovery(pg, monkeypatch, caplog, path, accept, outcome):
    """Exercise dispatch, error handling, all response callbacks and teardown."""
    state = {'invalidated': False, 'checkouts': 0, 'reconnects': 0, 'late_sql': [], 'late_identity_reads': 0}
    client = client_for()
    pool_connect = pg.pool.connect
    render_template = website.render_template
    avatar_diagnostics = website.log_authenticated_avatar_state
    user_parts = analytics._current_user_parts

    def checked_checkout():
        state['checkouts'] += 1
        if state['invalidated']:
            state['reconnects'] += 1
            raise AssertionError('Pool checkout after invalidation')
        return pool_connect()

    def checked_render(*args, **kwargs):
        assert not state['invalidated'], 'ORM-dependent template after invalidation'
        return render_template(*args, **kwargs)

    def checked_avatar(user):
        assert not state['invalidated'], 'Avatar attributes read after invalidation'
        return avatar_diagnostics(user)

    def checked_identity():
        if state['invalidated']:
            state['late_identity_reads'] += 1
            raise AssertionError('Collector read ORM identity after invalidation')
        return user_parts()

    def checked_sql(conn, cursor, sql, params, context, many):
        if state['invalidated']:
            state['late_sql'].append(sql)
            raise AssertionError('SQL after invalidation')

    def write():
        user = current_user._get_current_object()
        connection = db.session.connection()
        assert connection.execute(text(
            "SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
            "AND classid=16603 AND objid=2 AND pid=pg_backend_pid() AND granted"
        )).scalar_one() == 1
        db.session.execute(text('UPDATE "user" SET mobile=\'must-rollback\' WHERE id=2'))
        connection.invalidate()
        state['invalidated'] = True
        db.session.rollback()
        assert inspect(user).expired_attributes
        if outcome == 'exception':
            raise ValueError('PRIVATE injected disconnect detail')
        if outcome in ('500', '503', '404', '403'):
            abort(int(outcome))
        if outcome == 'redirect':
            return 'PRIVATE success body', 302, {'Location': '/private-target'}
        with pytest.raises(RuntimeError, match='invalidated'):
            db.session.execute(text('UPDATE "user" SET mobile=\'bypass\' WHERE id=2'))
        return 'PRIVATE success body', 200

    action(monkeypatch, write)
    caplog.set_level(logging.ERROR)
    # Do not let Flask's production exception wrapper conceal secondary errors.
    monkeypatch.setitem(website.app.config, 'PROPAGATE_EXCEPTIONS', True)
    with monkeypatch.context() as guard:
        guard.setattr(pg.pool, 'connect', checked_checkout)
        guard.setattr(website, 'render_template', checked_render)
        guard.setattr(website, 'log_authenticated_avatar_state', checked_avatar)
        guard.setattr(analytics, '_current_user_parts', checked_identity)
        event.listen(pg, 'before_cursor_execute', checked_sql)
        try:
            response = client.post(path, headers={'Accept': accept})
        finally:
            event.remove(pg, 'before_cursor_execute', checked_sql)
    assert response.status_code == 500
    assert response.mimetype == accept
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'Location' not in response.headers
    assert b'PRIVATE' not in response.data
    if accept == 'application/json':
        assert response.json == {'status': 'error', 'message': 'Internal server error'}
    else:
        assert b'The request could not be completed safely' in response.data
    assert state == {'invalidated': True, 'checkouts': 1, 'reconnects': 0, 'late_sql': [], 'late_identity_reads': 0}
    assert not caplog.records  # No secondary exception hidden in response processing.
    assert pg.pool.checkedout() == 0
    no_locks(pg)
    with pg.connect() as connection:
        assert connection.execute(text('SELECT mobile FROM "user" WHERE id=2')).scalar_one() is None
    # A fresh request must acquire its own valid fence, not retain failure state.
    def normal_write():
        db.session.execute(text('UPDATE "user" SET mobile=\'normal\' WHERE id=2'))
        db.session.commit()
        return 'normal response'
    action(monkeypatch, normal_write)
    normal = client.post('/__stability/write', headers={'Accept': accept})
    assert normal.status_code == 200 and normal.data == b'normal response'
    assert pg.pool.checkedout() == 0
    no_locks(pg)


def test_track_event_invalidated_fence_full_http(pg, monkeypatch, caplog):
    monkeypatch.setenv('ANALYTICS_ENABLED', 'true')
    client = client_for()
    client.set_cookie('ampyan_analytics_consent', 'granted')
    state = {'invalidated': False, 'reconnects': 0}
    pool_connect = pg.pool.connect

    def checked_checkout():
        if state['invalidated']:
            state['reconnects'] += 1
            raise AssertionError('Tracking request reconnected after invalidation')
        return pool_connect()

    def enqueue(_):
        db.session.connection().invalidate()
        state['invalidated'] = True
        db.session.rollback()
        raise ValueError('PRIVATE collector failure')

    monkeypatch.setattr(analytics, '_enqueue', enqueue)
    caplog.set_level(logging.ERROR)
    monkeypatch.setitem(website.app.config, 'PROPAGATE_EXCEPTIONS', True)
    with monkeypatch.context() as guard:
        guard.setattr(pg.pool, 'connect', checked_checkout)
        response = client.post('/api/track-event', json={'event_type': 'page_view'})
    assert response.status_code == 500
    assert response.json == {'status': 'error', 'message': 'Internal server error'}
    assert state == {'invalidated': True, 'reconnects': 0}
    assert not caplog.records
    assert pg.pool.checkedout() == 0
    no_locks(pg)


def test_full_http_invalidation_during_fence_acquisition(pg, monkeypatch, caplog):
    state = {'invalidated': False, 'reconnects': 0}
    client = client_for()
    pool_connect = pg.pool.connect

    def checked_checkout():
        if state['invalidated']:
            state['reconnects'] += 1
            raise AssertionError('Reconnected after failed fence acquisition')
        return pool_connect()

    def disconnect(conn, cursor, sql, params, context, many):
        if 'pg_advisory_lock_shared' in sql:
            conn.invalidate()
            state['invalidated'] = True
            raise RuntimeError('PRIVATE disconnect while acquiring fence')

    action(monkeypatch, lambda: pytest.fail('Handler ran without a fence'))
    caplog.set_level(logging.ERROR)
    monkeypatch.setitem(website.app.config, 'PROPAGATE_EXCEPTIONS', True)
    with monkeypatch.context() as guard:
        guard.setattr(pg.pool, 'connect', checked_checkout)
        event.listen(pg, 'before_cursor_execute', disconnect)
        try:
            response = client.post('/__stability/write')
        finally:
            event.remove(pg, 'before_cursor_execute', disconnect)
    assert response.status_code == 500
    assert b'The request could not be completed safely' in response.data
    assert b'PRIVATE' not in response.data
    assert state == {'invalidated': True, 'reconnects': 0}
    assert not caplog.records
    assert pg.pool.checkedout() == 0
    no_locks(pg)


def test_track_event_and_storage_worker_share_remaining_slot(pg,monkeypatch):
    monkeypatch.setenv('ANALYTICS_ENABLED','true')
    started=threading.Event();futures=[]
    with ThreadPoolExecutor(1) as executor:
        def persist(item):
            with website.app.app_context():
                started.set()
                analytics._persist(item)
        def enqueue(item):
            futures.append(executor.submit(persist,item))
            assert started.wait(2)
            return True
        monkeypatch.setattr(analytics,'_enqueue',enqueue)
        client=client_for();client.set_cookie('ampyan_analytics_consent','granted')
        with pg.connect() as occupied:
            response=client.post('/api/track-event',json={'event_type':'page_view'})
            assert response.status_code==202
            for future in futures: future.result(timeout=3)
    with pg.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM analytics_event WHERE event_type='page_view'")).scalar()==1
    no_locks(pg)

def test_batch_queries_bounded_at_500_users(pg):
    with website.app.app_context():
        db.session.add_all([User(id=i,username=f'large-{i}',email=f'large-{i}@example.invalid',password='synthetic',role='user') for i in range(5,505)])
        db.session.commit()
        statements=[]
        def collect(conn,cursor,sql,params,context,many): statements.append(sql)
        event.listen(pg,'before_cursor_execute',collect)
        try:
            result=admin._legacy_user_stats(list(range(5,505)),FrozenDatetime.utcnow()-timedelta(days=30))
            assert len(result)==500 and len(statements)==4
        finally: event.remove(pg,'before_cursor_execute',collect)
