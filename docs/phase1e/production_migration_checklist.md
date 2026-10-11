# Production migration checklist

Migration files live in the API repository:

- `migrations/20260726_community_blog_up.sql`
- `migrations/20260726_community_blog_down.sql`

## Audit result

- Upgrade/downgrade are enclosed in `BEGIN`/`COMMIT`.
- Upgrade creates 13 Blog tables, JSONB content blocks, foreign keys, unique
  constraints, check constraints, and query indexes.
- Downgrade removes tables in dependency-safe order.
- Upgrade changes no existing table definition.
- Upgrade is **not SQL-idempotent**. Never run it twice; use a migration ledger
  and a preflight catalog query.
- Downgrade is destructive. Never run it after Blog data exists without export
  and explicit approval.

## Preflight — read-only

- [ ] Live configuration and backup gates are PASS.
- [ ] Both Blog feature flags are confirmed `false`.
- [ ] Record production database hostname/name without credentials.
- [ ] Confirm PostgreSQL version and free storage.
- [ ] Confirm the `user` table and referenced IDs exist.
- [ ] Confirm no public table name matches `blog%`.
- [ ] Confirm no prior migration-ledger entry exists.
- [ ] Review active transactions/locks and choose a low-traffic window.
- [ ] Set `ON_ERROR_STOP=1`, statement timeout, and lock timeout.
- [ ] Record pre-migration table/row counts and backup identifier.

## Authorized execution template — do not run during Phase 1E

```sh
psql "$PRODUCTION_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f migrations/20260726_community_blog_up.sql
```

Run only from the reviewed API release commit and only after separately
authorizing production migration.

## Post-migration verification

- [ ] Exactly 13 public `blog%` tables exist.
- [ ] `blog_content_blocks.data` is JSONB.
- [ ] Required primary, foreign, unique, and check constraints exist.
- [ ] Required indexes exist and are valid.
- [ ] Existing `user` and non-Blog row counts match preflight.
- [ ] No invalid indexes, orphan constraints, or migration errors exist.
- [ ] Add the migration ledger entry only after verification succeeds.
- [ ] Keep flags `false`; schema presence does not authorize launch.

## Abort criteria

Abort on lock-timeout, statement error, unexpected pre-existing Blog object,
non-Blog row/count change, invalid index/constraint, database health alert, or
missing backup proof. Do not retry blindly after an ambiguous outcome.
