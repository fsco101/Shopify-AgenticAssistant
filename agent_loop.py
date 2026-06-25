import json
import shopify_api

# 1. Load the schemas that you will pass to your LLM API (OpenAI/Gemini)
def load_schemas():
    with open("agent_tools.json", "r") as f:
        return json.load(f)

# 2. Dispatch map linking LLM function names to our local Python module
TOOL_DISPATCHER = {
    "list_products": shopify_api.list_products,
    "get_product": shopify_api.get_product,
    "update_product": shopify_api.update_product,
    "list_inventory": shopify_api.list_inventory,
    "update_inventory": shopify_api.update_inventory,
    "list_orders": shopify_api.list_orders,
    "update_order": shopify_api.update_order,
    "create_discount": shopify_api.create_discount,
    "analytics_sales": shopify_api.analytics_sales,
    "analytics_slow_inventory": shopify_api.analytics_slow_inventory,
    "log_notification": shopify_api.log_notification
}

def execute_tool_call(function_name, arguments_dict):
    """Executes the mapped python function and returns the JSON serializable result."""
    if function_name in TOOL_DISPATCHER:
        func = TOOL_DISPATCHER[function_name]
        try:
            return func(**arguments_dict)
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"Function {function_name} not implemented"}

def run_agent_simulation():
    print("--- Shopify Agent Execution Loop Simulation ---")
    schemas = load_schemas()
    print(f"Loaded {len(schemas)} tools into the Agent context.")
    
    # ---------------------------------------------------------
    # In a real app, you would:
    # 1. Send the user prompt + schemas to your LLM API
    # 2. The LLM decides it needs to call a tool to answer the user
    # 3. The LLM returns a ToolCall request with a function name and arguments
    # ---------------------------------------------------------
    
    print("\n[User Prompt]: 'Please check if we have any slow moving inventory, and if so, log a notification.'")
    print("[System]: Sending prompt and tools to LLM...")
    
    # Simulating LLM returning a tool call:
    llm_tool_call_1 = {
        "function_name": "analytics_slow_inventory",
        "arguments": {}
    }
    print(f"\n[LLM Decision]: Call tool -> {llm_tool_call_1['function_name']}")
    
    # 4. We execute the local Python code based on the LLM request
    result_1 = execute_tool_call(llm_tool_call_1["function_name"], llm_tool_call_1["arguments"])
    print(f"[Tool Response]: {json.dumps(result_1, indent=2)}")
    
    # Simulating LLM returning the second tool call to log the notification
    llm_tool_call_2 = {
        "function_name": "log_notification",
        "arguments": {
            "message": f"Found {len(result_1)} slow moving products. Need to create a discount."
        }
    }
    print(f"\n[LLM Decision]: Call tool -> {llm_tool_call_2['function_name']}")
    
    result_2 = execute_tool_call(llm_tool_call_2["function_name"], llm_tool_call_2["arguments"])
    print(f"[Tool Response]: {json.dumps(result_2, indent=2)}")
    
    print("\n[LLM Final Response to User]: 'I checked your store and found some slow moving items. I have logged an alert to the system.'")

if __name__ == "__main__":
    run_agent_simulation()
