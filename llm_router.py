import os
import json
from dotenv import load_dotenv
import litellm
import shopify_api

load_dotenv()

# Read default model from .env, fallback to gpt-4o if not set
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")

# Load tools schema
with open("agent_tools.json", "r", encoding="utf-8") as f:
    TOOLS_SCHEMA = json.load(f)

# Load System Prompt
with open(".agents/AGENTS.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Re-use dispatcher from earlier
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
    "log_notification": shopify_api.log_notification,
    "create_landing_page": shopify_api.create_landing_page
}

def execute_tool_call(function_name, arguments_dict):
    if function_name in TOOL_DISPATCHER:
        func = TOOL_DISPATCHER[function_name]
        try:
            return func(**arguments_dict)
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"Function {function_name} not implemented"}

def process_agent_message(messages):
    """
    Given a conversation history (list of dicts), queries the LLM using LiteLLM.
    Handles tool calls automatically in a loop.
    Returns the final LLM string response and the updated message history.
    """
    # Ensure system prompt is first
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        
    try:
        response = litellm.completion(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        messages.append(response_message.model_dump(exclude_none=True))
        
        # Check if the LLM wanted to call any tools
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"[System] LLM triggered tool: {function_name}")
                result = execute_tool_call(function_name, arguments)
                
                # Append the tool result to the conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result)
                })
                
            # Recurse: ask LLM to synthesize final response after seeing tool results
            return process_agent_message(messages)
            
        return response_message.content, messages
        
    except Exception as e:
        error_msg = f"Error communicating with LLM: {str(e)}\n\nMake sure your API key is correctly set in .env for model '{DEFAULT_MODEL}'."
        print(f"[System Error] {error_msg}")
        return error_msg, messages
