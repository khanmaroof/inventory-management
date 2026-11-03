<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t("reports.title") }}</h2>
      <p>{{ t("reports.description") }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t("reports.loading") }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div
      v-else-if="quarterlyData.length === 0 && monthlyData.length === 0"
      class="empty-state"
    >
      {{ t("reports.noData") }}
    </div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.quarterly.title") }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t("reports.quarterly.quarter") }}</th>
                <th>{{ t("reports.quarterly.totalOrders") }}</th>
                <th>{{ t("reports.quarterly.totalRevenue") }}</th>
                <th>{{ t("reports.quarterly.avgOrderValue") }}</th>
                <th>{{ t("reports.quarterly.fulfillmentRate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td>
                  <strong>{{ q.quarter }}</strong>
                </td>
                <td>{{ formatInteger(q.total_orders) }}</td>
                <td>{{ formatMoney(q.total_revenue) }}</td>
                <td>{{ formatMoney(q.avg_order_value, 2) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ formatPercent(q.fulfillment_rate) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.trend.title") }}</h3>
        </div>
        <div class="chart-container">
          <div
            class="bar-chart"
            role="group"
            :aria-label="t('reports.trend.title')"
          >
            <div
              v-for="month in monthlyData"
              :key="month.month"
              class="bar-wrapper"
            >
              <div class="bar-container">
                <div
                  class="bar"
                  role="img"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatMoney(month.revenue)"
                  :aria-label="
                    formatMonth(month.month) + ': ' + formatMoney(month.revenue)
                  "
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.mom.title") }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t("reports.mom.month") }}</th>
                <th>{{ t("reports.mom.orders") }}</th>
                <th>{{ t("reports.mom.revenue") }}</th>
                <th>{{ t("reports.mom.change") }}</th>
                <th>{{ t("reports.mom.growthRate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td>
                  <strong>{{ formatMonth(month.month) }}</strong>
                </td>
                <td>{{ formatInteger(month.order_count) }}</td>
                <td>{{ formatMoney(month.revenue) }}</td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    "
                  >
                    {{
                      getChangeValue(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    "
                  >
                    {{
                      getGrowthRate(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.totalRevenue") }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            {{ t("reports.stats.avgMonthlyRevenue") }}
          </div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.totalOrders") }}</div>
          <div class="stat-value">{{ formatInteger(totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.bestQuarter") }}</div>
          <div class="stat-value">{{ bestQuarter || "-" }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from "vue";
import { api } from "../api";
import { useFilters } from "../composables/useFilters";
import { useI18n } from "../composables/useI18n";
import { formatCurrency, formatCurrencyWithDecimals } from "../utils/currency";

export default {
  name: "Reports",
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n();

    const loading = ref(true);
    const error = ref(null);
    const quarterlyData = ref([]);
    const monthlyData = ref([]);

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters,
    } = useFilters();

    // Only the latest request may write results; earlier in-flight ones are dropped
    let requestId = 0;

    const loadData = async () => {
      const currentRequest = ++requestId;
      try {
        loading.value = true;
        error.value = null;
        const filters = getCurrentFilters();
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters),
        ]);
        if (currentRequest !== requestId) return;
        quarterlyData.value = quarterly;
        monthlyData.value = monthly;
      } catch (err) {
        if (currentRequest !== requestId) return;
        error.value = t("reports.loadFailed") + ": " + err.message;
        console.error("Failed to load reports:", err);
      } finally {
        // A newer request owns the loading flag
        if (currentRequest === requestId) loading.value = false;
      }
    };

    // Watch for filter changes and reload data
    watch(
      [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
      () => {
        loadData();
      },
    );

    // Derived stats
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0),
    );

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0
        ? totalRevenue.value / monthlyData.value.length
        : 0,
    );

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0),
    );

    // Empty string when there are no quarters with revenue
    const bestQuarter = computed(() => {
      let best = null;
      for (const q of quarterlyData.value) {
        if (
          q.total_revenue > 0 &&
          (!best || q.total_revenue > best.total_revenue)
        ) {
          best = q;
        }
      }
      return best ? best.quarter : "";
    });

    // Computed once instead of per bar per render
    const maxRevenue = computed(() =>
      Math.max(0, ...monthlyData.value.map((m) => m.revenue)),
    );

    const numberLocale = computed(() =>
      currentLocale.value === "ja" ? "ja-JP" : "en-US",
    );

    const formatMoney = (amount, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
        : formatCurrency(amount, currentCurrency.value);
    };

    const formatInteger = (num) => num.toLocaleString(numberLocale.value);

    const formatPercent = (value) =>
      value.toLocaleString(numberLocale.value, { maximumFractionDigits: 1 }) +
      "%";

    // Convert YYYY-MM to "<localized month> <year>"
    const formatMonth = (monthStr) => {
      const [year, month] = (monthStr || "").split("-");
      const monthIndex = parseInt(month, 10) - 1;
      const keys = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
      ];
      if (!keys[monthIndex]) return monthStr;
      return t(`months.${keys[monthIndex]}`) + " " + year;
    };

    // Max bar height is 200px
    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0;
      return (revenue / maxRevenue.value) * 200;
    };

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return "badge success";
      if (rate >= 75) return "badge warning";
      return "badge danger";
    };

    const getChangeValue = (current, previous) => {
      const change = current - previous;
      if (change > 0) return "+" + formatMoney(change);
      if (change < 0) return "-" + formatMoney(Math.abs(change));
      return formatMoney(0);
    };

    const getChangeClass = (current, previous) => {
      const change = current - previous;
      if (change > 0) return "positive-change";
      if (change < 0) return "negative-change";
      return "";
    };

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return t("reports.mom.notAvailable");
      const rate = (current - previous) / previous;
      return rate.toLocaleString(numberLocale.value, {
        style: "percent",
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
        signDisplay: "exceptZero",
      });
    };

    onMounted(loadData);

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      formatMoney,
      formatInteger,
      formatPercent,
      formatMonth,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate,
    };
  },
};
</script>

<style scoped>
.reports {
  padding: 0;
}

/* .card, .card-header, .card-title, .stat-card, .stat-label, .stat-value, .badge come from App.vue */

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--color-surface-muted);
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.reports-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--gray-100);
  color: var(--gray-700);
}

.reports-table tr:hover {
  background: var(--color-surface-muted);
}

.chart-container {
  padding: var(--space-8) var(--space-4);
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--color-accent);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background var(--duration-base) var(--ease-out);
  cursor: pointer;
}

.bar:hover {
  background: var(--color-accent-hover);
}

.bar-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-6);
}

.stats-grid {
  margin-top: var(--space-6);
}

.positive-change {
  color: var(--color-success);
  font-weight: var(--weight-semibold);
}

.negative-change {
  color: var(--color-danger);
  font-weight: var(--weight-semibold);
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
}

.empty-state {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
}

.error {
  background: var(--color-danger-subtle);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
}

/* Responsive: the 12-month bar chart scrolls inside its card on phones instead of the page */
@media (max-width: 767px) {
  .chart-container {
    overflow-x: auto;
  }

  .bar-chart {
    /* keep bars readable; scroll container absorbs the overflow */
    min-width: 480px;
  }
}
</style>
