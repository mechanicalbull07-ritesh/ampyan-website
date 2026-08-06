# Production backup checklist

No restore or production write is authorized by this document.

## Required pre-migration proof

- [ ] Identify the exact production PostgreSQL database and owner.
- [ ] Confirm Render backup/PITR entitlement and retention for that database.
- [ ] Record latest successful backup timestamp: **TBD**.
- [ ] Require backup age to be within the release window agreed by operations.
- [ ] Create an on-demand pre-migration backup if policy requires it.
- [ ] Record immutable backup/snapshot identifier: **TBD**.
- [ ] Confirm backup completed before migration begins.
- [ ] Confirm backup covers the existing `user` table and all non-Blog data.
- [ ] Verify restore credentials and an authorized restore operator are available.
- [ ] Verify sufficient storage/quota for a restored database.

## Restore procedure to validate with Render

1. Abort release and keep both Blog feature flags `false`.
2. Prevent further application writes if a full-database restore is required.
3. In Render, restore the recorded snapshot/PITR point to a new database when
   possible; do not overwrite the only production database without approval.
4. Validate row counts, schema, extensions, ownership, and application access
   on the restored database.
5. Switch `DATABASE_URL` only through an approved change and redeploy/restart.
6. Run non-destructive health, login, News, Community, and Blog-disabled checks.
7. Retain the original database until recovery is accepted.

Current Render behavior: paid PostgreSQL instances provide PITR; the recovery
window is three days on Hobby workspaces and seven days on Pro or higher.
Render restores PITR into a new database, and the chosen recovery point cannot
be within ten minutes of the current time. On-demand logical exports are kept
for seven days. Verify the actual production plan and available window in the
database Recovery page. See [Render Postgres recovery and backups](https://render.com/docs/postgresql-backups).

## Rollback choice

- Before any Blog data exists: reviewed downgrade may remove the 13 Blog tables.
- After any Blog data exists: export Blog data first; prefer feature-flag
  rollback or database restore. The downgrade permanently deletes Blog data.

## Timing record

- Backup duration: **TBD**
- Restore rehearsal duration: **TBD**
- Estimated production restore time: **UNVERIFIED**
- Maximum acceptable RTO/RPO: **TBD by owner**
- Current status: **FAIL — latest backup and restore timing not verified**
