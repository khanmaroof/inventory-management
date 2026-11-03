# Design Tokens

Drop this into the global stylesheet (the unscoped `<style>` in `App.vue`, or `src/styles/tokens.css` imported from `main.js`). If the project already has a palette, keep its hex values and map them onto these names - the names are what matters for consistency.

## Why a 4px scale

Every spacing value in the UI should come from a small, predictable set. A 4px base gives enough resolution for tight controls (4/8px) while the larger steps (24/32/48px) create clear section breaks. When everything snaps to the same grid, alignment looks intentional even if nobody measured it. Ten-ish steps are enough; more steps just recreate the original chaos.

## Token set

```css
:root {
  /* Spacing - 4px base */
  --space-0: 0;
  --space-1: 0.25rem; /* 4px  - icon/text gap in tight controls */
  --space-2: 0.5rem; /* 8px  - inline gaps, badge padding */
  --space-3: 0.75rem; /* 12px - nav item padding, table cell padding */
  --space-4: 1rem; /* 16px - default control & card inner gap */
  --space-5: 1.25rem; /* 20px - card padding */
  --space-6: 1.5rem; /* 24px - gap between cards / sections */
  --space-8: 2rem; /* 32px - page gutter on desktop */
  --space-10: 2.5rem; /* 40px - large section breaks */
  --space-12: 3rem; /* 48px - empty states, hero spacing */

  /* Typography */
  --font-sans:
    "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --text-xs: 0.75rem; /* 12px - table headers, captions, badges */
  --text-sm: 0.8125rem; /* 13px - secondary text, meta */
  --text-base: 0.875rem; /* 14px - body, nav items, table cells */
  --text-md: 1rem; /* 16px - card titles */
  --text-lg: 1.25rem; /* 20px - section titles */
  --text-xl: 1.5rem; /* 24px - page titles */
  --text-2xl: 1.875rem; /* 30px - KPI values */
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

  /* Semantic surface/text roles - views use THESE, not raw grays */
  --color-bg: var(--gray-50);
  --color-surface: var(--gray-0);
  --color-surface-muted: var(--gray-50);
  --color-border: var(--gray-200);
  --color-border-strong: var(--gray-300);
  --color-text: var(--gray-900);
  --color-text-secondary: var(--gray-600);
  --color-text-muted: var(--gray-500);

  /* Accent (single brand color) */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-subtle: #eff6ff;
  --color-focus-ring: rgba(37, 99, 235, 0.35);

  /* Status - use only where they carry meaning */
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
  --radius-sm: 4px; /* badges, small inputs */
  --radius-md: 6px; /* buttons, nav items, inputs */
  --radius-lg: 10px; /* cards, modals */
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

  /* Layering */
  --z-sidebar: 40;
  --z-topbar: 30;
  --z-dropdown: 50;
  --z-overlay: 60;
  --z-modal: 70;
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
```

## Snapping existing values

When you meet a hard-coded value during the view sweep, snap it to the nearest token:

| Seen                     | Use         |
| ------------------------ | ----------- |
| 2-5px                    | `--space-1` |
| 6-10px                   | `--space-2` |
| 0.625-0.875rem / 10-14px | `--space-3` |
| 15-18px                  | `--space-4` |
| 1.25rem / 20px           | `--space-5` |
| 22-28px                  | `--space-6` |
| 30-36px                  | `--space-8` |

Odd sizes like `0.313rem`, `0.938rem`, `0.813rem` are usually someone approximating px in rem - snap them. Font sizes follow the same idea against the type ramp.

Exceptions that don't need tokens: `0`, `1px` borders, `50%`/`100%`, chart geometry inside SVGs, and values computed in JS.

## Rewriting global utilities

Keep existing class names; only their declarations change. Example:

```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-xs);
}
.card + .card {
  margin-top: var(--space-6);
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-tight);
  color: var(--color-text);
}
.page-header p {
  margin-top: var(--space-1);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

th {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
td {
  padding: var(--space-3);
  font-size: var(--text-base);
  color: var(--gray-700);
  border-top: 1px solid var(--gray-100);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}
.badge.success {
  background: var(--color-success-subtle);
  color: var(--color-success-text);
}
.badge.danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger-text);
}
```

Sentence-case badges (no uppercase) read as more modern; switch only if the project has no rule against it.

## Buttons and focus

If the app has no shared button styles, add them so views stop inventing their own:

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
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
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```
