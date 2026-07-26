# Community Blog Phase 1C handoff

## Scope and safety

Phase 1C is a local Website integration only. No production migration, deploy,
flag activation, service-token configuration, Cloudinary call, API source
change, Flutter change, commit, or push was performed. Existing dirty work was
preserved. `COMMUNITY_BLOG_ENABLED` defaults to `false`; blank and unknown
values are disabled, and only `true`, `1`, `yes`, and `on` enable Website
routes/navigation. Disabled requests return 404 before constructing an API
client.

## Architecture and authentication

The flow is Browser → Flask Website → `services/blog_api_client.py` → API v1.
Website Blog routes never import Blog database models or query Blog tables.
Anonymous reads omit service identity headers. Authenticated requests derive
the user ID only from Flask-Login and send it with the server-only
`BLOG_WEBSITE_SERVICE_TOKEN`; browser `user_id` and `role` values are ignored.
The client preserves API error codes, uses 5/15-second normal and 5/30-second
media timeouts, validates response envelopes, and never retries mutations.

## Routes and UI

`routes/blog_routes.py` provides listing/detail, author draft CRUD and workflow,
dashboard/analytics, likes/bookmarks/follows, comments, reports, media, views,
and moderation under `/blogs`. All mutations are POST routes protected by the
existing global CSRF layer and login where required. Same-origin return
redirects are validated to prevent open redirects.

Templates in `templates/blogs/` provide listing, detail, defensive content
blocks, editor, My Blogs, analytics, moderation, empty/unavailable states, SEO
metadata, share controls, and status text. The block renderer escapes user text,
never renders raw HTML/iframe input, accepts only absolute HTTPS media/links,
and wraps wide tables and galleries responsively. Isolated CSS and JavaScript
live in `static/css/blogs.css` and `static/js/blogs.js`.

The editor maintains canonical `{id,type,order,data}` blocks, supports all
declared block types, add/remove/reorder/edit/preview, unsaved-change warning,
busy buttons, and image upload through the same-origin Website endpoint.
Draft creation uses a session-owned idempotency key and retains it after failed
or timed-out attempts. Successful creation clears it. Updates forward API
versions and preserve submitted form content on `BLOG_EDIT_CONFLICT`.

View recording reuses a session identifier and failure does not block detail
rendering. Comment submission uses Post/Redirect/Get and immediate busy-button
protection; the API still has no persisted comment idempotency key, so comments
are intentionally never auto-retried.

## Validation evidence (2026-07-26)

- Website focused Blog/API-client/CSRF: 25 passed, 168 subtests passed.
- Full Website suite: 44 passed, 174 subtests passed.
- Focused API Blog contracts using disposable `/tmp` SQLite: 23 passed.
- Python compilation: passed.
- All 70 Jinja templates compiled.
- JavaScript parser check: not run because Node is not installed.
- Browser automation/responsive screenshots: not available; CSS inspection is
  complete but viewport validation remains PARTIAL.
- No real API, production database, or Cloudinary call was made.

The first API test attempt was unable to create tables in the read-only API
repository. The identical focused suite was rerun successfully with
`DATABASE_URL=sqlite:////tmp/ampyan_phase1c_api.sqlite`; this was disposable and
did not run migrations.

## Remaining production blockers and rollback

Keep both Website and API feature flags false. Before Phase 1D, perform real
browser viewport/keyboard testing at 360, 390, 768, 1024, and 1440 px against a
disposable API, complete operational token provisioning, validate caching and
rate limits, and obtain deployment approval. Rollback is configuration-only:
leave or set `COMMUNITY_BLOG_ENABLED=false`; routes then stop before all Blog API
traffic and navigation disappears.

Phase 1D browser findings and current rollout status are recorded in
`docs/community_blog_phase1d_handoff.md`.
