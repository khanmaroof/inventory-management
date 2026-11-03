<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-header">
              <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
              <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
            </div>

            <div class="shortage-summary">
              <div class="summary-card danger">
                <div class="info-label">{{ t('purchaseOrder.shortage') }}</div>
                <div class="summary-value">{{ shortage }} {{ t('purchaseOrder.units') }}</div>
              </div>
              <div class="summary-card">
                <div class="info-label">{{ t('purchaseOrder.daysDelayed') }}</div>
                <div class="summary-value">{{ backlogItem.days_delayed }} {{ t('purchaseOrder.days') }}</div>
              </div>
              <div class="summary-card">
                <div class="info-label">{{ t('purchaseOrder.orderId') }}</div>
                <div class="summary-value">{{ backlogItem.order_id }}</div>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="state-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="error" class="form-error">{{ error }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poNumber') }}</div>
                  <div class="info-value order-id">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">{{ purchaseOrder.status }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplierName') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatCurrencyWithDecimals(purchaseOrder.unit_cost, currentCurrency, 2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value total">{{ formatCurrency(viewTotal, currentCurrency) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notesView') }}</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" @submit.prevent="submit">
              <div class="form-grid">
                <div class="form-field full">
                  <label class="info-label" for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                  <input id="po-supplier" v-model="form.supplier_name" class="form-input" :class="{ invalid: touched.supplier && !supplierValid }" type="text" @blur="touched.supplier = true" />
                  <span v-if="touched.supplier && !supplierValid" class="field-error">{{ t('purchaseOrder.required') }}</span>
                </div>
                <div class="form-field">
                  <label class="info-label" for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model.number="form.quantity" class="form-input" :class="{ invalid: !quantityValid }" type="number" min="1" step="1" />
                  <span v-if="!quantityValid" class="field-error">{{ t('purchaseOrder.minQuantity') }}</span>
                </div>
                <div class="form-field">
                  <label class="info-label" for="po-cost">{{ t('purchaseOrder.unitCost') }} (USD)</label>
                  <input id="po-cost" v-model.number="form.unit_cost" class="form-input" :class="{ invalid: touched.cost && !costValid }" type="number" min="0" step="0.01" @blur="touched.cost = true" />
                  <span v-if="touched.cost && !costValid" class="field-error">{{ t('purchaseOrder.minCost') }}</span>
                </div>
                <div class="form-field full">
                  <label class="info-label" for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                  <input id="po-date" v-model="form.expected_delivery_date" class="form-input" :class="{ invalid: touched.date && !dateValid }" type="date" @blur="touched.date = true" />
                  <span v-if="touched.date && !dateValid" class="field-error">{{ t('purchaseOrder.required') }}</span>
                </div>
                <div class="form-field full">
                  <label class="info-label" for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                  <textarea id="po-notes" v-model="form.notes" class="form-input" rows="3"></textarea>
                </div>
              </div>
              <div v-if="error" class="form-error">{{ error }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">{{ t('common.close') }}</button>
            <button v-if="mode !== 'view'" class="btn-primary" type="submit" form="po-form" :disabled="!formValid || submitting">
              {{ submitting ? t('purchaseOrder.creating') : t('purchaseOrder.create') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create',
    validator: (value) => ['create', 'view'].includes(value)
  }
})

const emit = defineEmits(['close', 'po-created'])

const form = reactive({
  supplier_name: '',
  quantity: 1,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})
const touched = reactive({ supplier: false, cost: false, date: false })
const purchaseOrder = ref(null)
const loading = ref(false)
const submitting = ref(false)
const error = ref(null)

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const supplierValid = computed(() => form.supplier_name.trim().length > 0)
const quantityValid = computed(() => Number.isInteger(form.quantity) && form.quantity >= 1)
const costValid = computed(() => typeof form.unit_cost === 'number' && form.unit_cost > 0)
const dateValid = computed(() => form.expected_delivery_date !== '' && !isNaN(new Date(form.expected_delivery_date).getTime()))
const formValid = computed(() => supplierValid.value && quantityValid.value && costValid.value && dateValid.value)

// Total is quantity x unit cost in USD; formatCurrency converts to the active currency
const viewTotal = computed(() => {
  if (!purchaseOrder.value) return 0
  return purchaseOrder.value.quantity * purchaseOrder.value.unit_cost
})

const resetForm = () => {
  form.supplier_name = ''
  form.quantity = Math.max(1, shortage.value)
  form.unit_cost = null
  form.expected_delivery_date = ''
  form.notes = ''
  touched.supplier = touched.cost = touched.date = false
  error.value = null
}

const loadPurchaseOrder = async () => {
  loading.value = true
  error.value = null
  purchaseOrder.value = null
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    error.value = err.response?.data?.detail || t('purchaseOrder.loadError')
    console.error('Failed to load purchase order:', err)
  } finally {
    loading.value = false
  }
}

// (Re)initialise whenever the modal opens or switches item/mode
watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  ([open]) => {
    if (!open || !props.backlogItem) return
    if (props.mode === 'view') {
      loadPurchaseOrder()
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

const submit = async () => {
  if (!formValid.value || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const po = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name.trim(),
      quantity: form.quantity,
      unit_cost: form.unit_cost,
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes.trim() || null
    })
    emit('po-created', po)
  } catch (err) {
    error.value = err.response?.data?.detail || t('purchaseOrder.createError')
    console.error('Failed to create purchase order:', err)
  } finally {
    submitting.value = false
  }
}

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
  margin: 0;
}

.close-button {
  width: 36px;
  height: 36px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.close-button:hover {
  background: var(--gray-100);
  color: var(--color-text);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--text-base);
  color: var(--color-text);
  font-weight: var(--weight-medium);
}

.info-value.order-id,
.info-value.sku {
  font-family: var(--font-mono);
  color: var(--color-accent);
}

.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* Matches global .btn */
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.btn-secondary:hover {
  background: var(--gray-50);
  border-color: var(--color-border-strong);
}


.shortage-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.summary-card {
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--gray-50);
}

.summary-card.danger {
  border-color: var(--color-danger-subtle);
  background: var(--color-danger-subtle);
}

.summary-card.danger .summary-value {
  color: var(--color-danger);
}

.summary-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
}

.item-sku {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.item-name {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-1) 0;
}

.item-header {
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-input {
  height: 36px;
  padding: 0 var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  color: var(--color-text);
}

textarea.form-input {
  height: auto;
  padding: var(--space-2) var(--space-3);
  resize: vertical;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-input.invalid {
  border-color: var(--color-danger);
}

.field-error {
  font-size: var(--text-sm);
  color: var(--color-danger-text);
}

.form-error {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-subtle);
  border-radius: var(--radius-md);
  color: var(--color-danger-text);
  font-size: var(--text-base);
}

.state-message {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-muted);
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-value.total {
  font-weight: var(--weight-bold);
  font-size: var(--text-lg);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: #fff;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--duration-base) var(--ease-out);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--duration-base) var(--ease-out);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.97);
}
</style>
