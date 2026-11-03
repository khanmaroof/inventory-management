<template>
  <div class="app-shell" :class="{ 'is-rail': isRail }">
    <AppSidebar
      :collapsed="sidebarCollapsed"
      :overlay="overlayOpen"
      @toggle="toggleSidebar"
    />
    <div
      v-if="overlayOpen"
      class="sidebar-scrim"
      @click="overlayOpen = false"
    />

    <div class="app-main">
      <header class="topbar">
        <div class="topbar-spacer" />
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </header>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "./api";
import { useAuth } from "./composables/useAuth";
import { useI18n } from "./composables/useI18n";
import AppSidebar from "./components/AppSidebar.vue";
import FilterBar from "./components/FilterBar.vue";
import ProfileMenu from "./components/ProfileMenu.vue";
import ProfileDetailsModal from "./components/ProfileDetailsModal.vue";
import TasksModal from "./components/TasksModal.vue";
import LanguageSwitcher from "./components/LanguageSwitcher.vue";

export default {
  name: "App",
  components: {
    AppSidebar,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
  },
  setup() {
    const { currentUser } = useAuth();
    const { t } = useI18n();
    const showProfileDetails = ref(false);
    const showTasks = ref(false);
    const apiTasks = ref([]);
    const route = useRoute();

    // Sidebar: wide screens toggle expanded/rail (persisted); narrow screens are
    // always a rail, and the toggle opens an expanded overlay on top of the content.
    const STORAGE_KEY = "sidebar-collapsed";
    const readCollapsed = () => {
      try {
        return localStorage.getItem(STORAGE_KEY) === "1";
      } catch {
        return false;
      }
    };
    const mql = window.matchMedia("(min-width: 1280px)");
    const isWide = ref(mql.matches);
    const onMediaChange = (e) => {
      isWide.value = e.matches;
    };
    const collapsedPref = ref(readCollapsed());
    const overlayOpen = ref(false);

    // Grid column is a 64px rail on narrow screens regardless of the saved preference
    const isRail = computed(() => !isWide.value || collapsedPref.value);
    // Labels hidden only while it is a rail and not floating open as overlay
    const sidebarCollapsed = computed(() => isRail.value && !overlayOpen.value);

    const toggleSidebar = () => {
      if (isWide.value) {
        collapsedPref.value = !collapsedPref.value;
        try {
          localStorage.setItem(STORAGE_KEY, collapsedPref.value ? "1" : "0");
        } catch {
          /* ignore */
        }
      } else {
        overlayOpen.value = !overlayOpen.value;
      }
    };

    const onKeydown = (e) => {
      if (e.key === "Escape" && overlayOpen.value) overlayOpen.value = false;
    };

    // Close the overlay on navigation or when the viewport becomes wide
    watch(
      () => route.fullPath,
      () => {
        overlayOpen.value = false;
      },
    );
    watch(isWide, () => {
      overlayOpen.value = false;
    });

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value];
    });

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks();
      } catch (err) {
        console.error("Failed to load tasks:", err);
      }
    };

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData);
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask);
      } catch (err) {
        console.error("Failed to add task:", err);
      }
    };

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some((t) => t.id === taskId);

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(
            (t) => t.id === taskId,
          );
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1);
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId);
          apiTasks.value = apiTasks.value.filter((t) => t.id !== taskId);
        }
      } catch (err) {
        console.error("Failed to delete task:", err);
      }
    };

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find((t) => t.id === taskId);

        if (mockTask) {
          // Toggle mock task status
          mockTask.status =
            mockTask.status === "pending" ? "completed" : "pending";
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId);
          const index = apiTasks.value.findIndex((t) => t.id === taskId);
          if (index !== -1) {
            apiTasks.value[index] = updatedTask;
          }
        }
      } catch (err) {
        console.error("Failed to toggle task:", err);
      }
    };

    onMounted(() => {
      loadTasks();
      mql.addEventListener("change", onMediaChange);
      window.addEventListener("keydown", onKeydown);
    });

    onUnmounted(() => {
      mql.removeEventListener("change", onMediaChange);
      window.removeEventListener("keydown", onKeydown);
    });

    return {
      t,
      isRail,
      sidebarCollapsed,
      overlayOpen,
      toggleSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
    };
  },
};
</script>

<style>
:root {
  /* Spacing - 4px base */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Typography */
  --font-sans:
    "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --text-xs: 0.75rem;
  --text-sm: 0.8125rem;
  --text-base: 0.875rem;
  --text-md: 1rem;
  --text-lg: 1.25rem;
  --text-xl: 1.5rem;
  --text-2xl: 1.875rem;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --tracking-tight: -0.015em;

  /* Neutrals (slate) */
  --gray-0: #ffffff;
  --gray-50: #f8fafc;
  --gray-100: #f1f5f9;
  --gray-200: #e2e8f0;
  --gray-300: #cbd5e1;
  --gray-400: #94a3b8;
  --gray-500: #64748b;
  --gray-600: #475569;
  --gray-700: #334155;
  --gray-800: #1e293b;
  --gray-900: #0f172a;

  /* Semantic roles */
  --color-bg: var(--gray-50);
  --color-surface: var(--gray-0);
  --color-surface-muted: var(--gray-50);
  --color-border: var(--gray-200);
  --color-border-strong: var(--gray-300);
  --color-text: var(--gray-900);
  --color-text-secondary: var(--gray-600);
  --color-text-muted: var(--gray-500);

  /* Accent */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-subtle: #eff6ff;
  --color-focus-ring: rgba(37, 99, 235, 0.35);

  /* Status */
  --color-success: #059669;
  --color-success-subtle: #d1fae5;
  --color-success-text: #065f46;
  --color-info: #2563eb;
  --color-info-subtle: #dbeafe;
  --color-info-text: #1e40af;
  --color-warning: #d97706;
  --color-warning-subtle: #fef3c7;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-subtle: #fee2e2;
  --color-danger-text: #991b1b;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 10px;
  --radius-full: 9999px;

  /* Elevation */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm:
    0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.12);

  /* Motion */
  --duration-fast: 120ms;
  --duration-base: 180ms;
  --ease-out: cubic-bezier(0.2, 0, 0, 1);

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 64px;
  --topbar-height: 56px;
  --content-max-width: 1440px;
  --page-gutter: var(--space-8);

  /* Layering - kept below 1000: ProfileMenu/LanguageSwitcher dropdowns use 1000, modals 2000 */
  --z-filterbar: 20;
  --z-topbar: 30;
  --z-sidebar: 40;
  --z-sidebar-overlay: 50; /* scrim; the floating sidebar sits at +1 */
}

@media (max-width: 768px) {
  :root {
    --page-gutter: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition-duration: 0ms !important;
    animation-duration: 0ms !important;
  }
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* App shell */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--color-bg);
  transition: grid-template-columns var(--duration-base) var(--ease-out);
}

/* Rail = narrow screens (always) or wide screens with the sidebar collapsed */
.app-shell.is-rail {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.sidebar-scrim {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: var(--z-sidebar-overlay);
}

.app-main {
  /* Pin to column 2: when the narrow-screen overlay makes the sidebar position:fixed it leaves
     the grid, and auto-placement would otherwise drop the content into the 64px column */
  grid-column: 2;
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
  -webkit-backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--color-border);
}

.topbar-spacer {
  flex: 1;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  padding: var(--space-6) var(--page-gutter) var(--space-10);
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: var(--tracking-tight);
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}
.stat-card.success .stat-value {
  color: var(--color-success);
}
.stat-card.danger .stat-value {
  color: var(--color-danger);
}
.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-surface-muted);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: var(--weight-semibold);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--gray-100);
  color: var(--gray-700);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--duration-fast) var(--ease-out);
}

tbody tr:hover {
  background: var(--color-surface-muted);
}

/* Sentence-case pills; uppercase is reserved for th and .stat-label */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}

.badge.success,
.badge.increasing {
  background: var(--color-success-subtle);
  color: var(--color-success-text);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-subtle);
  color: var(--color-warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-subtle);
  color: var(--color-danger-text);
}

.badge.info,
.badge.low {
  background: var(--color-info-subtle);
  color: var(--color-info-text);
}

.badge.stable {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out);
}

.btn:hover {
  background: var(--gray-50);
  border-color: var(--color-border-strong);
}

.btn-primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--color-danger-subtle);
  border: 1px solid var(--color-danger-subtle);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
