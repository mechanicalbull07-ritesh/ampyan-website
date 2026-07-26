# Community Blog Phase 1D local performance baseline

This is a local browser regression and resource baseline, not a production load test.

| Scenario | Runs | Min ms | Max ms | Mean ms | Median ms | Std dev | p95 | Variation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Blog listing | 5 | 118.15 | 144.78 | 127.35 | 125.85 | 9.17 | 144.78 | 20.91% |
| Paginated listing | 5 | 113.29 | 129.82 | 120.22 | 117.24 | 5.93 | 129.82 | 13.75% |
| Published detail | 5 | 128.93 | 143.83 | 135.94 | 134.80 | 5.95 | 143.83 | 10.96% |
| Long rich article | 5 | 121.22 | 137.90 | 127.26 | 125.15 | 5.70 | 137.90 | 13.11% |
| Article with comments | 5 | 122.15 | 135.80 | 130.86 | 133.26 | 5.31 | 135.80 | 10.43% |
| Empty editor | 5 | 114.33 | 120.74 | 118.23 | 118.04 | 2.37 | 120.74 | 5.42% |
| Populated editor | 5 | 143.77 | 160.09 | 152.61 | 154.14 | 5.36 | 160.09 | 10.69% |
| My Blogs | 5 | 141.91 | 150.81 | 147.29 | 149.03 | 3.24 | 150.81 | 6.04% |
| Analytics | 5 | 115.12 | 125.27 | 121.29 | 121.67 | 3.66 | 125.27 | 8.37% |
| Save draft | 5 | 386.42 | 415.57 | 406.88 | 411.04 | 10.74 | 415.57 | 7.16% |
| Update draft | 5 | 401.80 | 420.21 | 409.43 | 407.75 | 6.79 | 420.21 | 4.50% |
| Submit for review | 5 | 1640.75 | 1753.32 | 1679.96 | 1655.73 | 41.40 | 1753.32 | 6.70% |
| Moderation queue | 5 | 153.46 | 166.96 | 160.04 | 160.29 | 4.88 | 166.96 | 8.44% |
| Moderation action | 5 | 217.49 | 367.43 | 254.37 | 225.04 | 57.21 | 367.43 | 58.95% |
| Fake-media upload | 5 | 247.31 | 595.24 | 322.80 | 255.51 | 136.41 | 595.24 | 107.79% |

- Measured runs: **75**
- Resource cycles: **20**
- Failed requests: **51**
- Console errors: **0**
- Page errors: **0**

## Resource and failure classification

- Resource cycles: **20 total** — reader 6, author/editor 5, moderator 5,
  deterministic fake-media 4.
- The 51 failed browser resources were exclusively external presentation
  fonts: `fonts.gstatic.com` 20, Font Awesome brand font 16, and Font Awesome
  solid font 15. There were zero failed Website/API documents or mutations.
- JavaScript heap after forced collection stabilized in every flow. DOM node,
  JavaScript event-listener, request-resource, object-URL, and PostgreSQL
  connection counts were flat within each flow.
- Browser RSS fluctuated but did not continuously rise in any flow. Website
  and API RSS remained bounded; PostgreSQL connections remained exactly 2
  throughout all 20 cycles.
- Console errors: **0**. Page errors: **0**. Duplicate mutations: **0**.
  No object-URL or PostgreSQL connection leak was observed.
- `main_api_duration_ms` is `null` in all browser records because the Website
  performs Blog API calls server-to-server and does not expose that internal
  timing to the browser. No timing value was invented. Main-document,
  mutation, navigation, resource, transfer, heap, RSS, DOM, listener, and
  connection measurements are retained for every applicable run.

Conclusion: **PASSED as a local browser regression and resource baseline**.
This is not a production load test and establishes no production SLA.
