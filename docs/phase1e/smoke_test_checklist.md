# Production smoke-test checklist

Use synthetic internal accounts and reversible data only. Do not expose the
Blog publicly during Phase 1E.

## Core Website/API

- [ ] Website `/health` and homepage return expected status and headers.
- [ ] API health endpoint succeeds; remote config contains no secret.
- [ ] News listing/detail and Community listing/detail load.
- [ ] Login succeeds; invalid login fails safely; logout is POST/CSRF protected.
- [ ] Register validation works without creating an unwanted real account.
- [ ] Garage listing/detail and authorized dashboard load.
- [ ] AI Diagnosis returns a controlled response with no server error.
- [ ] Navigation contains no Blog link while the flag is false.

## Existing editors

- [ ] News editor loads for an authorized internal admin.
- [ ] News draft/preview path works without changing an existing article.
- [ ] Existing media URLs render; no unintended Cloudinary write occurs.

## Blog-disabled checks before launch

- [ ] Website Blog routes are absent/controlled while flag is false.
- [ ] API Blog routes fail closed while flag is false.
- [ ] Service token is absent from HTML, logs, cookies, storage, and browser traffic.

## Internal Blog checks after separate internal-only authorization

- [ ] Blog listing, detail, My Blogs, editor, preview, and analytics load.
- [ ] Create/edit/submit a disposable draft; verify optimistic version handling.
- [ ] Moderator queue and approve/reject action work with an internal fixture.
- [ ] Comment, reply, edit, soft-delete, report, like, bookmark, and follow work.
- [ ] PNG/JPEG/WebP upload succeeds to the intended Blog folder.
- [ ] Invalid, corrupt, mismatched, empty, and oversized media fail safely.
- [ ] SEO canonical/robots metadata matches public/private state.
- [ ] No horizontal overflow at 360, 390, 768, 1024, and 1440 widths.
- [ ] Representative navigation is keyboard accessible.
- [ ] Response time/resource counts remain within the Phase 1D local baseline
  and the production thresholds approved by operations.

## Pass criteria

No unexpected 4xx/5xx, CSRF failure, secret exposure, production-data mutation,
external-host mistake, console/page error, or unsafe upload. Delete only the
explicitly identified synthetic test content after acceptance.
