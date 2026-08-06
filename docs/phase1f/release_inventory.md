# Phase 1F repository audit and release inventory

Audit date: 2026-08-06

No file was moved, deleted, staged, committed, or pushed during this audit.

## Website repository

- Path: `/Users/riteshkumar/carcommunity`
- Branch: `main`
- HEAD: `dcdb1ab8de9c7fd2458ada7b16fdca58938b9549`
- Upstream: `origin/main`

Current dirty files are all Community Blog validation/release material:

- `docs/community_blog_phase1d_handoff.md`
- `tests/e2e/blog/phase1d_payload_matrix.py`
- `docs/evidence/community_blog_phase1d_payload_matrix.json`
- `docs/evidence/community_blog_phase1d_payload_matrix.md`
- `docs/phase1e/`
- `docs/phase1f/`

No Diagnosis, News, Flutter, UI redesign, or unrelated Website source change is
present in the current Website delta.

## API repository

- Path: `/Users/riteshkumar/motronix_api`
- Branch: `main`
- HEAD: `2879ea8e4bc27356f2fab966870b5982e2d2d0c2`
- Upstream: `origin/main`

### Community Blog release files

- `blog/`
- `models/blog_model.py`
- `services/blog_content.py`
- `services/blog_media.py`
- `migrations/20260726_community_blog_up.sql`
- `migrations/20260726_community_blog_down.sql`
- `tests/blog_validation_baseline.sql`
- `tests/test_blog_*.py`
- `docs/community_blog_*.md`
- `.env.example` Blog keys
- `render.yaml` Blog flag and service-token declarations
- `requirements.txt` Pillow dependency
- Blog-specific imports, configuration, blueprint registration, rate-limit/
  security handling, and model registration hunks in `app.py`

### Diagnosis work — exclude from Blog release

- `ai_engine/diagnostic_engine.py`
- `ai_engine/guidance_engine.py`
- `ai_engine/intent_classifier.py`
- `ai_engine/language_utils.py`
- `ai_engine/reasoning_engine.py`
- `services/diagnosis_contract.py`
- `services/diagnosis_quality.py`
- `services/diagnosis_relevance_guard.py`
- `tests/fixtures/diagnosis_parity_cases.json`
- `tests/test_diagnosis_contract.py`
- `tests/test_diagnosis_p1_quality.py`
- `tests/test_query_understanding.py`
- Diagnosis-specific hunks in `app.py`

### News work — exclude from Blog release

- `services/news_content.py`
- `tests/test_content_sync_routes.py`
- `tests/test_news_content_blocks.py`
- `tests/test_news_identity_sequence_unit.py`
- `tests/test_news_postgresql_sequence.py`
- `docs/news_postgresql_identity_sequence_fix.md`
- News-specific hunks in `app.py`

### Do not include without separate review

- `CHATGPT_HANDOFF.md`
- Community serialization changes in `app.py` that are not required by Blog
- Any generated caches, local databases, credentials, or temporary evidence

## Mixed-file control

`app.py` contains Blog, Diagnosis, News, and Community changes. A whole-file
`git add app.py` is prohibited for the Blog release. Use an isolated release
branch/worktree and interactive hunk staging, then review the staged patch and
run the full regression. No history rewrite is required.

Repository audit: **PASS — inventory and separation plan complete; commits are
intentionally deferred.**
