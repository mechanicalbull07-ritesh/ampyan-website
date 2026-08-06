# Production backup verification report

Verification date: 2026-08-06

## Verified production state

- Database: `ampyan-db`
- PostgreSQL: version 18, status available
- Render PITR status: **AVAILABLE**
- Earliest current recovery point: **2026-08-03 03:21:40 UTC**
- Logical exports currently retained: **0**
- Restore operator: authenticated workspace owner, or another explicitly
  authorized Render workspace administrator

Render provides continuous PITR rather than a discrete latest-backup timestamp.
The official recovery workflow does not permit selecting a restore point within
ten minutes of current time, so the latest recoverable point is approximately
ten minutes behind live production.

## Planning estimates

- Estimated database recovery creation: **30–60 minutes**
- Estimated operational RTO including validation and connection switch:
  **60–90 minutes**
- Estimated RPO: **approximately 10 minutes**

These are conservative planning estimates for the current 1 GB database, not
measured guarantees. Phase 1F intentionally did not trigger a restore.

## Required release record

- Record the PITR status and window again immediately before migration.
- Record the selected pre-migration timestamp in UTC.
- Prefer creating an on-demand logical export for an additional immutable
  checkpoint; wait for completion and record its export ID.
- Confirm the named restore operator is present for the migration window.
- If PITR is no longer `AVAILABLE`, abort.

References:

- [Render Postgres recovery and backups](https://render.com/docs/postgresql-backups)
- [Render recovery-status API](https://api-docs.render.com/reference/retrieve-postgres-recovery-info)

Production backup verification: **PASS**, subject to the mandatory same-window
recheck and optional logical export in Phase 2.
