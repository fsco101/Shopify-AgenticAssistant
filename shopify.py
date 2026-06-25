import os
import json
import argparse
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.json")

def load_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}. Please make sure db.json exists.")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def print_table(headers, rows):
    if not rows:
        print("No data available.")
        return
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    
    # Print header
    header_str = " | ".join(f"{str(h).ljust(widths[i])}" for i, h in enumerate(headers))
    print(header_str)
    print("-" * len(header_str))
    
    # Print rows
    for row in rows:
        print(" | ".join(f"{str(val).ljust(widths[i])}" for i, val in enumerate(row)))

def cmd_products_list(args):
    db = load_db()
    products = db.get("products", [])
    inventory_map = {item["product_id"]: item["quantity"] for item in db.get("inventory", [])}
    
    headers = ["ID", "SKU", "Name", "Price", "Stock"]
    rows = []
    for p in products:
        stock = inventory_map.get(p["id"], 0)
        rows.append([p["id"], p["sku"], p["name"], f"${p['price']:.2f}", stock])
    
    if args.json:
        print(json.dumps(products, indent=2))
    else:
        print("\n--- Shopify Product Catalog ---")
        print_table(headers, rows)

def cmd_products_get(args):
    db = load_db()
    products = db.get("products", [])
    product = next((p for p in products if p["id"] == args.id), None)
    if not product:
        print(f"Error: Product with ID {args.id} not found.")
        return
    
    inventory_item = next((i for i in db.get("inventory", []) if i["product_id"] == args.id), None)
    stock = inventory_item["quantity"] if inventory_item else 0
    location = inventory_item["location"] if inventory_item else "N/A"
    
    if args.json:
        detail = product.copy()
        detail["stock"] = stock
        detail["location"] = location
        print(json.dumps(detail, indent=2))
    else:
        print(f"\nProduct Details for ID {args.id}:")
        print(f"  Name:        {product['name']}")
        print(f"  SKU:         {product['sku']}")
        print(f"  Price:       ${product['price']:.2f}")
        print(f"  Stock:       {stock} units (Location: {location})")
        print(f"  Description: {product['description']}")
        print(f"  Created At:  {product['created_at']}")

def cmd_products_update(args):
    db = load_db()
    products = db.get("products", [])
    product = next((p for p in products if p["id"] == args.id), None)
    if not product:
        print(f"Error: Product with ID {args.id} not found.")
        return
    
    updated = []
    if args.name is not None:
        product["name"] = args.name
        updated.append("name")
    if args.price is not None:
        product["price"] = args.price
        updated.append("price")
    if args.description is not None:
        product["description"] = args.description
        updated.append("description")
        
    if updated:
        save_db(db)
        print(f"Success: Updated {', '.join(updated)} for product ID {args.id}.")
    else:
        print("No changes specified. Use --name, --price, or --description to update.")

def cmd_inventory_list(args):
    db = load_db()
    inventory = db.get("inventory", [])
    products_map = {p["id"]: p for p in db.get("products", [])}
    
    headers = ["Product ID", "SKU", "Product Name", "Quantity", "Location", "Status"]
    rows = []
    for item in inventory:
        p = products_map.get(item["product_id"], {})
        qty = item["quantity"]
        status = "OK"
        if qty == 0:
            status = "OUT OF STOCK"
        elif qty <= 5:
            status = "LOW STOCK"
        rows.append([
            item["product_id"],
            p.get("sku", "N/A"),
            p.get("name", "Unknown"),
            qty,
            item["location"],
            status
        ])
    
    if args.json:
        print(json.dumps(inventory, indent=2))
    else:
        print("\n--- Inventory Status Report ---")
        print_table(headers, rows)

def cmd_inventory_update(args):
    db = load_db()
    inventory = db.get("inventory", [])
    products = db.get("products", [])
    
    # Find product by ID or SKU
    target_product_id = None
    target_sku = None
    
    try:
        pid = int(args.selector)
        target_product_id = pid
    except ValueError:
        target_sku = args.selector
        
    product = None
    if target_product_id:
        product = next((p for p in products if p["id"] == target_product_id), None)
    else:
        product = next((p for p in products if p["sku"].lower() == target_sku.lower()), None)
        
    if not product:
        print(f"Error: Product matching selector '{args.selector}' not found.")
        return
        
    inventory_item = next((i for i in inventory if i["product_id"] == product["id"]), None)
    if not inventory_item:
        print(f"Error: Inventory item not found for product {product['name']}.")
        return
        
    old_qty = inventory_item["quantity"]
    if args.quantity is not None:
        inventory_item["quantity"] = args.quantity
    elif args.change is not None:
        inventory_item["quantity"] += args.change
    else:
        print("Error: Must specify either --quantity or --change.")
        return
        
    if inventory_item["quantity"] < 0:
        inventory_item["quantity"] = 0
        
    save_db(db)
    print(f"Success: Updated inventory for '{product['name']}' ({product['sku']}). Quantity: {old_qty} -> {inventory_item['quantity']}.")

def cmd_orders_list(args):
    db = load_db()
    orders = db.get("orders", [])
    
    headers = ["Order ID", "Customer", "Total", "Financial Status", "Fulfillment Status", "Date"]
    rows = []
    for o in sorted(orders, key=lambda x: x["created_at"], reverse=True):
        rows.append([
            o["id"],
            o["customer_name"],
            f"${o['total_price']:.2f}",
            o["financial_status"],
            o["fulfillment_status"],
            o["created_at"][:10]
        ])
        
    if args.json:
        print(json.dumps(orders, indent=2))
    else:
        print("\n--- Shopify Customer Orders ---")
        print_table(headers, rows)

def cmd_orders_get(args):
    db = load_db()
    orders = db.get("orders", [])
    order = next((o for o in orders if o["id"] == args.id), None)
    if not order:
        print(f"Error: Order with ID {args.id} not found.")
        return
        
    if args.json:
        print(json.dumps(order, indent=2))
    else:
        print(f"\nOrder Details for ID {order['id']}:")
        print(f"  Customer:     {order['customer_name']} ({order['customer_email']})")
        print(f"  Date:         {order['created_at']}")
        print(f"  Financial:    {order['financial_status']}")
        print(f"  Fulfillment:  {order['fulfillment_status']}")
        print(f"  Total:        ${order['total_price']:.2f}")
        print("\n  Line Items:")
        for idx, item in enumerate(order["items"], start=1):
            print(f"    {idx}. SKU: {item['sku']} | Qty: {item['quantity']} | Price: ${item['price']:.2f}")

def cmd_orders_update(args):
    db = load_db()
    orders = db.get("orders", [])
    order = next((o for o in orders if o["id"] == args.id), None)
    if not order:
        print(f"Error: Order with ID {args.id} not found.")
        return
        
    updated = []
    if args.financial_status is not None:
        valid = ["paid", "refunded", "partially_refunded", "pending"]
        if args.financial_status not in valid:
            print(f"Error: Invalid financial status. Must be one of {valid}")
            return
        order["financial_status"] = args.financial_status
        updated.append("financial_status")
        
    if args.fulfillment_status is not None:
        valid = ["fulfilled", "unfulfilled", "cancelled"]
        if args.fulfillment_status not in valid:
            print(f"Error: Invalid fulfillment status. Must be one of {valid}")
            return
        order["fulfillment_status"] = args.fulfillment_status
        updated.append("fulfillment_status")
        
    if updated:
        save_db(db)
        print(f"Success: Updated {', '.join(updated)} for order ID {args.id}.")
    else:
        print("No changes specified. Use --financial_status or --fulfillment_status to update.")

def cmd_discounts_list(args):
    db = load_db()
    discounts = db.get("discounts", [])
    
    headers = ["Code", "Type", "Value", "Status", "Usage Count"]
    rows = []
    for d in discounts:
        val_str = f"{d['value']}%" if d["discount_type"] == "percentage" else f"${d['value']:.2f}"
        rows.append([d["code"], d["discount_type"], val_str, d["status"], d["usage_count"]])
        
    if args.json:
        print(json.dumps(discounts, indent=2))
    else:
        print("\n--- Active & Historical Discount Codes ---")
        print_table(headers, rows)

def cmd_discounts_create(args):
    db = load_db()
    discounts = db.get("discounts", [])
    
    # Check if code already exists
    code_upper = args.code.upper()
    if any(d["code"] == code_upper for d in discounts):
        print(f"Error: Discount code '{code_upper}' already exists.")
        return
        
    new_discount = {
      "code": code_upper,
      "discount_type": args.type,
      "value": args.value,
      "status": "active",
      "usage_count": 0
    }
    discounts.append(new_discount)
    save_db(db)
    print(f"Success: Created discount code '{code_upper}' ({args.type}: {args.value}).")

def cmd_discounts_update(args):
    db = load_db()
    discounts = db.get("discounts", [])
    code_upper = args.code.upper()
    discount = next((d for d in discounts if d["code"] == code_upper), None)
    if not discount:
        print(f"Error: Discount code '{code_upper}' not found.")
        return
        
    if args.status is not None:
        discount["status"] = args.status
        save_db(db)
        print(f"Success: Updated status of '{code_upper}' to '{args.status}'.")
    else:
        print("No changes specified. Use --status to update status (active/inactive).")

def cmd_analytics_sales(args):
    db = load_db()
    orders = db.get("orders", [])
    
    # Sum paid or fulfilled orders
    valid_orders = [o for o in orders if o["financial_status"] in ["paid", "partially_refunded"] or o["fulfillment_status"] == "fulfilled"]
    
    total_sales = sum(o["total_price"] for o in valid_orders)
    num_orders = len(valid_orders)
    aov = total_sales / num_orders if num_orders > 0 else 0
    
    print("\n--- Sales Analytics Summary ---")
    print(f"  Total Confirmed Sales:     ${total_sales:.2f}")
    print(f"  Number of Paid/Fulfilled:  {num_orders}")
    print(f"  Average Order Value (AOV): ${aov:.2f}")
    print(f"  Total Orders Logged:       {len(orders)}")

def cmd_analytics_top_products(args):
    db = load_db()
    orders = db.get("orders", [])
    products_map = {p["id"]: p for p in db.get("products", [])}
    
    product_sales = {} # prod_id -> {qty, revenue}
    
    for o in orders:
        if o["financial_status"] == "refunded":
            continue
        for item in o["items"]:
            pid = item["product_id"]
            qty = item["quantity"]
            price = item["price"]
            
            if pid not in product_sales:
                product_sales[pid] = {"qty": 0, "revenue": 0.0}
            product_sales[pid]["qty"] += qty
            product_sales[pid]["revenue"] += qty * price
            
    headers = ["Product ID", "SKU", "Product Name", "Units Sold", "Revenue Generated"]
    rows = []
    
    sorted_sales = sorted(product_sales.items(), key=lambda x: x[1]["qty"], reverse=True)
    for pid, stats in sorted_sales:
        p = products_map.get(pid, {})
        rows.append([
            pid,
            p.get("sku", "N/A"),
            p.get("name", "Unknown"),
            stats["qty"],
            f"${stats['revenue']:.2f}"
        ])
        
    print("\n--- Top Selling Products ---")
    print_table(headers, rows)

def cmd_analytics_slow_inventory(args):
    db = load_db()
    products = db.get("products", [])
    inventory_map = {item["product_id"]: item["quantity"] for item in db.get("inventory", [])}
    orders = db.get("orders", [])
    
    # Calculate units sold per product
    sold_qty = {}
    for o in orders:
        if o["financial_status"] == "refunded":
            continue
        for item in o["items"]:
            pid = item["product_id"]
            sold_qty[pid] = sold_qty.get(pid, 0) + item["quantity"]
            
    headers = ["Product ID", "SKU", "Product Name", "Stock Level", "Units Sold", "Status"]
    rows = []
    
    # A slow-moving item has high inventory and low sales
    for p in products:
        pid = p["id"]
        stock = inventory_map.get(pid, 0)
        sold = sold_qty.get(pid, 0)
        
        # Criteria: stock > 30 and sold < 5
        if stock > 30 and sold < 5:
            status = "Slow Moving"
            rows.append([pid, p["sku"], p["name"], stock, sold, status])
            
    print("\n--- Slow-Moving Inventory Alert ---")
    print_table(headers, rows)

def cmd_notify(args):
    db = load_db()
    notifications = db.get("notifications", [])
    
    new_notif = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": args.message
    }
    notifications.append(new_notif)
    save_db(db)
    print(f"Logged Notification: {args.message}")

def main():
    parser = argparse.ArgumentParser(description="Shopify Agent Store CLI Tools")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results where applicable")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Products parser
    p_parser = subparsers.add_parser("products", help="Manage products catalog")
    p_sub = p_parser.add_subparsers(dest="subcommand", required=True)
    
    p_sub.add_parser("list", help="List all products")
    
    p_get = p_sub.add_parser("get", help="Get product details")
    p_get.add_argument("id", type=int, help="Product ID")
    
    p_upd = p_sub.add_parser("update", help="Update product details")
    p_upd.add_argument("id", type=int, help="Product ID")
    p_upd.add_argument("--price", type=float, help="New price")
    p_upd.add_argument("--description", type=str, help="New description")
    p_upd.add_argument("--name", type=str, help="New name")
    
    # Inventory parser
    i_parser = subparsers.add_parser("inventory", help="Manage inventory levels")
    i_sub = i_parser.add_subparsers(dest="subcommand", required=True)
    
    i_sub.add_parser("list", help="List inventory items")
    
    i_upd = i_sub.add_parser("update", help="Update inventory level by product ID or SKU")
    i_upd.add_argument("selector", type=str, help="Product ID or SKU")
    i_upd_group = i_upd.add_mutually_exclusive_group(required=True)
    i_upd_group.add_argument("--quantity", type=int, help="Set absolute quantity")
    i_upd_group.add_argument("--change", type=int, help="Relative change (positive/negative)")
    
    # Orders parser
    o_parser = subparsers.add_parser("orders", help="Manage customer orders")
    o_sub = o_parser.add_subparsers(dest="subcommand", required=True)
    
    o_sub.add_parser("list", help="List all orders")
    
    o_get = o_sub.add_parser("get", help="Get order details")
    o_get.add_argument("id", type=int, help="Order ID")
    
    o_upd = o_sub.add_parser("update", help="Update order status")
    o_upd.add_argument("id", type=int, help="Order ID")
    o_upd.add_argument("--financial_status", type=str, choices=["paid", "refunded", "partially_refunded", "pending"], help="Update financial status")
    o_upd.add_argument("--fulfillment_status", type=str, choices=["fulfilled", "unfulfilled", "cancelled"], help="Update fulfillment status")
    
    # Discounts parser
    d_parser = subparsers.add_parser("discounts", help="Manage discount codes")
    d_sub = d_parser.add_subparsers(dest="subcommand", required=True)
    
    d_sub.add_parser("list", help="List all discount codes")
    
    d_cre = d_sub.add_parser("create", help="Create a new discount code")
    d_cre.add_argument("code", type=str, help="Discount code")
    d_cre.add_argument("--type", type=str, choices=["percentage", "fixed_amount"], default="percentage", help="Discount type")
    d_cre.add_argument("--value", type=float, required=True, help="Discount value (percentage or amount)")
    
    d_upd = d_sub.add_parser("update", help="Update discount code status")
    d_upd.add_argument("code", type=str, help="Discount code")
    d_upd.add_argument("--status", type=str, choices=["active", "inactive"], required=True, help="Enable or disable code")
    
    # Analytics parser
    a_parser = subparsers.add_parser("analytics", help="Sales and stock analytics")
    a_sub = a_parser.add_subparsers(dest="subcommand", required=True)
    a_sub.add_parser("sales", help="Overall sales report")
    a_sub.add_parser("top-products", help="Top selling products")
    a_sub.add_parser("slow-inventory", help="Identify slow moving stock")
    
    # Notify parser
    n_parser = subparsers.add_parser("notify", help="Trigger a mock notification")
    n_parser.add_argument("--message", type=str, required=True, help="Notification content")
    
    # Dispatch
    args = parser.parse_args()
    
    try:
        if args.command == "products":
            if args.subcommand == "list":
                cmd_products_list(args)
            elif args.subcommand == "get":
                cmd_products_get(args)
            elif args.subcommand == "update":
                cmd_products_update(args)
        elif args.command == "inventory":
            if args.subcommand == "list":
                cmd_inventory_list(args)
            elif args.subcommand == "update":
                cmd_inventory_update(args)
        elif args.command == "orders":
            if args.subcommand == "list":
                cmd_orders_list(args)
            elif args.subcommand == "get":
                cmd_orders_get(args)
            elif args.subcommand == "update":
                cmd_orders_update(args)
        elif args.command == "discounts":
            if args.subcommand == "list":
                cmd_discounts_list(args)
            elif args.subcommand == "create":
                cmd_discounts_create(args)
            elif args.subcommand == "update":
                cmd_discounts_update(args)
        elif args.command == "analytics":
            if args.subcommand == "sales":
                cmd_analytics_sales(args)
            elif args.subcommand == "top-products":
                cmd_analytics_top_products(args)
            elif args.subcommand == "slow-inventory":
                cmd_analytics_slow_inventory(args)
        elif args.command == "notify":
            cmd_notify(args)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
