---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern, professional SaaS-style interface - replaces a top navigation bar with a vertical left sidebar, introduces a consistent spacing/typography/color token system, and polishes every view to match. Use this skill whenever the user asks to modernize, restyle, refresh, or "make it look like a SaaS app", wants a sidebar or side nav instead of a top nav, complains that spacing is inconsistent or the UI looks dated/amateur, or asks for a dashboard-style app shell in a Vue project - even if they do not say "redesign" explicitly.
---

# SaaS Sidebar Redesign (Vue 3)

Turn a Vue 3 app with a top nav into a polished SaaS shell: fixed left sidebar, slim top bar, a content area with a consistent rhythm, and views that share one visual language.

The goal is a _coherent system_, not a pile of nicer-looking rules. Most "unprofessional" UIs come from three things: ad-hoc spacing values, too many competing colors/weights, and a navigation model that doesn't scale. Fix those at the root (tokens + shell) and the views mostly fall into place.

## Ground rules

- **Behavior is frozen.** This is a visual redesign. Do not change routes, API calls, props/emits, store logic, i18n keys, or data flow. If a template must be restructured, keep every binding, `v-if`, `v-for` `:key`, and event handler intact.
- **Follow the project's own rules first.** Read the project `CLAUDE.md` before editing. If it mandates a subagent for `.vue` changes (e.g. `vue-expert`), delegate those edits to it and give it the relevant reference file(s) from this skill. If it defines design constraints (palette, "no emojis", chart style), those override the defaults here.
- **No new dependencies without asking.** Use inline SVG icons and plain CSS. Don't pull in Tailwind, an icon pack, or a UI kit unless the user agrees.
- **Keep i18n working.** Nav labels must keep using the existing translation function (`t('nav.x')`). Any new visible string gets a key in every locale file, not a hard-coded literal.

## Workflow

### 1. Audit (read-only)

Before touching anything, build a picture of the current UI:

- Find the app shell (usually `App.vue`) and how nav is rendered: `router-link`s, active-state logic, and what else lives in the header (logo, language switcher, profile menu, global filters).
- List views and shared components. Note where global styles live (often an unscoped `<style>` in `App.vue`) vs scoped per-view styles.
- Run the spacing audit to see how fragmented the current values are:
  ```bash
  python3 <skill-dir>/scripts/audit_spacing.py <client-src-dir>
  ```
  It reports every distinct `padding`/`margin`/`gap` value with counts and flags values that aren't on the 4px scale. Use it as the before-baseline; you'll rerun it at the end.

Summarize findings to the user in a few lines (nav items, header extras, # of off-scale values) and state the plan before editing. If the app has an unusual shape (no router, many nested routes, an existing sidebar), say how you'll adapt.

### 2. Introduce design tokens

Add CSS custom properties on `:root` in the global stylesheet. Read `references/design-tokens.md` for the full token set and the reasoning behind each scale. In short:

- **Spacing**: a 4px-based scale (`--space-1` = 4px ... `--space-12` = 48px). Every padding/margin/gap should resolve to a token.
- **Type**: a short ramp (12/13/14/16/20/24/30) with two or three weights.
- **Color**: neutrals (slate), one brand/accent, and semantic status colors. Keep the project's existing palette if it has one - map it onto tokens rather than replacing it.
- **Radius, shadow, layout**: `--radius-sm/md/lg`, two or three elevation shadows, `--sidebar-width`, `--topbar-height`.

Then rewrite the existing global utility classes (`.card`, `.stat-card`, `.badge`, tables, `.page-header`, etc.) to consume tokens. Keep the class names - views depend on them.

### 3. Build the shell

Read `references/sidebar-layout.md` - it contains a drop-in `AppSidebar.vue` pattern, the shell layout CSS, and the responsive/accessibility requirements.

- Extract nav into a `components/AppSidebar.vue` driven by a `navItems` array (route, i18n key, icon). Active state comes from the router (`router-link`'s `active-class`/`exact-active-class`, or `useRoute()`), not hand-written path comparisons per link.
- Shell layout: CSS Grid with `grid-template-columns: var(--sidebar-width) 1fr`. Sidebar is sticky full-height; content column scrolls.
- Header extras go to sensible new homes: brand/logo to the sidebar top; profile menu to the sidebar footer or the top bar right; language switcher next to it. Global filter bars sit at the top of the content column, below the top bar.
- Support collapse (icon-only rail) on desktop and an off-canvas drawer below ~1024px. Persist the collapsed preference in `localStorage` (wrapped in try/catch).

### 4. Sweep the views

Go view by view (start with the busiest - usually the dashboard - since it exercises the most patterns). For each:

- Replace hard-coded spacing, font sizes, colors, radii and shadows with tokens. A value that has no token is a signal: either it's a one-off that should snap to the nearest token, or the scale is missing a step (rare - push back before adding one).
- Normalize the page header (title + subtitle + optional actions on the right) and the vertical rhythm between sections (`--space-6` between cards/sections is a good default).
- Make cards, tables, badges and buttons look the same everywhere. If two views style tables differently, converge on the global one.
- Remove `max-width` + `margin: 0 auto` centering from the main content if the sidebar now handles framing; use a generous max-width on an inner container only if very wide screens look sparse.
- Check modals and dropdowns (`z-index`, overlay color, radius) so they match the new shell and still layer above the sidebar.

Parallelize across views with subagents if there are many, but give each the token file and the same instructions so they converge.

### 5. Verify

Don't declare success from the diff. Check it:

1. `npm run build` (or the project's build script) passes with no new warnings.
2. Rerun `audit_spacing.py` - off-scale values should be near zero; report before/after counts.
3. Open the app in a browser (Playwright MCP or the built-in browser) and screenshot every route at ~1440px, ~1024px and ~390px wide. Confirm: active nav state is correct on each route, sidebar collapses/expands, mobile drawer opens and closes (Escape and overlay click), no horizontal scroll, modals layer correctly.
4. Switch language if the app has i18n and confirm nav labels translate and don't overflow the sidebar.
5. Keyboard pass: Tab through the sidebar - visible focus ring, logical order, `aria-current="page"` on the active link.

If something can't be verified (no browser available, backend not running), say so plainly.

### 6. Report

Give the user a short summary: files changed, new components, token file location, before/after audit numbers, screenshots (or where to find them), and anything deliberately left alone. Suggest a commit only if they ask - don't commit on your own.

## Style direction

Aim for the restrained look of tools like Linear, Vercel or Stripe Dashboard:

- Light, neutral background for content (`slate-50`), white surfaces, 1px `slate-200` borders. Shadows are subtle and reserved for elevation (dropdowns, modals, hover on interactive cards).
- Sidebar: either white with a right border, or dark (`slate-900`) for stronger contrast - pick one and commit. Nav items are 36-40px tall, 14px medium-weight text with a 16-18px icon, rounded hover background, and a clear but quiet active state (tinted background + accent text, optional 2px left indicator).
- Typography does the hierarchy work: one bold page title, semibold card titles, regular body, muted secondary text. Avoid uppercase except for tiny table headers / labels.
- One accent color. Status colors (green/blue/amber/red) appear only where they carry meaning.
- Motion is short (120-200ms) and only on hover/focus/open-close. Respect `prefers-reduced-motion`.

## Reference files

- `references/design-tokens.md` - full token set with values and usage notes. Read in step 2.
- `references/sidebar-layout.md` - `AppSidebar.vue` pattern, shell CSS, responsive and a11y checklist. Read in step 3.
- `scripts/audit_spacing.py` - spacing audit; run in steps 1 and 5.
