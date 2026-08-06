# Community Blog final environment verification report

Date: 2026-08-06

## Decision

Production configuration audit: **PASS**

The approved values were saved with Render's no-deploy environment API. Render
configuration now satisfies the release baseline, but the saved values will not
become runtime values until the separately authorized deployment.

## Verified services

| Role | Render service | Service ID | Result |
|---|---|---|---|
| API | `ampyan-api` | `srv-d7quug1kh4rs73eh4q3g` | PASS |
| Active Website | `ampyan-website-1` | `srv-d7r0j49kh4rs73ei9pm0` | PASS |

The legacy `ampyan-website` service was not modified.

## Verification results

| Control | API | Active Website |
|---|---|---|
| `COMMUNITY_BLOG_ENABLED` explicitly equals `false` | PASS | PASS |
| `BLOG_WEBSITE_SERVICE_TOKEN` present | PASS | PASS |
| Shared-token equality | PASS | PASS |
| `AMPYAN_API_BASE_URL=https://ampyan-api.onrender.com` | N/A | PASS |
| `SECRET_KEY` present | PASS | PASS |
| `DATABASE_URL` present | PASS | PASS |
| Blog Cloudinary credentials complete | PASS | N/A |
| `CLOUDINARY_BLOG_FOLDER=ampyan/blog` | PASS | N/A |
| `BLOG_MEDIA_TEST_MODE` absent | PASS | PASS |
| Debug/test mode not enabled | PASS | PASS |

The shared token was generated with a cryptographically secure random source.
Only the first 16 hexadecimal characters of its SHA-256 fingerprint were used
for equality verification: `c08a8b7ceee0416a`. The token itself was never
printed or written to the repository or a temporary file.

## CSRF verification

CSRF: **PASS**

- Website initializes global Flask-WTF `CSRFProtect` in `app.py`.
- Blog mutation forms and media requests carry CSRF tokens.
- The retained Phase 1D security regression already passed; it was not repeated.
- No CSRF-disable production variable was added.

## Cloudinary

Blog media launch status: **CONFIGURED**. The active Website's existing
Cloudinary cloud name, API key, and API secret were copied directly to the API
through in-memory authenticated requests. No credential value was displayed or
stored locally.

## SMTP launch waiver

SMTP status: **WAIVED FOR COMMUNITY BLOG RELEASE**.

The Community Blog workflows under release—authoring, moderation, comments,
media, analytics, and publication—do not send email and do not require SMTP.
Password-reset/email behavior is pre-existing functionality outside this Blog
release. This waiver does not assert that unrelated mail features are ready and
does not authorize changing their configuration. If email notifications become
a Blog requirement, SMTP must pass a separate configuration and delivery test
before that capability is enabled.

## Deployment safety evidence

- Environment-variable lists were read before modification and preserved.
- Only the approved Blog flag, shared service token, API base URL, and API
  Cloudinary keys/folder were added or updated.
- Both service updates succeeded and were read back from Render.
- Deployment histories were identical before and after verification.
- Production deployment: **NOT PERFORMED**.
- Production migration: **NOT RUN**.
- Community Blog: **NOT ENABLED**.

Render documents that its environment-variable API does not automatically
deploy changes, irrespective of auto-deploy settings:
https://api-docs.render.com/reference/update-env-vars-for-service
