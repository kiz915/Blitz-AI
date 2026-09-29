"""
Unit tests for BizPilot AI Bedrock Agent Operations Lambda Handler
Tests all 7 operations tools, parameter parsing, error handling, and response formatting.
"""

import sys
import os
import json
import pytest

# Ensure layers/model and agent/functions/operations are on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, 'layers', 'model'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'agent', 'functions', 'operations'))

import app as operations_handler
import model


# In-memory mock DynamoDB Table for unit testing
class MockDynamoDBTable:
    def __init__(self, initial_items=None):
        self.items = list(initial_items or [])

    def get_item(self, Key):
        k_name, k_val = list(Key.items())[0]
        for it in self.items:
            if it.get(k_name) == k_val:
                return {'Item': dict(it)}
        return {}

    def put_item(self, Item):
        k_name = list(Item.keys())[0]
        self.items = [i for i in self.items if i.get(k_name) != Item[k_name]]
        self.items.append(dict(Item))
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def scan(self, **kwargs):
        filtered = list(self.items)
        filter_expr = kwargs.get('FilterExpression')
        # Simple string attribute matching if filter provided
        return {'Items': filtered}

    def query(self, **kwargs):
        return {'Items': list(self.items)}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues, **kwargs):
        k_name, k_val = list(Key.items())[0]
        for it in self.items:
            if it.get(k_name) == k_val:
                it['status'] = ExpressionAttributeValues.get(':completed', 'completed')
                it['completed_at'] = ExpressionAttributeValues.get(':now', '2026-09-30')
                return {'Attributes': dict(it)}
        return {}


@pytest.fixture(autouse=True)
def setup_mock_db(monkeypatch):
    """Initializes mock tables and monkeypatches DynamoDB access in model.py"""
    customers_table = MockDynamoDBTable([
        {"customer_id": "CUST-001", "name": "Priya Sharma", "email": "priya.sharma@example.com", "phone": "+91 98765 43210"},
        {"customer_id": "CUST-002", "name": "Rajesh Patel", "email": "rajesh.patel@example.com", "phone": "+91 98234 56789"}
    ])

    orders_table = MockDynamoDBTable([
        {"order_id": "ORD-1001", "customer_id": "CUST-002", "product": "Ergonomic Office Chair", "amount": 8999, "status": "delivered", "order_date": "2026-09-18", "expected_delivery": "2026-09-22"},
        {"order_id": "ORD-1003", "customer_id": "CUST-001", "product": "Wireless Keyboard", "amount": 2499, "status": "delayed", "order_date": "2026-09-20", "expected_delivery": "2026-09-24"}
    ])

    tasks_table = MockDynamoDBTable([
        {"task_id": "TASK-001", "customer_id": "CUST-001", "order_id": "ORD-1003", "description": "Follow up with Priya about delayed order ORD-1003", "priority": "high", "status": "pending", "due_date": "2026-09-26"}
    ])

    def mock_get_table(table_name_or_resource):
        if isinstance(table_name_or_resource, MockDynamoDBTable):
            return table_name_or_resource
        t_name = str(table_name_or_resource).lower()
        if "customer" in t_name:
            return customers_table
        elif "order" in t_name:
            return orders_table
        elif "task" in t_name:
            return tasks_table
        return MockDynamoDBTable()

    monkeypatch.setattr(model, "get_table", mock_get_table)
    return {"customers": customers_table, "orders": orders_table, "tasks": tasks_table}


# ==========================================
# TOOL TESTS
# ==========================================

def test_get_order_success():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "get_order",
        "parameters": [{"name": "order_id", "type": "string", "value": "ORD-1003"}]
    }
    response = operations_handler.lambda_handler(event, None)
    assert response["messageVersion"] == "1.0"
    assert response["response"]["function"] == "get_order"
    
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "ORD-1003" in body_text
    assert "DELAYED" in body_text
    assert "Wireless Keyboard" in body_text


def test_get_order_not_found():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "get_order",
        "parameters": [{"name": "order_id", "type": "string", "value": "ORD-9999"}]
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "was not found" in body_text


def test_get_customer_success():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "get_customer",
        "parameters": [{"name": "customer_id", "type": "string", "value": "CUST-001"}]
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "Priya Sharma" in body_text
    assert "priya.sharma@example.com" in body_text


def test_search_orders_delayed():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "search_orders",
        "parameters": [{"name": "status", "type": "string", "value": "delayed"}]
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "delayed" in body_text.lower()
    assert "ORD-1003" in body_text


def test_create_followup_task():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "create_followup_task",
        "parameters": [
            {"name": "customer_id", "type": "string", "value": "CUST-001"},
            {"name": "order_id", "type": "string", "value": "ORD-1003"},
            {"name": "description", "type": "string", "value": "Call customer regarding revised shipment"},
            {"name": "priority", "type": "string", "value": "high"}
        ]
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "TASK-" in body_text
    assert "HIGH" in body_text
    assert "Call customer" in body_text


def test_list_pending_tasks():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "list_pending_tasks",
        "parameters": []
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "pending task" in body_text
    assert "TASK-001" in body_text


def test_complete_task():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "complete_task",
        "parameters": [{"name": "task_id", "type": "string", "value": "TASK-001"}]
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "TASK-001" in body_text
    assert "COMPLETED" in body_text


def test_get_business_summary():
    event = {
        "messageVersion": "1.0",
        "actionGroup": "BizPilotOperationsTools",
        "function": "get_business_summary",
        "parameters": []
    }
    response = operations_handler.lambda_handler(event, None)
    body_text = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "BizPilot Operational Summary" in body_text
    assert "Total Orders" in body_text
    assert "Active Customers" in body_text


def test_direct_api_invocation():
    event = {
        "action": "get_order",
        "parameters": {"order_id": "ORD-1003"}
    }
    response = operations_handler.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["status"] == "success"
    assert body["result"]["order"]["order_id"] == "ORD-1003"
