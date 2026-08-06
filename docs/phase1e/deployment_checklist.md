# Deployment checklist

This is the required order. Phase 1E executes none of these actions.

1. **Git commit**
   - [ ] Separate Website and API commits; exclude unrelated diagnosis/news work.
   - [ ] Include migration files, Blog implementation, Phase 1D evidence, and
     Phase 1E documents intentionally.
   - [ ] Review staged diff and secret scan.
2. **Git push**
   - [ ] Push reviewed commits to the approved release branches.
   - [ ] Record immutable commit SHAs.
3. **Render API**
   - [ ] Deploy API commit with Blog flag still `false`.
   - [ ] Verify health and non-Blog API smoke tests.
4. **Render Website**
   - [ ] Deploy Website commit with Blog flag still `false`.
   - [ ] Verify health, navigation, login, News, Community, Garage, and AI.
   - [ ] Confirm neither service uses a persistent disk if zero-downtime Render
     deployment is being assumed.
5. **Migration**
   - [ ] Reconfirm backup and catalog preflight.
   - [ ] Apply upgrade exactly once and verify 13 tables.
6. **Smoke test**
   - [ ] Run the production-safe, non-destructive smoke checklist with flags false.
7. **Internal testing**
   - [ ] Enable only in an approved internal/staging context, not publicly.
   - [ ] Exercise author, moderator, media, comments, analytics, and rollback.
8. **Enable feature flag — deferred**
   - [ ] Separate approval required; coordinate API then Website and verify.
9. **Public announcement — deferred**
   - [ ] Separate production-release task and business approval required.

At every step, record operator, timestamp, deploy ID, commit SHA, outcome, and
rollback decision. Stop immediately on an abort criterion.

Render normally keeps the old web-service instance serving while the new one
starts, then swaps traffic after successful startup; persistent disks disable
this zero-downtime behavior. See [Render deploy behavior](https://render.com/docs/deploys).
