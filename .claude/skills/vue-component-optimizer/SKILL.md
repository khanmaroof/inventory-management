---
name: vue-component-optimizer
description: Analyze Vue 3 single-file components for performance problems and code-reuse opportunities, and produce a ranked, evidence-backed optimization report (no edits). Use this skill whenever the user asks to audit, review, analyze, profile, or "clean up" Vue components or views; asks why a Vue page is slow or re-renders too much; wants to find duplicated logic, templates, or CSS across .vue files; asks what should become a composable or shared component; or mentions a .vue file being too big - even if they don't say "optimize".
---

# Vue Component Optimizer

Produce a report that tells the user **which changes are worth making, in what order, and why** - grounded in measured facts from their code, not a generic Vue checklist. The report is read-only: this project's CLAUDE.md requires that significant `.vue` edits go through the `vue-expert` subagent, so the report ends with a hand-off rather than applying fixes.

## Workflow

### 1. Scope

Default scope is `client/src` (views + components). If the user names files or a folder, analyze just those - but still run the script over all of `client/src` when the question is about reuse, because duplication is only visible across files.

### 2. Collect facts with the bundled script

```bash
node .claude/skills/vue-component-optimizer/scripts/analyze.mjs --root client [paths...] > <scratchpad>/vue-analysis.json
```

`--root` must point at the directory whose `node_modules` contains `@vue/compiler-sfc` (here: `client`). It parses every SFC with Vue's own compiler and emits JSON:

- `files[]`: line counts per block, `scriptStyle` (`script-setup` vs `setup()`), reactivity counts (ref/computed/watch/api calls), template stats, and per-file `findings[]` with `rule`, `line`, `detail`.
- `crossFile`: `duplicateFunctionBodies` (identical after whitespace/comment normalization), `sameNameFunctions` (same name, maybe diverged), `duplicateTemplateSubtrees`, `sharedCssSelectors` (with `identicalDeclarations`).
- `summary`: largest files and finding counts by rule.

Write the JSON to a scratch file and query it with `node -e` rather than dumping it into context - it is large.

The script reports _facts_, and some are deliberately over-inclusive. Your job is to verify and judge them. See `references/rules.md` for what each rule means, when it actually matters, and the typical fix.

### 3. Verify before reporting

For every finding you plan to include, open the cited lines and confirm it. Things the script cannot know:

- **Data size.** `deep-ref-array` only matters if the array is big (hundreds+ rows) or replaced wholesale often. Check what fills it (`server/data/*.json` sizes are a good proxy here).
- **Whether a function in `v-for` or `{{ }}` is cheap.** `formatCurrency(x)` is fine; `items.filter(...).sort(...)` per render is not.
- **Whether same-name functions actually behave the same.** Diff them. Two `formatDate`s with different locales are not duplicates - but they may be a _bug_ (inconsistent formatting across pages), which is worth saying.
- **Whether an existing home already exists.** Check `client/src/composables/`, `client/src/utils/`, and `client/src/App.vue` (global styles) before proposing a new file. Extending `useFilters` or `utils/currency.js` beats creating a sibling.

Drop anything you can't confirm. A short report of real issues is far more useful than a long one with noise - the user will stop trusting it after the first false positive.

### 4. Prioritize

Rank by **impact x confidence / effort**. Rough guide:

- **High**: measurable runtime cost on a real path (O(n) work per render on a large list, deep reactivity on big datasets, leaks), or duplication across 4+ files where copies have already drifted.
- **Medium**: duplication across 2-3 files, oversized components (>500 lines) with clear seams, missing `shallowRef` on medium data.
- **Low**: style consistency (`setup()` vs `<script setup>`), micro-optimizations with no observable effect.

Be honest about magnitude. In a demo app with a few hundred rows, most "performance" issues are low impact; say so, and lean the report toward reuse/maintainability where the real wins are. Don't inflate.

### 5. Write the report

Use this structure:

```markdown
# Vue Component Optimization Report

Scope: <paths> · <N> files · <date>

## Summary

<2-4 sentences: the biggest wins, overall health, honest magnitude.>

## Top recommendations

| #   | Recommendation | Impact | Effort | Files |
| --- | -------------- | ------ | ------ | ----- |

## Findings

### 1. <Title> - <Impact> / <Effort>

**Where:** `path:line`, `path:line`
**What:** <what the code does now, with a short excerpt if helpful>
**Why it matters:** <concrete consequence in this app>
**Suggested fix:** <code sketch: new composable/component signature + one call site>

## Reuse map

<Proposed shared pieces: name, location, which files adopt it, lines saved (approx).>

## Not worth changing

<Things the script flagged that you checked and dismissed, one line each. This shows the user you verified, and saves the next reviewer the trouble.>

## Next step

<One line offering to hand selected items to the vue-expert subagent.>
```

Keep fix sketches short and in the project's existing style (Composition API, `setup()` returning bindings, `api.js` for HTTP, `useX` naming under `composables/`). Respect the design system in CLAUDE.md when suggesting shared CSS (slate palette, no emojis).

If the user asked about a single file, collapse to just Summary + Findings + Next step.

## Project-specific notes

- Views live in `client/src/views/`, components in `client/src/components/`, global styles in `client/src/App.vue`.
- All data fetching goes through `client/src/api.js`; filters come from the singleton `useFilters()` composable. A repeated `loading/error/try/await api.x()/finally` block across views is the classic candidate for a `useAsyncData`-style composable that reads filters.
- Keys in `v-for` must be stable ids (`sku`, `month`, `id`) - this is called out in CLAUDE.md as a known issue.
