"""Opt-in disposable local PostgreSQL concurrency check.

Set TRAFFIC_TEST_DATABASE_URL to the dedicated local test database only.
"""

import multiprocessing
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.dialects.postgresql import insert

from models.models import TrafficMetric


def _increment_worker(url, hour, repetitions, start):
    engine = create_engine(url)
    table = TrafficMetric.__table__
    for _ in range(repetitions):
        statement = insert(table).values(hour_start_utc=hour, quality="human_like", count=1)
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.hour_start_utc, table.c.quality],
            set_={"count": table.c.count + 1},
        )
        start.wait()
        with engine.begin() as connection:
            connection.execute(statement)
    engine.dispose()


def test_two_process_postgres_counter_does_not_lose_increments():
    url = os.environ.get("TRAFFIC_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Dedicated local PostgreSQL URL not configured")
    identity = make_url(url)
    assert identity.database == "ampyan_traffic_quality_test"
    assert identity.host in {None, "", "localhost", "127.0.0.1"}
    assert identity.query.get("host", "").startswith("/private/tmp/ampyan-traffic-quality-pg")

    hour = "2026-01-01 00:00:00"
    engine = create_engine(url)
    TrafficMetric.__table__.create(engine, checkfirst=True)
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM traffic_metric WHERE hour_start_utc = :hour"), {"hour": hour})
    ctx = multiprocessing.get_context("spawn")
    start = ctx.Event()
    workers = [ctx.Process(target=_increment_worker, args=(url, hour, 50, start)) for _ in range(2)]
    for worker in workers:
        worker.start()
    start.set()
    for worker in workers:
        worker.join(timeout=30)
        assert worker.exitcode == 0
    with engine.connect() as connection:
        count = connection.execute(text("SELECT count FROM traffic_metric WHERE hour_start_utc = :hour AND quality = 'human_like'"), {"hour": hour}).scalar_one()
    assert count == 100
    engine.dispose()
