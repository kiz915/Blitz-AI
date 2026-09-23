"""
BizPilot AI - Data Model and DynamoDB Access Layer
Provides clean access methods for Customers, Orders, and Follow-up Tasks.
"""

import os
import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import boto3
from boto3.dynamodb.conditions import Key, Attr


def decimal_to_native(obj):
    """Recursively converts DynamoDB Decimal types to int or float for JSON compatibility."""
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj


def get_table(table_name_or_resource):
    """Returns a boto3 DynamoDB Table resource given either a name or an existing resource."""
    if isinstance(table_name_or_resource, str):
        dynamodb = boto3.resource('dynamodb')
        return dynamodb.Table(table_name_or_resource)
    return table_name_or_resource


# ==========================================
# CUSTOMER OPERATIONS
# ==========================================

def get_customer(customer_id, customers_table):
    """
    Retrieve customer by customer_id.
    """
    table = get_table(customers_table)
    response = table.get_item(Key={'customer_id': customer_id})
    item = response.get('Item')
    return decimal_to_native(item) if item else None


def list_customers(customers_table, limit=100):
    """
    List customers up to a limit.
    """
    table = get_table(customers_table)
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    return decimal_to_native(items)


def put_customer(customer_data, customers_table):
    """
    Store or update a customer record.
    """
    table = get_table(customers_table)
    # Ensure created_at exists
    if 'created_at' not in customer_data:
        customer_data['created_at'] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    table.put_item(Item=customer_data)
    return decimal_to_native(customer_data)


# ==========================================
# ORDER OPERATIONS
# ==========================================

def get_order(order_id, orders_table, customers_table=None):
    """
    Retrieve order details by order_id, optionally enriching with customer profile.
    """
    table = get_table(orders_table)
    response = table.get_item(Key={'order_id': order_id})
    order = response.get('Item')
    if not order:
        return None
    
    order = decimal_to_native(order)

    # Optional enrichment with customer information if available
    if customers_table and 'customer_id' in order:
        try:
            cust = get_customer(order['customer_id'], customers_table)
            if cust:
                order['customer_name'] = cust.get('name')
                order['customer_email'] = cust.get('email')
                order['customer_phone'] = cust.get('phone')
        except Exception as e:
            print(f"Warning: Failed to enrich order with customer info: {e}")

    return order


def search_orders_by_status(status, orders_table, customers_table=None):
    """
    Search orders by status using the GSI StatusIndex.
    Falls back to scan if index is still indexing or not present in local test.
    """
    table = get_table(orders_table)
    status_lower = status.lower().strip()
    
    try:
        response = table.query(
            IndexName='StatusIndex',
            KeyConditionExpression=Key('status').eq(status_lower)
        )
        items = response.get('Items', [])
    except Exception:
        # Fallback to scan with filter expression
        response = table.scan(
            FilterExpression=Attr('status').eq(status_lower)
        )
        items = response.get('Items', [])

    items = decimal_to_native(items)

    # Enrich with customer name if table provided
    if customers_table and items:
        for order in items:
            cid = order.get('customer_id')
            if cid:
                try:
                    c = get_customer(cid, customers_table)
                    if c:
                        order['customer_name'] = c.get('name')
                except Exception:
                    pass

    return items


def list_orders(orders_table, limit=100):
    """
    Scan all orders up to a limit.
    """
    table = get_table(orders_table)
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    return decimal_to_native(items)


def put_order(order_data, orders_table):
    """
    Store or update an order.
    """
    table = get_table(orders_table)
    # Ensure amount is Decimal or float/int
    item = dict(order_data)
    if 'amount' in item:
        item['amount'] = Decimal(str(item['amount']))
    table.put_item(Item=item)
    return decimal_to_native(item)


# ==========================================
# FOLLOW-UP TASK OPERATIONS
# ==========================================

def get_task(task_id, tasks_table):
    """
    Retrieve task by task_id.
    """
    table = get_table(tasks_table)
    response = table.get_item(Key={'task_id': task_id})
    item = response.get('Item')
    return decimal_to_native(item) if item else None


def create_followup_task(customer_id, order_id, description, priority, tasks_table, due_date=None, task_id=None):
    """
    Create a new follow-up task.
    """
    table = get_table(tasks_table)
    now = datetime.now(timezone.utc)
    
    if not task_id:
        task_id = f"TASK-{str(uuid.uuid4())[:6].upper()}"

    if not due_date:
        # Default due date to 24 hours later
        due_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    priority_normalized = priority.lower().strip()
    if priority_normalized not in ['high', 'medium', 'low']:
        priority_normalized = 'medium'

    task_item = {
        'task_id': task_id,
        'customer_id': customer_id.strip() if customer_id else '',
        'order_id': order_id.strip() if order_id else '',
        'description': description.strip(),
        'priority': priority_normalized,
        'status': 'pending',
        'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
        'due_date': due_date
    }

    table.put_item(Item=task_item)
    return task_item


def list_pending_tasks(tasks_table):
    """
    List all pending follow-up tasks.
    """
    table = get_table(tasks_table)
    try:
        response = table.query(
            IndexName='StatusIndex',
            KeyConditionExpression=Key('status').eq('pending')
        )
        items = response.get('Items', [])
    except Exception:
        response = table.scan(
            FilterExpression=Attr('status').eq('pending')
        )
        items = response.get('Items', [])

    # Sort high priority first
    priority_weights = {'high': 1, 'medium': 2, 'low': 3}
    items = decimal_to_native(items)
    items.sort(key=lambda t: priority_weights.get(t.get('priority', 'medium').lower(), 4))
    return items


def list_all_tasks(tasks_table, limit=100):
    """
    List all tasks.
    """
    table = get_table(tasks_table)
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    return decimal_to_native(items)


def complete_task(task_id, tasks_table):
    """
    Mark a task as completed.
    """
    table = get_table(tasks_table)
    
    # Check if task exists
    existing = get_task(task_id, table)
    if not existing:
        return None

    response = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression="SET #s = :completed, completed_at = :now",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':completed': 'completed',
            ':now': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        },
        ReturnValues="ALL_NEW"
    )
    return decimal_to_native(response.get('Attributes'))


# ==========================================
# BUSINESS SUMMARY AGGREGATION
# ==========================================

def get_business_summary(customers_table, orders_table, tasks_table):
    """
    Computes an operational summary of small business health:
    - Total Orders, status breakdown (delayed, pending, shipped, delivered, cancelled)
    - Total Customers
    - Pending Tasks (by priority: high, medium, low)
    - Actionable alerts (e.g., delayed orders needing follow-ups)
    """
    orders = list_orders(orders_table)
    customers = list_customers(customers_table)
    tasks = list_all_tasks(tasks_table)

    total_orders = len(orders)
    order_status_counts = {
        'pending': 0,
        'processing': 0,
        'shipped': 0,
        'delivered': 0,
        'delayed': 0,
        'cancelled': 0
    }
    
    delayed_orders_list = []
    total_revenue = 0.0

    for o in orders:
        st = o.get('status', '').lower()
        if st in order_status_counts:
            order_status_counts[st] += 1
        if st == 'delayed':
            delayed_orders_list.append({
                'order_id': o.get('order_id'),
                'customer_id': o.get('customer_id'),
                'product': o.get('product'),
                'amount': o.get('amount'),
                'expected_delivery': o.get('expected_delivery')
            })
        if st != 'cancelled':
            try:
                total_revenue += float(o.get('amount', 0))
            except (ValueError, TypeError):
                pass

    total_customers = len(customers)
    
    pending_tasks = [t for t in tasks if t.get('status') == 'pending']
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    
    high_priority_tasks = [t for t in pending_tasks if t.get('priority', '').lower() == 'high']
    medium_priority_tasks = [t for t in pending_tasks if t.get('priority', '').lower() == 'medium']
    low_priority_tasks = [t for t in pending_tasks if t.get('priority', '').lower() == 'low']

    return {
        'metrics': {
            'total_orders': total_orders,
            'delayed_orders': order_status_counts['delayed'],
            'pending_orders': order_status_counts['pending'],
            'processing_orders': order_status_counts['processing'],
            'shipped_orders': order_status_counts['shipped'],
            'delivered_orders': order_status_counts['delivered'],
            'cancelled_orders': order_status_counts['cancelled'],
            'total_customers': total_customers,
            'total_tasks': len(tasks),
            'pending_tasks_count': len(pending_tasks),
            'completed_tasks_count': len(completed_tasks),
            'high_priority_pending_tasks': len(high_priority_tasks),
            'estimated_pipeline_revenue': round(total_revenue, 2)
        },
        'delayed_orders': delayed_orders_list,
        'pending_tasks': pending_tasks,
        'status_breakdown': order_status_counts
    }
