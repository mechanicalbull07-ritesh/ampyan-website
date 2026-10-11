# Community Blog final deployment preparation

Date: 2026-08-06

This is an execution-ready runbook for the next separately authorized task.
Nothing in this document was executed during Phase 2 preparation.

## Fixed targets

- API: `ampyan-api` / `srv-d7quug1kh4rs73eh4q3g`
- Website: `ampyan-website-1` / `srv-d7r0j49kh4rs73ei9pm0`
- Database: `ampyan-db` / `dpg-d7quoojbc2fs7380t6eg-a`
- API URL: `https://ampyan-api.onrender.com`
- Website URL: `https://ampyan-website-1.onrender.com`

Never target the legacy `ampyan-website` service.

## Required operator variables

Set these only in the release operator's secured shell; do not commit them:

```sh
export API_RELEASE_SHA='<reviewed-api-commit-sha>'
export WEBSITE_RELEASE_SHA='<reviewed-website-commit-sha>'
export PRODUCTION_DATABASE_URL='<freshly-retrieved-production-database-url>'
```

## Final deployment commands

Keep both Blog flags explicitly false throughout.

```sh
render deploys create srv-d7quug1kh4rs73eh4q3g \
  --commit "$API_RELEASE_SHA" --wait --confirm

render deploys create srv-d7r0j49kh4rs73ei9pm0 \
  --commit "$WEBSITE_RELEASE_SHA" --wait --confirm
```

After each command, record the deploy ID, commit SHA, start/end time, health
result, and operator. Abort before the Website deployment if the API gate fails.

## Final migration command

Run from the reviewed API release checkout only after the full Phase 1F
execution-once preflight, same-window PITR check, schema check, external ledger
entry, and single-operator lock:

```sh
cd /Users/riteshkumar/motronix_api
psql "$PRODUCTION_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f migrations/20260726_community_blog_up.sql
```

Do not retry after ambiguous output. Query the live catalog first. The migration
is not SQL-idempotent and must execute exactly once.

## Rollback commands

First keep both `COMMUNITY_BLOG_ENABLED` values false. For application rollback,
record the selected known-good deploy IDs and use the Render Dashboard rollback,
which also disables auto-deploy. If the API endpoint is required, disable
auto-deploy first and then call `POST /v1/services/{serviceId}/rollback` with
the known-good `deployId`; API-triggered rollback does not disable auto-deploy.

Database rollback is separately authorized only when migration committed and
no Blog data exists:

```sh
cd /Users/riteshkumar/motronix_api
psql "$PRODUCTION_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f migrations/20260726_community_blog_down.sql
```

If migration failed transactionally, inspect whether zero or 13 Blog tables
exist and do not run downgrade blindly. If any Blog data exists, do not run the
destructive downgrade; keep flags false and use export/repair/PITR under incident
approval.

## Smoke-test order

1. API health and database connectivity.
2. Website health, homepage, navigation, and static assets.
3. Login, register, session, logout, and CSRF rejection behavior.
4. News, Community, Garage, and AI Diagnosis non-regression.
5. Confirm Blog navigation and public Blog routes remain disabled.
6. After migration, verify exactly 13 Blog tables, JSONB, constraints, indexes,
   unchanged non-Blog fingerprint, and no orphan objects.
7. Run approved internal/non-public Blog API, editor, comments, media,
   moderation, analytics, SEO, responsive, and performance smoke checks while
   the public feature flag remains false.

## Observation windows

- API deploy: minimum 30 minutes healthy before Website deployment.
- Website deploy: minimum 30 minutes healthy before migration authorization.
- Migration and internal smoke: minimum 60 minutes after completion.
- Continue enhanced monitoring for 24 hours; feature enablement remains a
  separate decision.

Monitor 5xx/404 rates, CSRF failures, response time, CPU, memory, database
connections/locks, failed uploads, comment failures, unexpected payload
rejections, and application logs.

## Success criteria

- Correct reviewed SHAs are live and all Render deploys are healthy.
- Both Blog flags remain false and configuration fingerprints match the report.
- Core Website/API smoke tests pass with no material error or latency increase.
- Migration runs once, creates exactly 13 valid Blog tables, and changes no
  non-Blog data/schema fingerprint.
- Internal Blog smoke checks pass; Cloudinary upload verification passes.
- Metrics stay within the accepted baseline for every observation window.

## Abort criteria

Abort on wrong target/SHA, flag unexpectedly true, failed health check, elevated
5xx/latency, authentication or CSRF regression, missing backup/PITR proof,
migration-ledger conflict, unexpected Blog table, SQL/lock timeout, ambiguous
connection loss, invalid constraint/index, non-Blog change, secret exposure,
connection exhaustion, failed media smoke, or unexplained resource growth.

Render deployment and rollback behavior references:
https://render.com/docs/deploys and https://render.com/docs/rollbacks
