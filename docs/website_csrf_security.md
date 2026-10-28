# Website CSRF security foundation

## Scope and status

The Website uses Flask-WTF 1.2.2 `CSRFProtect` globally. Community Blog remains
disabled and no Blog UI, API change, Flutter change, production access,
deployment, migration, commit or push was performed.

## Initialization and secrets

`app.py` creates one `CSRFProtect` extension and initializes it after the Flask
secret key is configured. `SECRET_KEY` is mandatory in production; the existing
`local-dev-secret` fallback is development-only. `.env.example` contains an
empty placeholder and Render keeps the value as an unmanaged secret.

Production cookie policy:

- Session and remember cookies are HTTP-only.
- SameSite is `Lax`.
- Secure cookies are enabled when the Website is running in production.
- Local HTTP development keeps Secure disabled.

CSRF remains required independently of cookie settings.

## HTML, JavaScript, JSON and uploads

All 63 discovered raw HTML POST forms include:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

The base template publishes the session-bound token in a same-origin meta tag.
Same-origin JavaScript mutations read it and send `X-CSRFToken`. The token is
not stored in a URL or localStorage and is never sent to the AMPYAN API domain.
JSON mutations and multipart uploads use the same global validation.

Future Community Blog forms must follow this pattern and call only Website
routes. They must never expose `BLOG_WEBSITE_SERVICE_TOKEN` or trust a browser
user ID or role.

## Error handling

Missing, invalid, expired or cross-session tokens return HTTP 400.
HTML receives a controlled retry page. JSON receives:

```json
{
  "success": false,
  "error": {
    "code": "CSRF_VALIDATION_FAILED",
    "message": "Your session form token is missing or expired. Refresh the page and try again."
  }
}
```

No expected token, received token, session identifier, secret or traceback is
returned.

## Exemptions and state-changing GET routes

There are no `csrf.exempt` routes and no default-check bypass. The final Flask
URL map contains 83 state-changing route/method combinations; global protection
applies to every POST, PUT, PATCH and DELETE route.

Unsafe GET mutations for logout, News deletion, car selection/deletion,
upvoting and admin actions were converted to POST. Email verification now uses
a GET confirmation page followed by a protected POST.

The Google OAuth callback remains GET because it is a protocol callback guarded
by Authlib OAuth state validation, not a browser mutation form or CSRF
exemption. The callback URL cannot be converted independently of the OAuth
protocol.

Route coverage by submission class:

| Routes | Authentication | Submission | CSRF mechanism | Result |
|---|---|---|---|---|
| `/login`, `/register`, password and email flows | Public/session | HTML | Hidden token | Protected |
| `/logout`, profile and vehicle routes | Flask-Login where required | HTML/JSON | Hidden token/header | Protected |
| `/admin/*` mutations | Admin checks | HTML | Hidden token | Protected |
| News create/edit/delete/replies/uploads | Login/admin where required | HTML/multipart/header | Hidden token/header | Protected |
| Community create/edit/delete/replies/upvote | Login where required | HTML/JSON | Hidden token/header | Protected |
| Garage, marketplace and review mutations | Login where required | HTML/JSON | Hidden token/header | Protected |
| Diagnosis, tools, feedback and analytics mutations | Route-specific | HTML/JSON | Hidden token/header | Protected |
| Future `/blogs/*` mutations | Flask-Login plus server API authorization | HTML/header | Hidden token/header | Ready |

## Template syntax repair

Full Jinja compilation exposed one pre-existing error in
`templates/mechanic_dashboard.html:53`. Git history and blame trace it to the
template's original May 2, 2026 commit; CSRF work had not touched the file.

Invalid:

```jinja2
mechanic.reviews|sort(attribute='id', reverse=True)[:5]
```

Corrected without changing behavior:

```jinja2
(mechanic.reviews|sort(attribute='id', reverse=True))[:5]
```

This preserves descending sorting followed by a five-review slice. All 62
templates compile after the correction.

## Testing

Security tests extract real rendered tokens instead of using fixed values.
Coverage includes valid/missing/invalid HTML tokens, JSON headers,
cross-session rejection, login/registration validation, password/profile/News/
Community/upload enforcement, POST-only logout, all-template compilation,
feature-disabled Blog state and actual mechanic-dashboard rendering.

Final focused security/template suite:

- 13 passed
- 0 failed
- 145 subtests passed
- 59 deprecation warnings

Final complete Website suite:

- 32 passed
- 0 failed
- 0 skipped
- 151 subtests passed
- 60 deprecation warnings

Python compilation, all-template compilation, YAML parsing and `git diff
--check` passed. A standalone JavaScript parser was unavailable because Node.js
is not installed; inline mutation sources were inspected and all four POST
fetch paths include `X-CSRFToken`.

Local and production-like boot checks returned HTTP 200 for the homepage,
login, News, Community and health routes. Production-like validation used a
fake secret, proved Secure session/remember cookies, kept Blog links absent and
mocked the Community remote call. A separate negative boot proved production
startup fails closed when `SECRET_KEY` is absent.

Tests use fake local secrets and disposable SQLite only.

## Production checklist

1. Configure a strong `SECRET_KEY` through the production secret manager.
2. Keep `COMMUNITY_BLOG_ENABLED=false` until its separate rollout.
3. Confirm HTTPS so Secure cookies are transmitted.
4. Run the full Website suite after dependency installation.
5. Do not add browser-route CSRF exemptions.
6. Add tokens and security tests with every future mutation form.

## Rollback and limitations

Rollback must be reviewed as a complete security change; removing only form
tokens while leaving global protection enabled would break mutations, while
disabling protection would reopen CSRF exposure.

No automated real-browser screenshot suite exists in this repository. Template,
route and static-source validation cover structure and behavior, but responsive
visual inspection is limited until browser automation or controlled staging is
available.
