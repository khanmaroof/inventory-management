<template>
  <aside
    class="sidebar"
    :class="{ collapsed, overlay }"
    :aria-label="t('nav.primary')"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{
        t("nav.companyName").charAt(0)
      }}</span>
      <span class="brand-text">
        <span class="brand-name">{{ t("nav.companyName") }}</span>
        <span class="brand-sub">{{ t("nav.subtitle") }}</span>
      </span>
    </div>

    <nav class="sidebar-nav">
      <!-- "/" matches exactly only; otherwise it would be active on every page -->
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :active-class="item.exact ? '' : 'is-active'"
        :exact-active-class="item.exact ? 'is-active' : ''"
        :title="collapsed ? t(item.label) : undefined"
        :aria-label="collapsed ? t(item.label) : undefined"
      >
        <svg
          class="nav-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          v-html="item.icon"
        />
        <span class="nav-label">{{ t(item.label) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button
        type="button"
        class="nav-item"
        :aria-expanded="!collapsed"
        :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')"
        :title="collapsed ? t('nav.expand') : undefined"
        @click="$emit('toggle')"
      >
        <svg
          class="nav-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          v-html="collapsed ? ICONS.chevronRight : ICONS.chevronLeft"
        />
        <span class="nav-label">{{ t("nav.collapse") }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { useI18n } from "../composables/useI18n";
import { ICONS } from "./icons";

export default {
  name: "AppSidebar",
  props: {
    // Icons-only rail (labels hidden)
    collapsed: { type: Boolean, default: false },
    // Narrow screens: expanded sidebar floating over the content
    overlay: { type: Boolean, default: false },
  },
  emits: ["toggle"],
  setup() {
    const { t } = useI18n();

    const navItems = [
      { to: "/", label: "nav.overview", exact: true, icon: ICONS.home },
      { to: "/inventory", label: "nav.inventory", icon: ICONS.box },
      { to: "/orders", label: "nav.orders", icon: ICONS.cart },
      { to: "/spending", label: "nav.finance", icon: ICONS.dollar },
      { to: "/demand", label: "nav.demandForecast", icon: ICONS.trending },
      { to: "/restocking", label: "nav.restocking", icon: ICONS.refresh },
      { to: "/reports", label: "nav.reports", icon: ICONS.file },
    ];

    return { t, navItems, ICONS };
  },
};
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  overflow-x: hidden;
  overflow-y: auto;
}

/* Narrow overlay: leaves the grid flow (the 64px column stays reserved) and floats above the scrim */
.sidebar.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  box-shadow: var(--shadow-lg);
  z-index: calc(var(--z-sidebar-overlay) + 1);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
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

.brand-text {
  min-width: 0;
}

.brand-name,
.brand-sub {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-name {
  font-weight: var(--weight-semibold);
  font-size: var(--text-base);
  color: var(--color-text);
}

.brand-sub {
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
  font-family: inherit;
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
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Labels hidden via CSS (not v-if); links keep their name through aria-label */
.sidebar.collapsed .nav-label,
.sidebar.collapsed .brand-text {
  display: none;
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}
</style>
