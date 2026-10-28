# Migration execution-once preflight

The migration SQL is unchanged. Safety comes from a release ledger, catalog
preflight, transaction enforcement, and an explicit operator lock.

## Release identity

- Migration ID: `20260726_community_blog_up`
- Expected pre-state: zero public tables matching `blog%`
- Expected post-state: exactly 13 reviewed Blog tables
- Required command behavior: `psql -v ON_ERROR_STOP=1`

## Before execution

- [ ] Both production Blog flags are explicitly `false`.
- [ ] Configuration and backup reports are PASS in the same release window.
- [ ] Record release commit SHA, database ID, operator, and UTC timestamp.
- [ ] Acquire the operational migration lock: one named operator and one shell;
  no parallel Render job, deploy hook, or second terminal may run migration.
- [ ] Check the team migration ledger for ID `20260726_community_blog_up`.
- [ ] Query `information_schema.tables` for public `blog%` tables.
- [ ] Abort if the ledger says applied, any Blog table exists, or state is ambiguous.
- [ ] Record existing `user` count and a non-Blog schema fingerprint.
- [ ] Confirm PITR `AVAILABLE` and record its window start.
- [ ] Set reviewed statement and lock timeouts for the session.

## Execute exactly once

1. Insert a `running` entry into the external/team release ledger with migration
   ID, commit SHA, operator, database ID, and start time.
2. Run the reviewed upgrade once using `ON_ERROR_STOP=1`.
3. Do not retry automatically after lost output or network interruption.
4. Query the catalog to determine committed state before any decision.
5. Verify exactly 13 tables, required indexes/constraints, JSONB type, and
   unchanged non-Blog fingerprint.
6. Mark the ledger `applied` only after verification; include finish time and
   evidence. If verification fails, mark `failed/ambiguous` and stop.

## Duplicate prevention

- CI/CD must not contain the migration in API startup, Website startup, or both
  deploy pipelines.
- Only the named migration operator may execute it.
- The Phase 2 runbook must check both the ledger and live schema; neither check
  alone is sufficient.
- A duplicate command is expected to fail on `CREATE TABLE`; rehearsal proved
  the transaction leaves all existing Blog tables and rows unchanged. This is
  a last defense, not the execution-once mechanism.

## Rollback trigger

Abort/rollback on SQL error, lock timeout, unexpected existing object,
non-Blog fingerprint change, missing/invalid index or constraint, database
health degradation, or ambiguous connection loss. Keep both flags false.

- If the transaction failed: verify whether zero or 13 Blog tables exist before
  taking action; do not run downgrade blindly.
- If committed and no Blog data exists: separately authorize the reviewed down
  migration.
- If Blog data exists: do not run destructive down migration; use flag rollback,
  export, repair, or PITR according to the incident decision.

Migration audit: **PASS — non-idempotent SQL is controlled by explicit
execution-once safeguards and transactional failure behavior.**
