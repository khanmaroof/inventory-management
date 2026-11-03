import threading
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Submitted restocking orders, kept in memory only (lost on server restart, like all other data here)
restocking_orders: list = []
# Sync endpoints run in a threadpool, so numbering + append must be atomic to keep order numbers unique
restocking_orders_lock = threading.Lock()

# User-created tasks, in memory only. Ids are "task-N" strings so they never collide with the
# numeric ids of the mock tasks the client merges in from useAuth.js
tasks: list = []
tasks_lock = threading.Lock()
task_seq = 0

# Guards purchase_orders (loaded from purchase_orders.json) so the one-PO-per-backlog-item check
# and the append happen atomically
purchase_orders_lock = threading.Lock()

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: date
    notes: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    priority: Literal['high', 'medium', 'low']
    dueDate: str
    status: Literal['pending', 'completed']

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: date

class RestockingOrderLine(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class CreateRestockingOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockingOrderLine] = Field(min_length=1)

class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    lead_time_days: int
    line_total: float

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderItem]
    total_cost: float
    budget: float
    submitted_date: str
    lead_time_days: int
    expected_delivery: str
    status: str

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/restocking-orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restocking_orders))

@app.post("/api/restocking-orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order for demand-forecast items within a budget"""
    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}

    items = []
    for line in request.items:
        forecast = forecasts_by_sku.get(line.sku)
        if not forecast:
            raise HTTPException(status_code=404, detail=f"SKU {line.sku} not found in demand forecasts")
        # Price from server data, never from the client, so the budget check below can't be bypassed
        items.append({
            "sku": line.sku,
            "name": forecast["item_name"],
            "quantity": line.quantity,
            "unit_cost": forecast["unit_cost"],
            "lead_time_days": forecast["lead_time_days"],
            "line_total": round(line.quantity * forecast["unit_cost"], 2),
        })

    total_cost = round(sum(item["line_total"] for item in items), 2)
    if total_cost > request.budget:
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_cost} exceeds budget {request.budget}"
        )

    # The order ships complete, so it arrives when its slowest item does
    lead_time_days = max(item["lead_time_days"] for item in items)
    submitted = date.today()

    with restocking_orders_lock:
        order_seq = len(restocking_orders) + 1
        order = {
            "id": f"rst-{order_seq}",
            "order_number": f"RST-{order_seq:04d}",
            "items": items,
            "total_cost": total_cost,
            "budget": request.budget,
            "submitted_date": submitted.isoformat(),
            "lead_time_days": lead_time_days,
            "expected_delivery": (submitted + timedelta(days=lead_time_days)).isoformat(),
            "status": "Submitted",
        }
        restocking_orders.append(order)
    return order

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    po_ids_by_backlog = {po["backlog_item_id"]: po["id"] for po in purchase_orders}
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # The Dashboard switches "Create PO" to "View PO" on purchase_order_id, so expose it
        # alongside the flag to keep that state across reloads
        item_dict["purchase_order_id"] = po_ids_by_backlog.get(item["id"])
        item_dict["has_purchase_order"] = item_dict["purchase_order_id"] is not None
        result.append(item_dict)
    return result

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one per item)"""
    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")

    with purchase_orders_lock:
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail="Backlog item already has a purchase order")
        po = {
            "id": f"po-{len(purchase_orders) + 1}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": request.supplier_name,
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": request.expected_delivery_date.isoformat(),
            "status": "Pending",
            "created_date": date.today().isoformat(),
            "notes": request.notes,
        }
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    for po in purchase_orders:
        if po["backlog_item_id"] == backlog_item_id:
            return po
    raise HTTPException(status_code=404, detail=f"Purchase order for backlog item {backlog_item_id} not found")

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get user-created tasks, newest first"""
    return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task"""
    global task_seq
    with tasks_lock:
        # Monotonic counter rather than len(tasks), so ids aren't reused after a delete
        task_seq += 1
        task = {
            "id": f"task-{task_seq}",
            "title": request.title,
            "priority": request.priority,
            "dueDate": request.dueDate.isoformat(),
            "status": "pending",
        }
        tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    with tasks_lock:
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed" if task["status"] == "pending" else "pending"
                return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/api/tasks/{task_id}", response_model=Task)
def delete_task(task_id: str):
    """Delete a task"""
    with tasks_lock:
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                return tasks.pop(i)
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports (honors the global filters)"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    quarters = {}

    for order in filtered_orders:
        order_date = order.get('order_date', '')
        # Derive the quarter from the YYYY-MM prefix; skip malformed dates
        try:
            year, month_num = int(order_date[:4]), int(order_date[5:7])
        except ValueError:
            continue
        if year != 2025 or not 1 <= month_num <= 12:
            continue
        quarter = f"Q{(month_num - 1) // 3 + 1}-{year}"

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0,
                'fulfillment_rate': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for data in quarters.values():
        data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
        data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends (honors the global filters)"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    months = {}

    for order in filtered_orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        order_month = order_date[:7]  # Gets YYYY-MM

        if order_month not in months:
            months[order_month] = {
                'month': order_month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[order_month]['order_count'] += 1
        months[order_month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[order_month]['delivered_count'] += 1

    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
