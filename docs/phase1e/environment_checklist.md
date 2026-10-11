# Production environment checklist

Never record secret values in this checklist. Record only `present`, `absent`,
or `mismatch`, plus the verifier and timestamp.

## Current audit

- [x] Website blueprint service name: `ampyan-website`.
- [x] API blueprint service name: `ampyan-api`.
- [x] Both blueprints set `COMMUNITY_BLOG_ENABLED=false`.
- [x] Both blueprints declare `BLOG_WEBSITE_SERVICE_TOKEN` as an unmanaged secret.
- [ ] Authenticate Render CLI/dashboard and verify both live services.
- [ ] Confirm live `COMMUNITY_BLOG_ENABLED=false` on Website and API.
- [ ] Confirm the same non-empty service token is configured on both services.
- [ ] Confirm no secret appears in build logs, HTML, browser storage, or client requests.

## Website (`ampyan-website`)

- [ ] `DATABASE_URL`: present and points to the intended Website database.
- [ ] `SECRET_KEY`: present, strong, production-only, and not shared in tickets.
- [ ] `AMPYAN_API_BASE_URL`: HTTPS production API origin, no trailing test host.
- [ ] `COMMUNITY_BLOG_ENABLED`: exactly `false` before and during migration.
- [ ] `BLOG_WEBSITE_SERVICE_TOKEN`: present and matches API value.
- [ ] `ENV`/Render production detection: active; Secure cookies enabled.
- [ ] CSRF: global Flask-WTF protection active; no exemptions added.
- [ ] `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`: present if Website mail is used.
- [ ] Existing News Cloudinary configuration remains present and unchanged.
- [ ] Analytics/site-verification values are present where currently required.

## API (`ampyan-api`)

- [ ] `DATABASE_URL`: present and points to the intended production PostgreSQL database.
- [ ] `SECRET_KEY`: present and production-only.
- [ ] `COMMUNITY_BLOG_ENABLED`: exactly `false` before and during migration.
- [ ] `BLOG_WEBSITE_SERVICE_TOKEN`: present and matches Website value.
- [ ] `CLOUDINARY_URL`, or all of `CLOUDINARY_CLOUD_NAME`,
  `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: present.
- [ ] `CLOUDINARY_BLOG_FOLDER`: reviewed; default is `ampyan/blog`.
- [ ] `BLOG_MEDIA_TEST_MODE`: absent or `false` in production.
- [ ] `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM`:
  present if API password-reset mail is enabled.
- [ ] `AI_REASONING_ENGINE_ENABLED`: remains at its approved unrelated value.

## Verification record

- Render verifier: **TBD**
- Verification timestamp: **TBD**
- Live configuration result: **BLOCKED — unauthenticated Render CLI**
