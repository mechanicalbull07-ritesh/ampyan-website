# Rollback checklist

## Triggers

Rollback or abort on elevated 5xx/latency, failed health checks, migration
error, invalid/missing constraints, authentication/CSRF regression, secret
exposure, database connection exhaustion, data corruption, failed uploads,
or incorrect public visibility.

## Immediate containment

1. Set Website `COMMUNITY_BLOG_ENABLED=false`.
2. Set API `COMMUNITY_BLOG_ENABLED=false`.
3. Confirm Blog UI/API are unavailable while core Website/API remain healthy.
4. Pause rollout and announcement; preserve logs and deploy/migration IDs.

## Application rollback

- [ ] Select the last known-good API deploy in Render and roll back.
- [ ] Select the last known-good Website deploy in Render and roll back.
- [ ] Confirm autodeploy behavior: Dashboard rollback disables autodeploy;
  Render API rollback does not, so disable it separately when using the API.
- [ ] Do not change `DATABASE_URL` or secrets unless the incident requires it.
- [ ] Verify health, login, News, Community, Garage, and AI Diagnosis.

## Database rollback decision

- If migration failed inside its transaction: verify zero Blog tables and do
  not run the downgrade blindly.
- If migration succeeded and no Blog data was created: the reviewed downgrade
  may be authorized separately:

```sh
psql "$PRODUCTION_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f migrations/20260726_community_blog_down.sql
```

- If any Blog data exists: do not use the downgrade without export and explicit
  destructive approval. Keep flags false and restore/repair from the verified
  backup plan.

## Verification

- [ ] Both flags are false.
- [ ] No Blog navigation/API exposure remains.
- [ ] Core health and non-Blog smoke tests pass.
- [ ] Expected schema state is documented: 13 tables retained or zero removed.
- [ ] Existing users/non-Blog data are unchanged.
- [ ] Error rate, latency, CPU, memory, and database connections normalize.
- [ ] Incident owner records cause, scope, data impact, and next decision.

Disposable rollback rehearsal: **PASS**. Production rollback: **NOT RUN**.

Reference: [Render service rollbacks](https://render.com/docs/rollbacks).
