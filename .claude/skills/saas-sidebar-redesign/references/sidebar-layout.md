# Sidebar Shell Layout

## Contents

1. Shell structure
2. `AppSidebar.vue` pattern
3. Shell CSS
4. Responsive behavior
5. Accessibility checklist
6. Common pitfalls

## 1. Shell structure

```
+-----------+--------------------------------------+
| Brand     | Top bar: [menu btn*] title  [lang][profile] |
|-----------+--------------------------------------|
| Nav       | Global filter bar (if any)           |
|  item     |--------------------------------------|
|  item     |                                      |
|  item     |   <router-view />                    |
|           |                                      |
|-----------|                                      |
| Footer    |                                      |
| (profile/ |                                      |
|  collapse)|                                      |
+-----------+--------------------------------------+
* menu button only visible below the drawer breakpoint
```

`App.vue` template (adapt names to the project; keep every existing modal, prop and emit):

```vue
<template>
  <div
    class="app-shell"
    :class="{ 'is-collapsed': collapsed, 'is-drawer-open': drawerOpen }"
  >
    <AppSidebar
      :collapsed="collapsed"
      :drawer-open="drawerOpen"
      @toggle-collapse="toggleCollapse"
      @close-drawer="drawerOpen = false"
    />
    <div
      v-if="drawerOpen"
      class="sidebar-overlay"
      @click="drawerOpen = false"
    />

    <div class="app-main">
      <header class="topbar">
        <button
          class="topbar-menu"
          :aria-label="t('nav.openMenu')"
          @click="drawerOpen = true"
        >
          <!-- inline hamburger svg -->
        </button>
        <div class="topbar-spacer" />
        <LanguageSwitcher />
        <ProfileMenu @show-profile-details="..." @show-tasks="..." />
      </header>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- existing modals unchanged -->
  </div>
</template>
```

Close the drawer on route change (`watch(() => route.fullPath, () => drawerOpen.value = false)`) so tapping a nav item on mobile doesn't leave the drawer covering the page.

## 2. `AppSidebar.vue` pattern

Drive nav from data so adding a page is one line and every item renders identically.

```vue
<template>
  <aside
    class="sidebar"
    :class="{ collapsed, open: drawerOpen }"
    :aria-label="t('nav.primary')"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{
        t("nav.companyName").charAt(0)
      }}</span>
      <span v-if="!collapsed" class="brand-text">
        <span class="brand-name">{{ t("nav.companyName") }}</span>
        <span class="brand-sub">{{ t("nav.subtitle") }}</span>
      </span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :active-class="item.exact ? '' : 'is-active'"
        :exact-active-class="item.exact ? 'is-active' : ''"
        :title="collapsed ? t(item.label) : undefined"
      >
        <svg
          class="nav-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          v-html="item.icon"
        />
        <span v-if="!collapsed" class="nav-label">{{ t(item.label) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button
        class="nav-item"
        @click="$emit('toggle-collapse')"
        :aria-expanded="!collapsed"
      >
        <!-- chevron icon -->
        <span v-if="!collapsed" class="nav-label">{{ t("nav.collapse") }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
// The root route needs exact matching, otherwise "/" is "active" on every page.
const navItems = [
  { to: "/", label: "nav.overview", exact: true, icon: ICONS.home },
  { to: "/inventory", label: "nav.inventory", icon: ICONS.box },
  // ...
];
</script>
```

Notes:

- `router-link` sets `aria-current="page"` on the exact-active link automatically - don't override it.
- Icons: 24x24 viewBox, `fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"`, Feather/Lucide-style paths written inline. Keep the path data in a small `icons.js` map rather than repeating SVG in templates. `v-html` is fine here only because the strings are static and authored in the repo - never feed it user data.
- If the project mixes Options API and `<script setup>`, match whichever the surrounding components use.
- Group items under small section labels ("Operations", "Finance") only if there are more than ~7 items.

## 3. Shell CSS

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--color-bg);
  transition: grid-template-columns var(--duration-base) var(--ease-out);
}
.app-shell.is-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  overflow-y: auto;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
}
.brand-mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--gray-900);
  color: #fff;
  font-weight: var(--weight-bold);
  font-size: var(--text-base);
}
.brand-name {
  display: block;
  font-weight: var(--weight-semibold);
  font-size: var(--text-base);
  color: var(--color-text);
}
.brand-sub {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
}
.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 36px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  text-decoration: none;
  white-space: nowrap;
  background: none;
  border: 0;
  width: 100%;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out);
}
.nav-item:hover {
  background: var(--gray-100);
  color: var(--color-text);
}
.nav-item.is-active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}
.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}
.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.app-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--page-gutter);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--color-border);
}
.topbar-spacer {
  flex: 1;
}
.topbar-menu {
  display: none;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  padding: var(--space-6) var(--page-gutter) var(--space-10);
}
```

`minmax(0, 1fr)` and `min-width: 0` matter: without them a wide table inside the content column forces the whole grid wider than the viewport instead of scrolling inside `.table-container`.

## 4. Responsive behavior

| Width       | Behavior                                                                       |
| ----------- | ------------------------------------------------------------------------------ |
| >= 1280px   | Full sidebar (default), collapse toggle available                              |
| 1024-1279px | Start collapsed if no stored preference                                        |
| < 1024px    | Sidebar leaves the grid and becomes an off-canvas drawer; hamburger in top bar |

```css
@media (max-width: 1023px) {
  .app-shell,
  .app-shell.is-collapsed {
    grid-template-columns: minmax(0, 1fr);
  }
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--duration-base) var(--ease-out);
    box-shadow: var(--shadow-lg);
    z-index: var(--z-overlay);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  /* In drawer mode always show labels, regardless of desktop collapse state */
  .sidebar.collapsed .nav-label,
  .sidebar.collapsed .brand-text {
    display: inline;
  }
  .sidebar-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: calc(var(--z-overlay) - 1);
  }
  .topbar-menu {
    display: inline-grid;
    place-items: center;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
  }
}
```

If labels are hidden with `v-if="!collapsed"`, the drawer-mode CSS above can't show them - use a `isDrawerMode` computed (from `matchMedia('(max-width: 1023px)')`) to force labels on, or hide labels with CSS instead of `v-if`.

Persist collapse:

```js
const STORAGE_KEY = "sidebar-collapsed";
const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
};
const collapsed = ref(readCollapsed());
const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
  try {
    localStorage.setItem(STORAGE_KEY, collapsed.value ? "1" : "0");
  } catch {}
};
```

## 5. Accessibility checklist

- `<aside aria-label>` wraps a `<nav>`; the active link has `aria-current="page"` (router-link does this).
- Collapse toggle has `aria-expanded`; hamburger has an `aria-label`.
- Collapsed rail: every icon-only link has a `title` or visually-hidden label so it still has an accessible name.
- Drawer: Escape closes it; focus moves into the drawer on open and back to the hamburger on close.
- Visible `:focus-visible` ring on nav items and buttons; don't remove outlines without a replacement.
- Text contrast >= 4.5:1 - `--gray-500` on white passes for 14px; don't go lighter for nav labels.

## 6. Common pitfalls

- **"/" always active** - the root link needs exact matching.
- **Old header CSS left behind** - delete `.top-nav`, `.nav-tabs` etc. once replaced, or they'll fight the new layout.
- **Sticky filter bar offset** - if the filter bar was `position: sticky; top: 70px` for the old header, update it to `var(--topbar-height)`.
- **Dropdowns clipped** - profile/language dropdowns in the sidebar footer need to open upward or be positioned outside the sidebar's `overflow` context.
- **Modals under the sidebar** - modals need `z-index: var(--z-modal)` above `--z-sidebar` and `--z-overlay`.
- **Content centered off-axis** - an old `margin: 0 auto` on `.main-content` centers it in the content column, which can look misaligned next to the sidebar. Left-align by default.
