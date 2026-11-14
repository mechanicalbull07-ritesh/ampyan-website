"""Exact function from deployed SHA d37fe3a6c39e91cf9ff65c4b3225f86ddd828d0c."""
def account_deletion_write_fence():
    if os.environ.get("ACCOUNT_DELETION_ENABLED", "").lower() != "true" or request.method in ("GET", "HEAD", "OPTIONS"):
        return
    if not current_user.is_authenticated:
        return
    if current_user.is_banned:
        return "Account unavailable", 403
    if db.engine.dialect.name == "postgresql":
        from sqlalchemy import text as deletion_text
        from flask import g
        conn = db.engine.connect()
        g.deletion_fence = conn
        g.deletion_owner = current_user.id
        conn.execute(deletion_text("SELECT pg_advisory_lock_shared(16603,:owner)"), {"owner": current_user.id})
        flags = conn.execute(deletion_text('SELECT is_banned FROM "user" WHERE id=:owner'), {"owner": current_user.id}).first()
        if not flags or flags[0]:
            return "Account unavailable", 403
