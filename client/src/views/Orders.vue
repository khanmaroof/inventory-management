<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t("orders.title") }}</h2>
      <p>{{ t("orders.description") }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t("common.loading") }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t("status.delivered") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Delivered").length }}
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t("status.shipped") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Shipped").length }}
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t("status.processing") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Processing").length }}
          </div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t("status.backordered") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Backordered").length }}
          </div>
        </div>
      </div>

      <!-- Submitted restocking orders (not affected by the global filters) -->
      <div class="card submitted-orders">
        <div class="card-header">
          <h3 class="card-title">
            {{ t("orders.submittedOrders.title") }} ({{
              restockingOrders.length
            }})
          </h3>
        </div>
        <div v-if="restockingError" class="error">{{ restockingError }}</div>
        <div v-else-if="restockingOrders.length === 0" class="empty-state">
          {{ t("orders.submittedOrders.empty") }}
        </div>
        <div v-else class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">
                  {{ t("orders.table.orderNumber") }}
                </th>
                <th class="col-items">{{ t("orders.table.items") }}</th>
                <th class="col-value">
                  {{ t("orders.submittedOrders.total") }}
                </th>
                <th class="col-date">
                  {{ t("orders.submittedOrders.submittedDate") }}
                </th>
                <th class="col-date">
                  {{ t("orders.submittedOrders.leadTime") }}
                </th>
                <th class="col-date">
                  {{ t("orders.table.expectedDelivery") }}
                </th>
                <th class="col-status">{{ t("orders.table.status") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in restockingOrders" :key="order.id">
                <td class="col-order-number">
                  <strong>{{ order.order_number }}</strong>
                </td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{
                        t("orders.itemsCount", { count: order.items.length })
                      }}
                    </summary>
                    <div class="items-dropdown">
                      <div
                        v-for="item in order.items"
                        :key="item.sku"
                        class="item-entry"
                      >
                        <span class="item-name">{{
                          translateProductName(item.name)
                        }}</span>
                        <span class="item-meta"
                          >{{ t("orders.quantity") }}: {{ item.quantity }} @
                          {{ formatMoney(item.unit_cost, 2) }}</span
                        >
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-value">
                  <strong>{{ formatMoney(order.total_cost, 2) }}</strong>
                </td>
                <td class="col-date">{{ formatDate(order.submitted_date) }}</td>
                <td class="col-date">
                  {{
                    t("orders.submittedOrders.days", {
                      count: order.lead_time_days,
                    })
                  }}
                </td>
                <td class="col-date">
                  {{ formatDate(order.expected_delivery) }}
                </td>
                <td class="col-status">
                  <span class="badge info">
                    {{
                      t(
                        `orders.submittedOrders.status.${order.status.toLowerCase()}`,
                      )
                    }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t("orders.allOrders") }} ({{ orders.length }})
          </h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">
                  {{ t("orders.table.orderNumber") }}
                </th>
                <th class="col-customer">{{ t("orders.table.customer") }}</th>
                <th class="col-items">{{ t("orders.table.items") }}</th>
                <th class="col-status">{{ t("orders.table.status") }}</th>
                <th class="col-date">{{ t("orders.table.orderDate") }}</th>
                <th class="col-date">
                  {{ t("orders.table.expectedDelivery") }}
                </th>
                <th class="col-value">{{ t("orders.table.totalValue") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number">
                  <strong>{{ order.order_number }}</strong>
                </td>
                <td class="col-customer">
                  {{ translateCustomerName(order.customer) }}
                </td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{
                        t("orders.itemsCount", { count: order.items.length })
                      }}
                    </summary>
                    <div class="items-dropdown">
                      <div
                        v-for="(item, idx) in order.items"
                        :key="idx"
                        class="item-entry"
                      >
                        <span class="item-name">{{
                          translateProductName(item.name)
                        }}</span>
                        <span class="item-meta"
                          >{{ t("orders.quantity") }}: {{ item.quantity }} @
                          {{ currencySymbol }}{{ item.unit_price }}</span
                        >
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">
                  {{ formatDate(order.expected_delivery) }}
                </td>
                <td class="col-value">
                  <strong
                    >{{ currencySymbol
                    }}{{ order.total_value.toLocaleString() }}</strong
                  >
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
import { ref, onMounted, watch, computed } from "vue";
import { api } from "../api";
import { useFilters } from "../composables/useFilters";
import { useI18n } from "../composables/useI18n";
import { formatCurrency, formatCurrencyWithDecimals } from "../utils/currency";

export default {
  name: "Orders",
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } =
      useI18n();

    const currencySymbol = computed(() => {
      return currentCurrency.value === "JPY" ? "¥" : "$";
    });
    const loading = ref(true);
    const error = ref(null);
    const orders = ref([]);
    const restockingOrders = ref([]);
    const restockingError = ref(null);

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters,
    } = useFilters();

    const loadOrders = async () => {
      try {
        loading.value = true;
        const filters = getCurrentFilters();

        // Restocking orders are independent of the global filters; a failure here
        // must not break the main orders table
        restockingError.value = null;
        const restockingPromise = api.getRestockingOrders().catch((err) => {
          console.error("Failed to load submitted orders:", err);
          restockingError.value = t("orders.submittedOrders.loadFailed");
          return [];
        });

        const [fetchedOrders, fetchedRestocking] = await Promise.all([
          api.getOrders(filters),
          restockingPromise,
        ]);
        restockingOrders.value = fetchedRestocking;

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date);
          const dateB = new Date(b.order_date);
          return dateA - dateB;
        });
      } catch (err) {
        error.value = "Failed to load orders: " + err.message;
      } finally {
        loading.value = false;
      }
    };

    // Watch for filter changes and reload data
    watch(
      [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
      () => {
        loadOrders();
      },
    );

    const getOrdersByStatus = (status) => {
      return orders.value.filter((order) => order.status === status);
    };

    const getOrderStatusClass = (status) => {
      const statusMap = {
        Delivered: "success",
        Shipped: "info",
        Processing: "warning",
        Backordered: "danger",
      };
      return statusMap[status] || "info";
    };

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n();
      const locale = currentLocale.value === "ja" ? "ja-JP" : "en-US";
      // Date-only strings (YYYY-MM-DD, used by restocking orders) parse as UTC midnight,
      // which shows the previous day west of UTC; parse them as local midnight instead
      const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString);
      return new Date(
        isDateOnly ? `${dateString}T00:00:00` : dateString,
      ).toLocaleDateString(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    };

    const formatMoney = (amount, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
        : formatCurrency(amount, currentCurrency.value);
    };

    onMounted(loadOrders);

    return {
      t,
      loading,
      error,
      orders,
      restockingOrders,
      restockingError,
      formatMoney,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName,
    };
  },
};
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-order-number {
  width: 130px;
}

.col-customer {
  width: 180px;
}

.col-items {
  width: 200px;
}

.col-status {
  width: 130px;
}

.col-date {
  width: 140px;
}

.col-value {
  width: 120px;
}

.submitted-orders {
  margin-bottom: var(--space-6);
}

.empty-state {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--color-accent);
  font-weight: var(--weight-medium);
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: "▶";
  display: inline-block;
  margin-right: var(--space-2);
  font-size: var(--text-xs);
  transition: transform var(--duration-base) var(--ease-out);
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-3);
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 1px solid var(--gray-100);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.item-meta {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
