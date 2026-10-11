# Recommended release commit sequence

No commit was created during Phase 1F.

Use new release branches/worktrees from the recorded `main` heads. Preserve the
current dirty worktrees as source material; do not reset or rewrite history.

## API repository

1. **News identity/content work** — separate non-Blog commit(s)
   - Stage News service/tests/docs and only News hunks from `app.py`.
   - Run News-focused and full API regressions.
2. **Diagnosis contract/quality work** — separate non-Blog commit(s)
   - Stage Diagnosis engine/services/fixtures/tests and only Diagnosis hunks
     from `app.py`.
   - Run diagnosis-focused and full API regressions.
3. **Community Blog API release**
   - Stage `blog/`, Blog model/services/migrations/tests/docs, `.env.example`,
     Render Blog declarations, Pillow, and only Blog-required `app.py` hunks.
   - Exclude News, Diagnosis, unrelated Community serialization, and
     `CHATGPT_HANDOFF.md` unless separately approved.
   - Suggested message: `Add Community Blog API behind disabled feature flag`.
   - Run full API, focused Blog/media, PostgreSQL migration, and static/security checks.

If Blog depends on a specific News identity-sequence repair, make that repair a
reviewed prerequisite commit and document the dependency; do not silently mix it
into the Blog commit.

## Website repository

4. **Phase 1D retained evidence and harness correction**
   - Stage the Phase 1D handoff, payload harness, JSON, and Markdown evidence.
   - Suggested message: `Retain Community Blog Phase 1D approval evidence`.
5. **Phase 1E/1F release-readiness documentation**
   - Stage `docs/phase1e/` and `docs/phase1f/`.
   - Suggested message: `Document Community Blog production release controls`.

The Website Community Blog implementation is already in HEAD `dcdb1ab`; verify
the final release diff from the production deploy SHA rather than recommitting it.

## Final controls

- Review `git diff --cached` for every commit.
- Run a secret scan before committing.
- Require clean status after each scoped commit in the isolated worktree.
- Push only during Phase 2 after explicit approval.
