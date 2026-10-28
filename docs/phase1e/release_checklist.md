# Community Blog release checklist

## Pre-deploy

- [ ] Repository audit is PASS and worktrees/releases are clean and reviewed.
- [ ] Website/API release commits contain no unrelated changes.
- [ ] Live environment checklist is signed off with both Blog flags false.
- [ ] Latest production backup ID/time and restore operator are recorded.
- [ ] Restore time/RTO/RPO are accepted.
- [ ] Migration and rollback commands are reviewed by two operators.
- [ ] Maintenance/release window and communications owners are assigned.
- [ ] Phase 1D evidence and Phase 1E rehearsal remain available.

## Deploy and migrate

- [ ] Follow `deployment_checklist.md` exactly.
- [ ] Record commit SHAs and Render deploy IDs.
- [ ] Keep both feature flags false through code deployment and migration.
- [ ] Run migration preflight, execute upgrade once, and verify 13 tables.
- [ ] Run production-safe smoke tests.

## Internal validation

- [ ] Obtain separate authorization for internal-only flag activation.
- [ ] Run Blog author/moderator/media/comment/analytics tests with synthetic data.
- [ ] Confirm monitoring and rollback operators are present.
- [ ] Remove explicitly identified synthetic data when approved.

## Success criteria

- All repository, configuration, backup, migration, smoke, and monitoring gates pass.
- Core Website/API behavior remains healthy.
- Migration produces exactly the reviewed schema without non-Blog changes.
- No secret exposure, corruption, unexpected error spike, or resource regression.
- Rollback remains immediately available.

## Abort criteria

Abort for any unresolved dirty/unreviewed release content, missing backup proof,
configuration mismatch, migration ambiguity, failing smoke test, authentication
or CSRF regression, database anomaly, secret exposure, or monitoring gap.

## Deferred public release

- [ ] Public feature activation requires a separate Production Release task.
- [ ] Public announcement requires separate product/business approval.
- [ ] Do not infer approval from completion of these documents.

Phase 1E documentation: **COMPLETE**

Ready for Production Deployment: **NO — live Render and backup verification,
plus clean release commits, remain required.**
