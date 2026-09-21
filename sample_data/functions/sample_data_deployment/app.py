"""
BizPilot AI - Sample Data & Seeding Custom Resource Lambda
Seeds realistic small business demo data for Customers, Orders, and Tasks,
uploads business SOP documents to S3, and prepares the Bedrock Agent.
"""

import os
import json
import logging
import boto3
import cfnresponse

from model import put_customer, put_order, create_followup_task

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Realistic Small Business Demo Dataset
SAMPLE_CUSTOMERS = [
    {
        "customer_id": "CUST-001",
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+91 98765 43210",
        "created_at": "2026-09-01"
    },
    {
        "customer_id": "CUST-002",
        "name": "Rajesh Patel",
        "email": "rajesh.patel@example.com",
        "phone": "+91 98234 56789",
        "created_at": "2026-09-05"
    },
    {
        "customer_id": "CUST-003",
        "name": "Anita Roy",
        "email": "anita.roy@example.com",
        "phone": "+91 97123 45678",
        "created_at": "2026-09-10"
    },
    {
        "customer_id": "CUST-004",
        "name": "Vikram Malhotra",
        "email": "vikram.m@example.com",
        "phone": "+91 96543 21098",
        "created_at": "2026-09-12"
    },
    {
        "customer_id": "CUST-005",
        "name": "Sneha Kulkarni",
        "email": "sneha.k@example.com",
        "phone": "+91 95432 10987",
        "created_at": "2026-09-15"
    }
]

SAMPLE_ORDERS = [
    {
        "order_id": "ORD-1001",
        "customer_id": "CUST-002",
        "product": "Ergonomic Office Chair",
        "amount": 8999,
        "status": "delivered",
        "order_date": "2026-09-18",
        "expected_delivery": "2026-09-22"
    },
    {
        "order_id": "ORD-1002",
        "customer_id": "CUST-003",
        "product": "USB-C Multiport Dock",
        "amount": 3499,
        "status": "shipped",
        "order_date": "2026-09-25",
        "expected_delivery": "2026-10-02"
    },
    {
        "order_id": "ORD-1003",
        "customer_id": "CUST-001",
        "product": "Wireless Keyboard",
        "amount": 2499,
        "status": "delayed",
        "order_date": "2026-09-20",
        "expected_delivery": "2026-09-24"
    },
    {
        "order_id": "ORD-1004",
        "customer_id": "CUST-004",
        "product": "4K Ultra-HD Monitor 27-inch",
        "amount": 24999,
        "status": "delayed",
        "order_date": "2026-09-21",
        "expected_delivery": "2026-09-26"
    },
    {
        "order_id": "ORD-1005",
        "customer_id": "CUST-005",
        "product": "Noise Cancelling Headphones",
        "amount": 5999,
        "status": "pending",
        "order_date": "2026-09-29",
        "expected_delivery": "2026-10-04"
    },
    {
        "order_id": "ORD-1006",
        "customer_id": "CUST-001",
        "product": "Aluminum Laptop Stand",
        "amount": 1299,
        "status": "processing",
        "order_date": "2026-09-28",
        "expected_delivery": "2026-10-03"
    },
    {
        "order_id": "ORD-1007",
        "customer_id": "CUST-003",
        "product": "Blue-light Blocking Glasses",
        "amount": 799,
        "status": "cancelled",
        "order_date": "2026-09-15",
        "expected_delivery": "2026-09-19"
    }
]

SAMPLE_TASKS = [
    {
        "task_id": "TASK-001",
        "customer_id": "CUST-001",
        "order_id": "ORD-1003",
        "description": "Follow up with Priya about delayed order ORD-1003",
        "priority": "high",
        "due_date": "2026-09-26"
    },
    {
        "task_id": "TASK-002",
        "customer_id": "CUST-004",
        "order_id": "ORD-1004",
        "description": "Check logistics courier status for Vikram's monitor",
        "priority": "medium",
        "due_date": "2026-09-28"
    },
    {
        "task_id": "TASK-003",
        "customer_id": "CUST-002",
        "order_id": "ORD-1001",
        "description": "Send delivery satisfaction survey to Rajesh",
        "priority": "low",
        "due_date": "2026-09-24"
    }
]


def seed_dynamodb(customers_table, orders_table, tasks_table):
    logger.info("Seeding customers into DynamoDB...")
    for c in SAMPLE_CUSTOMERS:
        put_customer(c, customers_table)

    logger.info("Seeding orders into DynamoDB...")
    for o in SAMPLE_ORDERS:
        put_order(o, orders_table)

    logger.info("Seeding tasks into DynamoDB...")
    for t in SAMPLE_TASKS:
        create_followup_task(
            customer_id=t['customer_id'],
            order_id=t['order_id'],
            description=t['description'],
            priority=t['priority'],
            tasks_table=tasks_table,
            due_date=t['due_date'],
            task_id=t['task_id']
        )
    logger.info("DynamoDB seeding complete.")


def upload_sops_to_s3(bucket_name):
    if not bucket_name:
        return
    logger.info(f"Uploading business documents/SOPs to S3 bucket: {bucket_name}")
    s3 = boto3.client('s3')
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
        files = [f for f in os.listdir(assets_dir) if os.path.isfile(os.path.join(assets_dir, f))]
        for f in files:
            file_path = os.path.join(assets_dir, f)
            logger.info(f"Uploading {f} to {bucket_name}...")
            s3.upload_file(file_path, bucket_name, f"sops/{f}")
    logger.info("S3 upload complete.")


def prepare_bedrock_agent(agent_id):
    if not agent_id:
        return
    try:
        logger.info(f"Preparing Bedrock Agent: {agent_id}")
        bedrock_agent = boto3.client('bedrock-agent')
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"Bedrock Agent prepare response: {response}")
    except Exception as e:
        logger.warning(f"Could not prepare agent automatically: {e}")


def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    request_type = event.get('RequestType', 'Create')
    props = event.get('ResourceProperties', {})
    
    customers_table = props.get('customers_table')
    orders_table = props.get('orders_table')
    tasks_table = props.get('tasks_table')
    s3_bucket = props.get('s3_bucket')
    agent_id = props.get('agent_id')

    physical_id = f"BizPilot-SampleData-{request_type}"

    if request_type in ['Create', 'Update']:
        try:
            if customers_table and orders_table and tasks_table:
                seed_dynamodb(customers_table, orders_table, tasks_table)
            
            if s3_bucket:
                upload_sops_to_s3(s3_bucket)

            if agent_id:
                prepare_bedrock_agent(agent_id)

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"status": "SUCCESS"}, physical_id)
        except Exception as e:
            logger.error(f"Error seeding data: {e}", exc_info=True)
            cfnresponse.send(event, context, cfnresponse.FAILED, {"error": str(e)}, physical_id)
    else:
        # On Delete, simply return SUCCESS
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"status": "DELETED"}, physical_id)
