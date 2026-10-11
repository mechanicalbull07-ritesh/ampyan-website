# Production environment verification report

Verification date: 2026-08-06

Method: authenticated, read-only Render CLI/API. Secret values were never
printed or written to repository files.

## Live resources

- PostgreSQL: `ampyan-db`, PostgreSQL 18, available, Oregon, 1 GB disk.
- API: `ampyan-api`, starter, one instance, `main`, auto-deploy enabled.
- Active Website: `ampyan-website-1`, starter, one instance, `main`,
  auto-deploy disabled, live at commit `dcdb1ab`.
- Legacy Website: `ampyan-website`, free; recent deploys are failed and it is
  not the live Website release target.

## API findings

| Requirement | Result |
|---|---|
| `COMMUNITY_BLOG_ENABLED=false` explicitly configured | FAIL — absent |
| `BLOG_WEBSITE_SERVICE_TOKEN` present | FAIL — absent |
| `DATABASE_URL` present | PASS |
| `SECRET_KEY` present | PASS |
| Cloudinary configuration complete | FAIL — absent/incomplete |
| SMTP configuration complete | FAIL — absent/incomplete |
| `BLOG_MEDIA_TEST_MODE` disabled | PASS — absent |
| Other feature flags consistent | `AI_REASONING_ENGINE_ENABLED` absent live; blueprint default is `false` |

The live API currently has only `DATABASE_URL`, `FLASK_DEBUG`, `FLASK_ENV`, and
`SECRET_KEY` configured.

## Active Website findings

| Requirement | Result |
|---|---|
| `COMMUNITY_BLOG_ENABLED=false` explicitly configured | FAIL — absent |
| `BLOG_WEBSITE_SERVICE_TOKEN` present | FAIL — absent |
| `AMPYAN_API_BASE_URL` points to production API | FAIL — absent |
| `DATABASE_URL` present | PASS |
| `SECRET_KEY` present | PASS |
| Existing Cloudinary configuration present | PASS |
| Website mail configuration complete | FAIL — absent/incomplete |
| CSRF implementation | PASS — global Flask-WTF protection in deployed code baseline |

Because the feature parser defaults an absent Blog flag to disabled, the Blog
is currently disabled. Release approval nevertheless requires the flag to be
explicitly set to `false` on both services.

## Required remediation before Phase 2

1. Add explicit `COMMUNITY_BLOG_ENABLED=false` to API and active Website.
2. Generate/configure one strong service token on both services and verify
   equality by fingerprint only.
3. Configure active Website `AMPYAN_API_BASE_URL=https://ampyan-api.onrender.com`.
4. Configure API Cloudinary credentials and reviewed Blog folder.
5. Verify/configure SMTP only if the corresponding production mail flows are
   required; otherwise obtain an explicit product/operations waiver.
6. Redeploy/restart under the Phase 2 change window, because Render environment
   changes do not prove runtime use until a new deploy starts.
7. Re-run this read-only report after remediation and keep both flags false.

Production configuration audit: **FAIL**
