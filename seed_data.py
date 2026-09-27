"""
BizPilot AI - Standalone Demo Data Seeder CLI
Run this script to seed realistic demo data into AWS DynamoDB or local DynamoDB tables.

Usage:
  python seed_data.py --env dev
  python seed_data.py --customers-table BizPilot-Customers-dev --orders-table BizPilot-Orders-dev --tasks-table BizPilot-Tasks-dev
"""

import sys
import os
import argparse
import boto3

# Add layers/model to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'layers', 'model'))
from model import put_customer, put_order, create_followup_task

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


def seed(customers_table, orders_table, tasks_table):
    print(f"🚀 Seeding BizPilot AI Demo Data...")
    print(f"  • Customers Table: {customers_table}")
    print(f"  • Orders Table:    {orders_table}")
    print(f"  • Tasks Table:     {tasks_table}\n")

    print(f"Inserting {len(SAMPLE_CUSTOMERS)} customers...")
    for c in SAMPLE_CUSTOMERS:
        put_customer(c, customers_table)
        print(f"  ✓ Customer: {c['customer_id']} - {c['name']}")

    print(f"\nInserting {len(SAMPLE_ORDERS)} orders...")
    for o in SAMPLE_ORDERS:
        put_order(o, orders_table)
        print(f"  ✓ Order: {o['order_id']} ({o['status']}) - {o['product']} (₹{o['amount']})")

    print(f"\nInserting {len(SAMPLE_TASKS)} tasks...")
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
        print(f"  ✓ Task: {t['task_id']} [{t['priority'].upper()}] - {t['description']}")

    print("\n✨ Data seeding successfully completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed BizPilot AI DynamoDB tables")
    parser.add_argument("--env", default="dev", help="Environment suffix (default: dev)")
    parser.add_argument("--customers-table", help="Explicit customers table name")
    parser.add_argument("--orders-table", help="Explicit orders table name")
    parser.add_argument("--tasks-table", help="Explicit tasks table name")
    args = parser.parse_args()

    c_table = args.customers_table or f"BizPilot-Customers-{args.env}"
    o_table = args.orders_table or f"BizPilot-Orders-{args.env}"
    t_table = args.tasks_table or f"BizPilot-Tasks-{args.env}"

    seed(c_table, o_table, t_table)
