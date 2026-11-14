"""Keep a deletion-fenced request on one externally owned connection.

PostgreSQL session advisory locks survive ORM commits. Returning that connection
to the pool before request teardown would allow unrelated work to inherit the
lock, so ownership must begin at the first ORM checkout (including user loading).
"""
import os

from flask import g, has_request_context, request
from flask_sqlalchemy.session import Session


def fence_connection_invalidated():
    """Inspect request-owned state only; never resolve a user or query the DB."""
    if not has_request_context():
        return False
    connection = g.get("deletion_connection")
    if g.get("deletion_connection_failed") or (
        connection is not None and (connection.invalidated or connection.closed)
    ):
        # Failure is terminal for this request, even if another caller later
        # changes the Connection object's state. Never recover by reconnecting.
        g.deletion_connection_failed = True
        return True
    return False


class RequestSession(Session):
    def get_bind(self, mapper=None, clause=None, bind=None, **kwargs):
        engine = super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)
        if (
            has_request_context()
            and request.method not in ("GET", "HEAD", "OPTIONS")
            and os.environ.get("ACCOUNT_DELETION_ENABLED", "").lower() == "true"
            and engine is self._db.engines[None]
            and engine.dialect.name == "postgresql"
        ):
            connection = g.get("deletion_connection")
            if connection is None:
                connection = engine.connect()
                g.deletion_connection = connection
            # An invalidated connection must never reconnect without its lock.
            if fence_connection_invalidated():
                raise RuntimeError("Deletion fence connection was invalidated")
            return connection
        return engine


def close_request_connection(db):
    connection = g.get("deletion_connection")
    if connection is None:
        return
    try:
        # Roll back unfinished ORM work before unlocking, without returning the
        # externally owned connection to the pool.
        db.session.remove()
        connection.rollback()
        if connection.invalidated:
            return  # Physical session and its locks have already been discarded.
        if g.get("deletion_fence_locked"):
            from sqlalchemy import text

            unlocked = connection.execute(
                text("SELECT pg_advisory_unlock_shared(16603,:owner)"),
                {"owner": g.deletion_owner},
            ).scalar_one()
            if not unlocked:
                raise RuntimeError("Deletion fence lock ownership lost")
            connection.rollback()
    except BaseException:
        # A failed unlock must discard the physical connection, never pool a
        # session that might still own an advisory lock.
        connection.invalidate()
        raise
    finally:
        g.pop("deletion_connection", None)
        g.pop("deletion_fence_locked", None)
        g.pop("deletion_connection_failed", None)
        connection.close()
