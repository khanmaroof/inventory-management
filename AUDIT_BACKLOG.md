# Audit Backlog

Audit date: 2026-11-03. Three-angle review (security, performance, UX) with a cross-challenge round on severities.
Basis: code reading plus curl against the running API. No builds, benchmarks, `npm audit` or `pip-audit` were run. Status: not started.

## P1

| ID | Severity | Finding | Location | Fix |
|----|----------|---------|----------|-----|
| UX-1 | High | Modals lack dialog semantics, Escape, focus move/trap; overlay mouse-up discards form | `components/PurchaseOrderModal.vue:2-24` + 6 other modals | `role="dialog"`, `aria-modal`, shared `useModal` composable, labelled close button, `@mousedown.self` |
| UX-2 | High | Clickable rows and chart bars are mouse-only | `Inventory.vue:73-76`, `Dashboard.vue:381-415,464`, `Spending.vue:143,241` | Real `<button>` in first cell, or `tabindex`/`role`/Enter/Space + `aria-label` |
| PERF-5 | Medium | No request cancellation; stale response can overwrite newer one (wrong numbers under active filter) | `Dashboard.vue:950-957`, `Orders.vue:276-318`, `Inventory.vue:205` | `AbortController` or request token in `loadData` |
| UX-3 | Medium-High | Profile menu closes on blur after 200 ms; keyboard users can't reach items | `components/ProfileMenu.vue:3,120-125` | Close on outside click/Escape; `aria-expanded`, `role="menu"`; check `LanguageSwitcher.vue` |

## P2 (Medium)

| ID | Finding | Location | Fix |
|----|---------|----------|-----|
| UX-4 | Loading/error states replace whole page; raw `err.message`, no retry, untranslated, no `role="alert"` | `Dashboard.vue:7-8`, `Inventory.vue:198,339-346`, `Reports.vue:8,210`, `Backlog.vue:8,156`, `Demand.vue:210` | Shared state component with retry; keep page chrome |
| UX-5 | Task add/delete/toggle failures only reach `console.error` | `App.vue:135-191` | Toast/inline error; roll back optimistic update |
| UX-6 | Filter labels not tied to selects; reset button has no `aria-label`; faint disabled state | `components/FilterBar.vue:6,25,37,55,70` | `for`/`id` pairs, translated `aria-label` |
| UX-7 | PO modal validation gaps (no `aria-invalid`/`describedby`, unexplained disabled submit, no date `:min`, hardcoded USD/en-US) | `PurchaseOrderModal.vue:136-240` | Tie errors to inputs, explain disabled state |
| UX-8 | Wide tables lack overflow handling on narrow screens; no captions/`th scope` | Inventory, Backlog, Orders | `overflow-x` wrappers, captions, `scope` |
| SEC-3 | Unbounded strings/lists; every POST grows in-memory lists (UX/perf rate Medium, security Low for demo) | `server/main.py:137-161` | `max_length` on fields and lists; `maxlength` + counter in modals |
| PERF-1 | Dashboard and Spending download all 250 orders (110KB) to aggregate client-side | `Dashboard.vue:828-834`, `Spending.vue:489-502`, `main.py:203-213` | Server-side aggregates or pagination/`fields`, or shared cache |
| SEC-1 | No authn/authz on any endpoint (High before any shared deploy, Medium for demo); mock `useAuth` implies a real session | `main.py:233,295,331,348,358` | `Depends` check on non-GET routes; label "demo user" in profile menu |

## P3 (Low)

- PERF-2: add `GZipMiddleware` (`main.py`). BREACH not a concern, no secrets in bodies.
- SEC-2: binds `0.0.0.0` (`main.py:494`); use `127.0.0.1` or env var.
- SEC-4: CORS `*` with `allow_credentials=True` (`main.py:69-70`); explicit origin list, drop credentials. Latent until cookies exist.
- SEC-5: `1e400` accepted as `inf` budget. Verified: POST returns 201 and GET returns 200 with `"budget": null`, not a 500 as first reported. Fix: `allow_inf_nan=False` on float fields (`main.py:139,160`).
- SEC-6: `/docs` and `/openapi.json` on by default; disable outside development.
- SEC-7: unpinned deps, no server lockfile. Commit `uv.lock` only. Do NOT commit `client/package-lock.json` (gitignored on purpose, see CLAUDE.md).
- SEC-8: hardcoded `http://localhost:8001/api` (`client/src/api.js:3`); read from env var.
- SEC-9 (Info): synthetic email/phone in `useAuth.js:7-8`.
- PERF-3: all routes eagerly imported, single 277KB bundle (`main.js:4-10`); lazy-load routes. Plain "Loading..." matters more than size.
- PERF-4: Demand view re-filters in template (`Demand.vue:20-96,221`); one `computed`.
- PERF-6: empty watcher (`Spending.vue:519-521`); delete.
- PERF-7: index `v-for` keys (`Reports.vue:28,54,88`); key on `quarter`/`month`.
- PERF-8: oversized components (`Dashboard.vue` 1580 lines, `Spending.vue` 1053, `PurchaseOrderModal.vue` 697); split.
- PERF-9: backend recomputes per request (details not captured beyond this line).
- UX-9: mixed breakpoints (768/767/900/480).
- UX-10: overlay sidebar has no focus move or `inert`; `aria-expanded` wrong on mobile.
- UX-11: Unicode glyph icons instead of SVG; hardcoded English in `Backlog.vue` and `Reports.vue`.
