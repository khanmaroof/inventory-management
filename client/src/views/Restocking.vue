<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t("restocking.title") }}</h2>
      <p>{{ t("restocking.description") }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t("common.loading") }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t("restocking.budget") }}</h3>
          <span class="budget-value">{{ formatMoney(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          step="100"
        />
        <div class="budget-scale">
          <span>{{ formatMoney(0) }}</span>
          <span>{{ formatMoney(maxBudget) }}</span>
        </div>
        <p class="budget-hint">{{ t("restocking.budgetHint") }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t("restocking.stats.totalCost") }}</div>
          <div class="stat-value">{{ formatMoney(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">
            {{ t("restocking.stats.remainingBudget") }}
          </div>
          <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t("restocking.stats.itemCount") }}</div>
          <div class="stat-value">{{ recommendation.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t("restocking.stats.leadTime") }}</div>
          <div class="stat-value">
            {{ t("restocking.days", { count: expectedLeadTime }) }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t("restocking.recommendedItems") }} ({{ recommendation.length }})
          </h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="
              recommendation.length === 0 || submitting || successOrder !== null
            "
            @click="placeOrder"
          >
            {{
              submitting ? t("restocking.placing") : t("restocking.placeOrder")
            }}
          </button>
        </div>

        <div v-if="successOrder" class="message success-message">
          {{
            t("restocking.orderPlaced", {
              orderNumber: successOrder.order_number,
            })
          }}
          <router-link to="/orders">{{
            t("restocking.viewOrders")
          }}</router-link>
        </div>
        <div v-if="submitError" class="message error-message">
          {{ submitError }}
        </div>

        <div v-if="recommendation.length === 0" class="empty-state">
          {{ t("restocking.noItems") }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t("restocking.table.sku") }}</th>
                <th>{{ t("restocking.table.itemName") }}</th>
                <th>{{ t("restocking.table.trend") }}</th>
                <th class="num">{{ t("restocking.table.quantity") }}</th>
                <th class="num">{{ t("restocking.table.unitCost") }}</th>
                <th class="num">{{ t("restocking.table.lineTotal") }}</th>
                <th class="num">{{ t("restocking.table.leadTime") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation" :key="item.sku">
                <td>
                  <strong>{{ item.sku }}</strong>
                </td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{
                    t(`trends.${item.trend}`)
                  }}</span>
                </td>
                <td class="num">{{ item.quantity }}</td>
                <td class="num">{{ formatMoney(item.unit_cost, 2) }}</td>
                <td class="num">
                  <strong>{{ formatMoney(item.line_total, 2) }}</strong>
                </td>
                <td class="num">
                  {{ t("restocking.days", { count: item.lead_time_days }) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";
import { formatCurrency, formatCurrencyWithDecimals } from "../utils/currency";

const BUDGET_STEP = 100;
// Lower rank = higher priority
const TREND_RANK = { increasing: 0, stable: 1, decreasing: 2 };

export default {
  name: "Restocking",
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n();

    const loading = ref(true);
    const error = ref(null);
    const forecasts = ref([]);
    // Budget is always held in base USD; it is only converted for display
    const budget = ref(0);
    const submitting = ref(false);
    const submitError = ref(null);
    const successOrder = ref(null);

    // Needed quantity: the forecast gap if demand is growing, otherwise the full
    // forecasted demand (nothing to close a gap against, so stock to forecast level)
    const getNeededQty = (f) => {
      const gap = f.forecasted_demand - f.current_demand;
      return gap > 0 ? gap : f.forecasted_demand;
    };

    // Candidates ranked by trend (increasing > stable > decreasing), then by gap descending
    const rankedItems = computed(() => {
      return forecasts.value
        .map((f) => ({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          unit_cost: f.unit_cost,
          lead_time_days: f.lead_time_days,
          needed: getNeededQty(f),
          gap: f.forecasted_demand - f.current_demand,
        }))
        .filter((i) => i.needed > 0 && i.unit_cost > 0)
        .sort((a, b) => {
          const rankDiff =
            (TREND_RANK[a.trend] ?? 3) - (TREND_RANK[b.trend] ?? 3);
          return rankDiff !== 0 ? rankDiff : b.gap - a.gap;
        });
    });

    // Slider max: cost of fulfilling every needed quantity, rounded up to the next 100
    const maxBudget = computed(() => {
      const total = rankedItems.value.reduce(
        (sum, i) => sum + i.needed * i.unit_cost,
        0,
      );
      return Math.ceil(total / BUDGET_STEP) * BUDGET_STEP;
    });

    // Greedy fill. Money is tracked in integer cents to avoid float drift so the
    // total can never exceed the budget the server validates against.
    const recommendation = computed(() => {
      let remainingCents = Math.round(budget.value * 100);
      const selected = [];

      for (const item of rankedItems.value) {
        const unitCents = Math.round(item.unit_cost * 100);
        let quantity = 0;

        if (item.needed * unitCents <= remainingCents) {
          // Full needed quantity fits
          quantity = item.needed;
        } else {
          // Partial fill: take as many units as the remaining budget allows (if at
          // least one), then keep walking - later, cheaper items may still fit
          quantity = Math.floor(remainingCents / unitCents);
        }

        if (quantity >= 1) {
          remainingCents -= quantity * unitCents;
          selected.push({
            sku: item.sku,
            name: item.name,
            trend: item.trend,
            quantity,
            unit_cost: item.unit_cost,
            lead_time_days: item.lead_time_days,
            line_total: (quantity * unitCents) / 100,
          });
        }
      }

      return selected;
    });

    const totalCost = computed(() => {
      return (
        recommendation.value.reduce(
          (sum, i) => sum + Math.round(i.line_total * 100),
          0,
        ) / 100
      );
    });

    const remainingBudget = computed(() =>
      Math.max(0, budget.value - totalCost.value),
    );

    // Order arrives when the slowest selected item does
    const expectedLeadTime = computed(() => {
      return recommendation.value.reduce(
        (max, i) => Math.max(max, i.lead_time_days),
        0,
      );
    });

    const formatMoney = (amount, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
        : formatCurrency(amount, currentCurrency.value);
    };

    const loadForecasts = async () => {
      try {
        loading.value = true;
        error.value = null;
        forecasts.value = await api.getDemandForecasts();
        // Default to 50% of max, snapped to the slider step
        budget.value =
          Math.round(maxBudget.value / 2 / BUDGET_STEP) * BUDGET_STEP;
      } catch (err) {
        error.value = t("restocking.loadFailed") + ": " + err.message;
      } finally {
        loading.value = false;
      }
    };

    const placeOrder = async () => {
      if (
        recommendation.value.length === 0 ||
        submitting.value ||
        successOrder.value
      )
        return;
      submitting.value = true;
      submitError.value = null;
      successOrder.value = null;
      try {
        successOrder.value = await api.createRestockingOrder({
          budget: budget.value,
          items: recommendation.value.map((i) => ({
            sku: i.sku,
            quantity: i.quantity,
          })),
        });
      } catch (err) {
        // 422 validation errors carry an array in `detail`; only show plain-string messages
        const detail = err.response?.data?.detail;
        submitError.value =
          typeof detail === "string" ? detail : t("restocking.orderFailed");
      } finally {
        submitting.value = false;
      }
    };

    // A placed order matches the current recommendation, so Place Order stays disabled
    // (preventing a duplicate submit) until the budget changes and a new plan is shown
    watch(budget, () => {
      successOrder.value = null;
      submitError.value = null;
    });

    onMounted(loadForecasts);

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      recommendation,
      totalCost,
      remainingBudget,
      expectedLeadTime,
      submitting,
      submitError,
      successOrder,
      formatMoney,
      placeOrder,
      translateProductName,
    };
  },
};
</script>

<style scoped>
.budget-card {
  margin-bottom: var(--space-6);
}

.budget-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
}

.budget-slider {
  width: 100%;
  accent-color: var(--color-accent);
  margin: var(--space-2) 0;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.budget-hint {
  margin-top: var(--space-3);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

/* Matches global .btn.btn-primary */
.place-order-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--color-accent);
  color: #fff;
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out);
}

.place-order-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.place-order-btn:disabled {
  background: var(--color-border-strong);
  border-color: var(--color-border-strong);
  cursor: not-allowed;
}

.message {
  margin: 0 0 var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
}

.success-message {
  background: var(--color-success-subtle);
  color: var(--color-success-text);
  border: 1px solid var(--color-success);
}

.success-message a {
  margin-left: var(--space-2);
  color: var(--color-success-text);
  font-weight: var(--weight-semibold);
  text-decoration: underline;
}

.error-message {
  background: var(--color-danger-subtle);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger);
}

.empty-state {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
}

th.num,
td.num {
  text-align: right;
}
</style>
