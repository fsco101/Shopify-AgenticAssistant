# Universal Agentic Shopify Assistant Setup

This workspace is configured with a fully mockable Shopify Store environment designed for autonomous agent operations.

## Setup Components

1. **Agent Customization Rules (`.agents/AGENTS.md`)**:
   - Contains the core instruction prompt for the Universal Agentic Shopify Assistant.
   - Instructs the AI agent to operate autonomously, plan multi-step operations, recovery from tool errors, and follow Shopify management guidelines.
2. **Mock Database (`db.json`)**:
   - Stores current state of the Shopify store:
     - **Products**: ID, SKU, Name, Description, Price, and Creation date.
     - **Inventory**: Location-based inventory tracking matching product IDs.
     - **Orders**: Full customer orders (line items, pricing, payment status, fulfillment status, and order history).
     - **Discounts**: Store discount codes, usage count, discount type, value, and activation status.
     - **Notifications**: System notification log for campaign updates and alerts.
3. **Shopify CLI Tool (`shopify.py`)**:
   - A unified Python-based utility that acts as the toolset for the agent.
   - Supports subcommands for products, inventory, orders, discounts, notifications, and analytics.

## Repository Files & Functions

Here is a list of all files in this workspace, their functions, and descriptions of their purposes.

### Core Application Files

1. **[shopify_api.py](file:///c:/Shopify-AgenticAssistant/shopify_api.py)**: Contains the core backend interface for interacting with the mock Shopify store. It exposes CRUD operations and analytical tools, reading/writing to the local database file.
   * **Key Functions**:
     * [list_products](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L24): Lists all products.
     * [get_product](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L28): Retrieves details for a specific product ID including its stock and location.
     * [update_product](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L39): Updates a product's name, price, or description.
     * [list_inventory](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L54): Lists inventory items.
     * [update_inventory](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L58): Adjusts stock levels (absolute or relative change) for a product (via ID/SKU).
     * [list_orders](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L90): Retrieves all customer orders.
     * [get_order](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L94): Retrieves details for a specific order.
     * [update_order](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L101): Modifies the payment or fulfillment status of an order.
     * [list_discounts](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L117): Lists existing discount codes.
     * [create_discount](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L121): Generates a new discount code.
     * [update_discount](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L140): Activates or deactivates a discount code.
     * [analytics_sales](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L155): Computes total sales, order count, and average order value.
     * [analytics_top_products](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L170): Identifies the best-selling products by quantity and revenue.
     * [analytics_slow_inventory](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L185): Highlights items with low sales velocity and high inventory.
     * [log_notification](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L209): Logs system notifications for marketing or alerts.
     * [create_landing_page](file:///c:/Shopify-AgenticAssistant/shopify_api.py#L221): Publishes a promotional or content landing page.

2. **[shopify.py](file:///c:/Shopify-AgenticAssistant/shopify.py)**: A comprehensive CLI utility for executing Shopify commands directly from the terminal. Useful for manual verification and triggering admin commands.
   * **Subcommands**:
     * `products` (`list`, `get`, `update`)
     * `inventory` (`list`, `update`)
     * `orders` (`list`, `get`, `update`)
     * `discounts` (`list`, `create`, `update`)
     * `analytics` (`sales`, `top-products`, `slow-inventory`)
     * `notify`

3. **[chat_ui.py](file:///c:/Shopify-AgenticAssistant/chat_ui.py)**: A graphical chat interface written using standard library `tkinter`. It allows you to text the assistant, view tool executions in real-time, inspect past chat histories, and verify database connections.
   * **Key Components**:
     * [AgentChatWindow](file:///c:/Shopify-AgenticAssistant/chat_ui.py#L9): Class responsible for UI layout, background threads, and loading/saving history.
     * [process_agent_response](file:///c:/Shopify-AgenticAssistant/chat_ui.py#L155): Coordinates message processing asynchronously with the LLM router.

4. **[llm_router.py](file:///c:/Shopify-AgenticAssistant/llm_router.py)**: Manages interactions with LLM models via `litellm`. It reads the schemas, feeds them to the LLM completion API, parses tool calls dynamically in a recursive loop, and updates the conversation history.
   * **Key Functions**:
     * [process_agent_message](file:///c:/Shopify-AgenticAssistant/llm_router.py#L46): Processes current chat history with the LLM and runs tool call sequences.

5. **[history_manager.py](file:///c:/Shopify-AgenticAssistant/history_manager.py)**: Handles conversation storage, querying, and updating. It connects to a MongoDB database if available or gracefully falls back to local storage in `chat_history.json`.
   * **Key Functions**:
     * [save_message](file:///c:/Shopify-AgenticAssistant/history_manager.py#L76): Appends a message to a chat session.
     * [save_full_session](file:///c:/Shopify-AgenticAssistant/history_manager.py#L120): Writes/updates the entire conversation logs at once.

### Simulation and Data Files

6. **[agent_loop.py](file:///c:/Shopify-AgenticAssistant/agent_loop.py)**: A mock terminal simulation that mimics how an autonomous LLM decides to call tools (e.g. identifying slow inventory and sending a notification) in a loop, displaying structured input/output logs.

7. **[agent_tools.json](file:///c:/Shopify-AgenticAssistant/agent_tools.json)**: A JSON schema declaring all function formats, descriptions, and arguments exposed to the LLM agent.

8. **[db.json](file:///c:/Shopify-AgenticAssistant/db.json)**: The database file storing state for products, inventory, orders, discounts, and notifications.

### Configuration and Infrastructure

9. **[AGENTS.md](file:///c:/Shopify-AgenticAssistant/.agents/AGENTS.md)**: Rules and instruction guidelines guiding the autonomous agent behavior.

10. **[.env](file:///c:/Shopify-AgenticAssistant/.env)**: Store credentials, database URIs, API keys, and configurations.

11. **[requirements.txt](file:///c:/Shopify-AgenticAssistant/requirements.txt)**: Specifies package requirements (`litellm`, `python-dotenv`, `pymongo`).

12. **[.gitignore](file:///c:/Shopify-AgenticAssistant/.gitignore)**: Standard Git ignore configuration.

---

## Tool CLI Usage Guide

All tools can be run from the terminal using `python shopify.py`. Output can be formatted as a standard printout or as raw JSON by prefixing the command with `--json`.

### 1. Products Management
* **List Products**:
  ```bash
  python shopify.py products list
  ```
* **Get Specific Product Details**:
  ```bash
  python shopify.py products get <product_id>
  ```
* **Update Product Details**:
  ```bash
  python shopify.py products update <product_id> --price <new_price> --description "<new_description>" --name "<new_name>"
  ```

### 2. Inventory Management
* **List Inventory**:
  ```bash
  python shopify.py inventory list
  ```
* **Update Stock Levels** (Supports selection by Product ID or SKU):
  ```bash
  # Set absolute stock level
  python shopify.py inventory update <id_or_sku> --quantity <qty>
  
  # Change relative stock level (add or subtract)
  python shopify.py inventory update <id_or_sku> --change <relative_qty>
  ```

### 3. Orders Management
* **List Orders**:
  ```bash
  python shopify.py orders list
  ```
* **Get Specific Order**:
  ```bash
  python shopify.py orders get <order_id>
  ```
* **Update Order Status**:
  ```bash
  python shopify.py orders update <order_id> --financial_status <paid|refunded|partially_refunded|pending> --fulfillment_status <fulfilled|unfulfilled|cancelled>
  ```

### 4. Discount Code Management
* **List Discount Codes**:
  ```bash
  python shopify.py discounts list
  ```
* **Create Discount Code**:
  ```bash
  python shopify.py discounts create <CODE> --type <percentage|fixed_amount> --value <value>
  ```
* **Activate/Deactivate Discount Code**:
  ```bash
  python shopify.py discounts update <CODE> --status <active|inactive>
  ```

### 5. Analytics Subsystem
* **Overall Sales Summary** (Calculates total sales, order count, and Average Order Value):
  ```bash
  python shopify.py analytics sales
  ```
* **Top Selling Products** (Calculates units sold and total revenue per product):
  ```bash
  python shopify.py analytics top-products
  ```
* **Slow-moving Inventory Alert** (Identifies products with stock level > 30 and units sold < 5):
  ```bash
  python shopify.py analytics slow-inventory
  ```

### 6. Notification Logger
* **Create/Send Log Notification**:
  ```bash
  python shopify.py notify --message "<notification_message>"
  ```

---

## Dynamic Verification Examples

You can combine commands dynamically to perform agentic operations.

**Example 1: Restocking Low Stock Products**
1. Check inventory status:
   ```bash
   python shopify.py inventory list
   ```
2. Locate items marked `LOW STOCK` or `OUT OF STOCK`.
3. Increase stock:
   ```bash
   python shopify.py inventory update 2 --quantity 50
   ```

**Example 2: Preparing a Weekend Sale**
1. Identify slow-moving items:
   ```bash
   python shopify.py analytics slow-inventory
   ```
2. Generate and create a new promotional code:
   ```bash
   python shopify.py discounts create WEEKEND30 --value 30
   ```
3. Update product descriptions of slow-moving items to mention the sale:
   ```bash
   python shopify.py products update 6 --description "Sleek Minimalist Leather Wallet - Now 30% off this weekend with code WEEKEND30!"
   ```