# Rule reference

What each `analyze.mjs` signal means, when it is a real problem, and the usual fix. "Default impact" is a starting point; adjust after checking data size and call frequency.

## Per-file rules (`files[].findings[].rule`)

| Rule                          | Meaning                                                                       | Real problem when                                                                                          | Usual fix                                                         | Default impact                                  |
| ----------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| `vfor-missing-key`            | `v-for` with no `:key`                                                        | Always (state/DOM reuse bugs, worse diffing)                                                               | Key by stable id                                                  | High                                            |
| `vfor-index-key`              | `:key` is the loop index                                                      | List can be sorted, filtered, inserted into, or rows hold state (inputs, transitions)                      | Key by `sku`/`id`/`month`                                         | Medium; Low if list is static                   |
| `vfor-with-vif`               | `v-for` and `v-if` on the same element                                        | Always - in Vue 3 `v-if` runs first and can't see the loop variable, so this is often a bug, not just perf | Filter in a `computed`, or move `v-if` to a wrapping `<template>` | High (correctness)                              |
| `vfor-calls-function`         | Iterable is a function call, e.g. `v-for="x in getRows()"`                    | Function does filter/sort/map; it reruns on every render of the component                                  | Turn into a `computed`                                            | Medium if non-trivial, else Low                 |
| `array-op-in-template`        | `.filter/.map/.sort/...` inside `{{ }}`                                       | List is non-trivial or component re-renders often                                                          | Move into a `computed`                                            | Medium                                          |
| `inline-handler-in-loop`      | Arrow/function literal in `@event` inside `v-for`                             | Rarely - Vue caches handlers on elements. Matters only when passed to a child component as a prop/listener | Usually dismiss                                                   | Low                                             |
| `object-literal-prop-in-loop` | `{...}`/`[...]` literal bound as a prop on a child _component_ inside `v-for` | Child is non-trivial; new object each render forces child re-render                                        | Hoist to a `computed` map or pass primitives                      | Low-Medium                                      |
| `deep-ref-array`              | `ref([])` / `reactive([])`                                                    | Array holds hundreds+ of objects that are replaced wholesale (fetch results), never mutated in place       | `shallowRef([])` - assigning `.value` still triggers              | Low for small demo data; Medium for large lists |
| `deep-watch`                  | `watch(..., { deep: true })`                                                  | Watched object is large                                                                                    | Watch specific getters                                            | Medium                                          |
| `json-deep-clone`             | `JSON.parse(JSON.stringify(x))`                                               | Large objects or hot paths; also drops Dates/undefined                                                     | `structuredClone` or avoid cloning                                | Low-Medium                                      |
| `interval-not-cleared`        | `setInterval` without `clearInterval` in the same file                        | Always - leaks after unmount                                                                               | Clear in `onUnmounted`                                            | High                                            |
| `listener-not-removed`        | `addEventListener` without `removeEventListener`                              | Target is `window`/`document`                                                                              | Remove in `onUnmounted`                                           | High                                            |
| `loading-error-fetch-pattern` | File has `loading` + `error` refs and `api.*` calls                           | Pattern repeats in 3+ files                                                                                | Shared composable (see below)                                     | Medium (reuse)                                  |

## Cross-file signals (`crossFile`)

- **`duplicateFunctionBodies`** - byte-identical after normalization. Highest-confidence reuse candidate. Move to `client/src/utils/` (pure helpers) or a composable (if it touches refs/i18n).
- **`sameNameFunctions`** - same name in multiple files. Diff them before recommending. Three outcomes: identical (merge), trivially different (merge with a parameter), meaningfully different (rename one; or flag inconsistency as a UX bug).
- **`duplicateTemplateSubtrees`** - same element structure (text and attribute values masked). Within one file it often means two near-identical table rows or cards; across files it suggests a shared presentational component. Check that the bound data shapes are compatible before recommending.
- **`sharedCssSelectors`** - same selector in several SFCs. `identicalDeclarations: true` means copy-paste; move to global styles in `App.vue` or a shared base component. `false` means the same class name is styled differently - either intentional per-component variants, or drift.

## Patterns that come up here

**Modal shell.** If many `*Modal.vue` files repeat `.modal-overlay/.modal-container/.modal-header/.close-button` markup and CSS, recommend a `BaseModal.vue` with `title` prop, `default` + `footer` slots, `v-model:open` or `isOpen` + `close` emit, owning `<Teleport>`/`<Transition>` and Escape-to-close.

**Fetch composable.** For repeated loading/error/try/catch around `api.*`:

```js
// composables/useAsyncData.js
export function useAsyncData(
  fetcher,
  { watchSources = [], immediate = true } = {},
) {
  const data = shallowRef(null);
  const loading = ref(false);
  const error = ref(null);
  const run = async () => {
    loading.value = true;
    error.value = null;
    try {
      data.value = await fetcher();
    } catch (e) {
      error.value = e.message || String(e);
    } finally {
      loading.value = false;
    }
  };
  if (watchSources.length) watch(watchSources, run);
  if (immediate) onMounted(run);
  return { data, loading, error, reload: run };
}
```

**Formatting helpers.** `formatDate`, `formatMoney`, `translateCategory` etc. belong next to `utils/currency.js` (or in `useI18n` if they depend on locale).

**Oversized components.** For files >500 lines, look for seams: independent cards/sections with their own computed data, repeated table blocks, or chart SVG code. Propose specific child components with their props, not just "split this up".
