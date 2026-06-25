import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.json")

def _load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

# --- PRODUCTS ---

def list_products():
    db = _load_db()
    return db.get("products", [])

def get_product(product_id):
    db = _load_db()
    product = next((p for p in db.get("products", []) if p["id"] == product_id), None)
    if not product:
        return {"error": f"Product {product_id} not found"}
    
    inv_item = next((i for i in db.get("inventory", []) if i["product_id"] == product_id), None)
    product["stock"] = inv_item["quantity"] if inv_item else 0
    product["location"] = inv_item["location"] if inv_item else "N/A"
    return product

def update_product(product_id, name=None, price=None, description=None):
    db = _load_db()
    product = next((p for p in db.get("products", []) if p["id"] == product_id), None)
    if not product:
        return {"error": f"Product {product_id} not found"}
        
    if name is not None: product["name"] = name
    if price is not None: product["price"] = price
    if description is not None: product["description"] = description
    
    _save_db(db)
    return {"status": "success", "product": product}

# --- INVENTORY ---

def list_inventory():
    db = _load_db()
    return db.get("inventory", [])

def update_inventory(selector, quantity=None, change=None):
    db = _load_db()
    products = db.get("products", [])
    inventory = db.get("inventory", [])
    
    target_id = None
    try:
        target_id = int(selector)
    except ValueError:
        pass
        
    product = next((p for p in products if p["id"] == target_id or p["sku"].lower() == str(selector).lower()), None)
    if not product:
        return {"error": f"Product matching '{selector}' not found"}
        
    inv_item = next((i for i in inventory if i["product_id"] == product["id"]), None)
    if not inv_item:
        return {"error": "Inventory item not found"}
        
    if quantity is not None:
        inv_item["quantity"] = quantity
    elif change is not None:
        inv_item["quantity"] += change
        
    if inv_item["quantity"] < 0:
        inv_item["quantity"] = 0
        
    _save_db(db)
    return {"status": "success", "product_id": product["id"], "new_quantity": inv_item["quantity"]}

# --- ORDERS ---

def list_orders():
    db = _load_db()
    return db.get("orders", [])

def get_order(order_id):
    db = _load_db()
    order = next((o for o in db.get("orders", []) if o["id"] == order_id), None)
    if not order:
        return {"error": f"Order {order_id} not found"}
    return order

def update_order(order_id, financial_status=None, fulfillment_status=None):
    db = _load_db()
    order = next((o for o in db.get("orders", []) if o["id"] == order_id), None)
    if not order:
        return {"error": f"Order {order_id} not found"}
        
    if financial_status:
        order["financial_status"] = financial_status
    if fulfillment_status:
        order["fulfillment_status"] = fulfillment_status
        
    _save_db(db)
    return {"status": "success", "order": order}

# --- DISCOUNTS ---

def list_discounts():
    db = _load_db()
    return db.get("discounts", [])

def create_discount(code, discount_type, value):
    db = _load_db()
    discounts = db.get("discounts", [])
    code_upper = code.upper()
    
    if any(d["code"] == code_upper for d in discounts):
        return {"error": f"Discount code {code_upper} already exists"}
        
    new_discount = {
        "code": code_upper,
        "discount_type": discount_type,
        "value": value,
        "status": "active",
        "usage_count": 0
    }
    discounts.append(new_discount)
    _save_db(db)
    return {"status": "success", "discount": new_discount}

def update_discount(code, status):
    db = _load_db()
    discounts = db.get("discounts", [])
    code_upper = code.upper()
    
    discount = next((d for d in discounts if d["code"] == code_upper), None)
    if not discount:
        return {"error": f"Discount {code_upper} not found"}
        
    discount["status"] = status
    _save_db(db)
    return {"status": "success", "discount": discount}

# --- ANALYTICS ---

def analytics_sales():
    db = _load_db()
    valid_orders = [o for o in db.get("orders", []) if o["financial_status"] in ["paid", "partially_refunded"] or o["fulfillment_status"] == "fulfilled"]
    
    total_sales = sum(o["total_price"] for o in valid_orders)
    num_orders = len(valid_orders)
    aov = total_sales / num_orders if num_orders > 0 else 0
    
    return {
        "total_sales": total_sales,
        "num_orders": num_orders,
        "aov": aov,
        "total_logged": len(db.get("orders", []))
    }

def analytics_top_products():
    db = _load_db()
    product_sales = {}
    for o in db.get("orders", []):
        if o["financial_status"] == "refunded": continue
        for item in o["items"]:
            pid = item["product_id"]
            if pid not in product_sales:
                product_sales[pid] = {"qty": 0, "revenue": 0.0}
            product_sales[pid]["qty"] += item["quantity"]
            product_sales[pid]["revenue"] += item["quantity"] * item["price"]
            
    sorted_sales = sorted(product_sales.items(), key=lambda x: x[1]["qty"], reverse=True)
    return [{"product_id": pid, "units_sold": stats["qty"], "revenue": stats["revenue"]} for pid, stats in sorted_sales]

def analytics_slow_inventory():
    db = _load_db()
    products = db.get("products", [])
    inv_map = {i["product_id"]: i["quantity"] for i in db.get("inventory", [])}
    
    sold_qty = {}
    for o in db.get("orders", []):
        if o["financial_status"] == "refunded": continue
        for item in o["items"]:
            pid = item["product_id"]
            sold_qty[pid] = sold_qty.get(pid, 0) + item["quantity"]
            
    slow_items = []
    for p in products:
        pid = p["id"]
        stock = inv_map.get(pid, 0)
        sold = sold_qty.get(pid, 0)
        if stock > 30 and sold < 5:
            slow_items.append({"product_id": pid, "sku": p["sku"], "stock": stock, "sold": sold})
            
    return slow_items

# --- NOTIFICATIONS ---

def log_notification(message):
    db = _load_db()
    notif = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": message
    }
    db.get("notifications", []).append(notif)
    _save_db(db)
    return {"status": "success", "notification": notif}

# --- PAGES ---

def create_landing_page(title, content, url_handle):
    db = _load_db()
    if "pages" not in db:
        db["pages"] = []
    
    new_page = {
        "title": title,
        "content": content,
        "url_handle": url_handle,
        "status": "published",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    db["pages"].append(new_page)
    _save_db(db)
    return {"status": "success", "page": new_page}
