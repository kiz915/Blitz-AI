"""
BizPilot AI - Bedrock Agent Operations Lambda Handler
Implements the 7 core operations tools for small business management:
- get_order(order_id)
- get_customer(customer_id)
- search_orders(status)
- create_followup_task(customer_id, order_id, description, priority)
- list_pending_tasks()
- complete_task(task_id)
- get_business_summary()
"""

import os
import json
import logging
from datetime import datetime, timezone

# Import data layer methods
from model import (
    get_customer as db_get_customer,
    list_customers as db_list_customers,
    get_order as db_get_order,
    search_orders_by_status as db_search_orders,
    list_orders as db_list_orders,
    create_followup_task as db_create_task,
    list_pending_tasks as db_list_pending_tasks,
    complete_task as db_complete_task,
    get_business_summary as db_get_summary,
    get_task as db_get_task
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Table configuration from environment variables with fallbacks
CUSTOMERS_TABLE = os.environ.get("CUSTOMERS_TABLE", "BizPilot-Customers-dev")
ORDERS_TABLE = os.environ.get("ORDERS_TABLE", "BizPilot-Orders-dev")
TASKS_TABLE = os.environ.get("TASKS_TABLE", "BizPilot-Tasks-dev")


def parse_parameters(parameters_list):
    """
    Normalizes Bedrock Agent parameters array into a clean dictionary.
    Parameters format: [{'name': 'order_id', 'type': 'string', 'value': 'ORD-1003'}, ...]
    """
    params = {}
    if isinstance(parameters_list, list):
        for item in parameters_list:
            if isinstance(item, dict) and 'name' in item:
                params[item['name']] = item.get('value')
    elif isinstance(parameters_list, dict):
        params = parameters_list
    return params


# ==========================================
# TOOL IMPLEMENTATIONS
# ==========================================

def handle_get_order(params):
    order_id = params.get('order_id')
    if not order_id:
        return {"error": "Missing required parameter: order_id"}
    
    order_id = order_id.strip()
    order = db_get_order(order_id, ORDERS_TABLE, CUSTOMERS_TABLE)
    
    if not order:
        return {
            "status": "not_found",
            "message": f"Order {order_id} was not found in the database. Please verify the order ID."
        }
    
    customer_info = f" for customer {order.get('customer_name', order.get('customer_id'))}" if order.get('customer_id') else ""
    return {
        "status": "success",
        "order": order,
        "message": f"Order {order['order_id']} is currently {order['status'].upper()}{customer_info}. Product: {order.get('product')}, Amount: ₹{order.get('amount')}, Ordered on: {order.get('order_date')}, Expected delivery: {order.get('expected_delivery')}."
    }


def handle_get_customer(params):
    customer_id = params.get('customer_id')
    if not customer_id:
        return {"error": "Missing required parameter: customer_id"}
    
    customer_id = customer_id.strip()
    customer = db_get_customer(customer_id, CUSTOMERS_TABLE)
    
    if not customer:
        return {
            "status": "not_found",
            "message": f"Customer {customer_id} does not exist in the database."
        }
    
    # Also find customer's orders
    all_orders = db_list_orders(ORDERS_TABLE)
    cust_orders = [o for o in all_orders if o.get('customer_id') == customer_id]
    customer['orders'] = cust_orders
    customer['orders_count'] = len(cust_orders)
    
    orders_summary = f"{len(cust_orders)} associated orders" if cust_orders else "no orders yet"
    return {
        "status": "success",
        "customer": customer,
        "message": f"Customer {customer['name']} ({customer['customer_id']}): Email: {customer.get('email')}, Phone: {customer.get('phone')}. Has {orders_summary}."
    }


def handle_search_orders(params):
    status = params.get('status')
    if not status:
        return {"error": "Missing required parameter: status (e.g. pending, delayed, shipped, delivered)"}
    
    status_clean = status.strip().lower()
    orders = db_search_orders(status_clean, ORDERS_TABLE, CUSTOMERS_TABLE)
    
    if not orders:
        return {
            "status": "success",
            "count": 0,
            "orders": [],
            "message": f"No orders found with status '{status_clean}'."
        }
    
    order_lines = []
    for o in orders:
        cust_name = o.get('customer_name', o.get('customer_id', 'Unknown'))
        order_lines.append(f"- {o['order_id']}: {o.get('product')} (₹{o.get('amount')}) - Customer: {cust_name}, Expected: {o.get('expected_delivery')}")

    summary_text = f"Found {len(orders)} order(s) with status '{status_clean}':\n" + "\n".join(order_lines)
    return {
        "status": "success",
        "count": len(orders),
        "orders": orders,
        "message": summary_text
    }


def handle_create_followup_task(params):
    customer_id = params.get('customer_id', '').strip()
    order_id = params.get('order_id', '').strip()
    description = params.get('description', '').strip()
    priority = params.get('priority', 'medium').strip().lower()

    # If customer_id missing but order_id provided, look up customer_id from order
    if not customer_id and order_id:
        order = db_get_order(order_id, ORDERS_TABLE)
        if order and 'customer_id' in order:
            customer_id = order['customer_id']

    # If description missing, generate default description
    if not description:
        if order_id:
            description = f"Follow up regarding order {order_id}"
        elif customer_id:
            description = f"Customer follow-up for {customer_id}"
        else:
            description = "General operational follow-up task"

    if priority not in ['high', 'medium', 'low']:
        priority = 'medium'

    task = db_create_task(
        customer_id=customer_id,
        order_id=order_id,
        description=description,
        priority=priority,
        tasks_table=TASKS_TABLE
    )

    cust_mention = f" for customer {customer_id}" if customer_id else ""
    order_mention = f" regarding {order_id}" if order_id else ""
    
    return {
        "status": "success",
        "task": task,
        "message": f"Created {task['task_id']} as a {priority.upper()}-priority follow-up task{cust_mention}{order_mention}. Description: '{description}'. Due date: {task['due_date']}."
    }


def handle_list_pending_tasks(params):
    tasks = db_list_pending_tasks(TASKS_TABLE)
    
    if not tasks:
        return {
            "status": "success",
            "count": 0,
            "tasks": [],
            "message": "There are currently no pending tasks. Operations are fully up to date!"
        }
    
    task_lines = []
    for t in tasks:
        task_lines.append(f"- [{t.get('priority', 'medium').upper()}] {t['task_id']}: {t.get('description')} (Due: {t.get('due_date', 'N/A')}, Customer: {t.get('customer_id', 'N/A')}, Order: {t.get('order_id', 'N/A')})")

    summary_text = f"Found {len(tasks)} pending task(s):\n" + "\n".join(task_lines)
    return {
        "status": "success",
        "count": len(tasks),
        "tasks": tasks,
        "message": summary_text
    }


def handle_complete_task(params):
    task_id = params.get('task_id')
    if not task_id:
        return {"error": "Missing required parameter: task_id"}
    
    task_id = task_id.strip()
    updated = db_complete_task(task_id, TASKS_TABLE)
    
    if not updated:
        return {
            "status": "not_found",
            "message": f"Task {task_id} was not found. Please check the task ID."
        }
    
    return {
        "status": "success",
        "task": updated,
        "message": f"Successfully marked task {task_id} ('{updated.get('description')}') as COMPLETED."
    }


def handle_get_business_summary(params):
    summary = db_get_summary(CUSTOMERS_TABLE, ORDERS_TABLE, TASKS_TABLE)
    metrics = summary['metrics']
    
    delayed_details = ""
    if summary['delayed_orders']:
        delayed_lines = [f"- {d['order_id']} ({d['product']}, ₹{d['amount']}) Expected: {d['expected_delivery']}" for d in summary['delayed_orders']]
        delayed_details = "\nDelayed Orders Requiring Action:\n" + "\n".join(delayed_lines)

    summary_text = (
        f"BizPilot Operational Summary:\n"
        f"• Total Orders: {metrics['total_orders']} "
        f"({metrics['delayed_orders']} delayed, {metrics['pending_orders']} pending, {metrics['shipped_orders']} shipped, {metrics['delivered_orders']} delivered)\n"
        f"• Active Customers: {metrics['total_customers']}\n"
        f"• Follow-up Tasks: {metrics['pending_tasks_count']} pending ({metrics['high_priority_pending_tasks']} HIGH priority), {metrics['completed_tasks_count']} completed\n"
        f"• Pipeline Revenue: ₹{metrics['estimated_pipeline_revenue']:,.2f}\n"
        f"{delayed_details}"
    )

    return {
        "status": "success",
        "summary": summary,
        "message": summary_text
    }


# Tool Dispatcher Map
TOOL_DISPATCHER = {
    'get_order': handle_get_order,
    'get_customer': handle_get_customer,
    'search_orders': handle_search_orders,
    'create_followup_task': handle_create_followup_task,
    'list_pending_tasks': handle_list_pending_tasks,
    'complete_task': handle_complete_task,
    'get_business_summary': handle_get_business_summary,
}


# ==========================================
# MAIN LAMBDA HANDLER
# ==========================================

def lambda_handler(event, context):
    """
    Main entry point for Amazon Bedrock Agent action group requests and direct invocations.
    """
    logger.info(f"Incoming event: {json.dumps(event)}")
    
    # 1. Determine function/tool name and parameters
    action_group = event.get('actionGroup', 'BizPilotOperationsTools')
    function_name = event.get('function') or event.get('action')
    message_version = event.get('messageVersion', '1.0')
    
    # If Bedrock Agent event structure
    if 'parameters' in event:
        raw_params = event.get('parameters', [])
        params = parse_parameters(raw_params)
    elif 'body' in event and isinstance(event['body'], str):
        try:
            body = json.loads(event['body'])
            function_name = function_name or body.get('function') or body.get('action')
            params = body.get('parameters', body)
        except Exception:
            params = {}
    else:
        params = event.get('parameters', event)

    # 2. Dispatch to matching tool
    if function_name in TOOL_DISPATCHER:
        try:
            result = TOOL_DISPATCHER[function_name](params)
            response_text = result.get('message', json.dumps(result))
            status_code = 200
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}", exc_info=True)
            result = {"status": "error", "error": str(e)}
            response_text = f"An error occurred while executing {function_name}: {str(e)}"
            status_code = 500
    else:
        valid_tools = list(TOOL_DISPATCHER.keys())
        result = {
            "status": "unknown_function",
            "error": f"Function '{function_name}' is not recognized. Valid tools: {valid_tools}"
        }
        response_text = result['error']
        status_code = 400

    # 3. Check if caller is Bedrock Agent or direct API/Gateway
    is_bedrock_agent = 'actionGroup' in event or 'messageVersion' in event
    
    if is_bedrock_agent:
        # Standard Amazon Bedrock Agent response structure
        bedrock_response = {
            'messageVersion': message_version,
            'response': {
                'actionGroup': action_group,
                'function': function_name,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': response_text
                        }
                    }
                }
            }
        }
        logger.info(f"Bedrock Agent response: {json.dumps(bedrock_response)}")
        return bedrock_response
    else:
        # Direct API response
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                'result': result,
                'message': response_text
            })
        }
