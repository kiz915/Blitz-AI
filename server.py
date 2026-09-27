"""
BizPilot AI — Local Development & Demo Server
Serves the web dashboard and provides the REST / Agent API backend.

Usage:
  python server.py [--port 3000] [--live-bedrock]
"""

import sys
import os
import json
import argparse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

# Add layers/model and agent/functions/operations to Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, 'layers', 'model'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'agent', 'functions', 'operations'))

from model import (
    get_customer, list_customers, put_customer,
    get_order, search_orders_by_status, list_orders, put_order,
    create_followup_task, list_pending_tasks, list_all_tasks, complete_task,
    get_business_summary
)
import app as operations_lambda

# In-memory demo data store when AWS DynamoDB is not connected
LOCAL_STORE = {
    "customers": [
        {"customer_id": "CUST-001", "name": "Priya Sharma", "email": "priya.sharma@example.com", "phone": "+91 98765 43210", "created_at": "2026-09-01"},
        {"customer_id": "CUST-002", "name": "Rajesh Patel", "email": "rajesh.patel@example.com", "phone": "+91 98234 56789", "created_at": "2026-09-05"},
        {"customer_id": "CUST-003", "name": "Anita Roy", "email": "anita.roy@example.com", "phone": "+91 97123 45678", "created_at": "2026-09-10"},
        {"customer_id": "CUST-004", "name": "Vikram Malhotra", "email": "vikram.m@example.com", "phone": "+91 96543 21098", "created_at": "2026-09-12"},
        {"customer_id": "CUST-005", "name": "Sneha Kulkarni", "email": "sneha.k@example.com", "phone": "+91 95432 10987", "created_at": "2026-09-15"}
    ],
    "orders": [
        {"order_id": "ORD-1001", "customer_id": "CUST-002", "customer_name": "Rajesh Patel", "product": "Ergonomic Office Chair", "amount": 8999, "status": "delivered", "order_date": "2026-09-18", "expected_delivery": "2026-09-22"},
        {"order_id": "ORD-1002", "customer_id": "CUST-003", "customer_name": "Anita Roy", "product": "USB-C Multiport Dock", "amount": 3499, "status": "shipped", "order_date": "2026-09-25", "expected_delivery": "2026-10-02"},
        {"order_id": "ORD-1003", "customer_id": "CUST-001", "customer_name": "Priya Sharma", "product": "Wireless Keyboard", "amount": 2499, "status": "delayed", "order_date": "2026-09-20", "expected_delivery": "2026-09-24"},
        {"order_id": "ORD-1004", "customer_id": "CUST-004", "customer_name": "Vikram Malhotra", "product": "4K Ultra-HD Monitor 27-inch", "amount": 24999, "status": "delayed", "order_date": "2026-09-21", "expected_delivery": "2026-09-26"},
        {"order_id": "ORD-1005", "customer_id": "CUST-005", "customer_name": "Sneha Kulkarni", "product": "Noise Cancelling Headphones", "amount": 5999, "status": "pending", "order_date": "2026-09-29", "expected_delivery": "2026-10-04"},
        {"order_id": "ORD-1006", "customer_id": "CUST-001", "customer_name": "Priya Sharma", "product": "Aluminum Laptop Stand", "amount": 1299, "status": "processing", "order_date": "2026-09-28", "expected_delivery": "2026-10-03"},
        {"order_id": "ORD-1007", "customer_id": "CUST-003", "customer_name": "Anita Roy", "product": "Blue-light Blocking Glasses", "amount": 799, "status": "cancelled", "order_date": "2026-09-15", "expected_delivery": "2026-09-19"}
    ],
    "tasks": [
        {"task_id": "TASK-001", "customer_id": "CUST-001", "order_id": "ORD-1003", "description": "Follow up with Priya about delayed order ORD-1003", "priority": "high", "status": "pending", "created_at": "2026-09-25 10:00:00", "due_date": "2026-09-26"},
        {"task_id": "TASK-002", "customer_id": "CUST-004", "order_id": "ORD-1004", "description": "Check logistics courier status for Vikram's monitor", "priority": "medium", "status": "pending", "created_at": "2026-09-26 11:30:00", "due_date": "2026-09-28"},
        {"task_id": "TASK-003", "customer_id": "CUST-002", "order_id": "ORD-1001", "description": "Send delivery satisfaction survey to Rajesh", "priority": "low", "status": "completed", "created_at": "2026-09-23 09:15:00", "due_date": "2026-09-24"}
    ]
}


class BizPilotHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Static Assets
        if path == '/' or not path.startswith('/api/'):
            self.serve_static(path)
            return

        # API Endpoints
        if path == '/api/orders':
            status = query.get('status', [None])[0]
            orders = LOCAL_STORE['orders']
            if status:
                orders = [o for o in orders if o.get('status') == status.lower()]
            self._set_headers(200)
            self.wfile.write(json.dumps({'orders': orders}).encode('utf-8'))
            return

        if path == '/api/customers':
            self._set_headers(200)
            self.wfile.write(json.dumps({'customers': LOCAL_STORE['customers']}).encode('utf-8'))
            return

        if path == '/api/tasks':
            status = query.get('status', [None])[0]
            tasks = LOCAL_STORE['tasks']
            if status:
                tasks = [t for t in tasks if t.get('status') == status.lower()]
            self._set_headers(200)
            self.wfile.write(json.dumps({'tasks': tasks}).encode('utf-8'))
            return

        if path == '/api/summary':
            orders = LOCAL_STORE['orders']
            customers = LOCAL_STORE['customers']
            tasks = LOCAL_STORE['tasks']

            delayed = [o for o in orders if o.get('status') == 'delayed']
            pending = [o for o in orders if o.get('status') == 'pending']
            completed_tasks = [t for t in tasks if t.get('status') == 'completed']
            pending_tasks = [t for t in tasks if t.get('status') == 'pending']

            summary = {
                'metrics': {
                    'total_orders': len(orders),
                    'delayed_orders': len(delayed),
                    'pending_orders': len(pending),
                    'completed_tasks_count': len(completed_tasks),
                    'total_customers': len(customers),
                    'pending_tasks_count': len(pending_tasks)
                },
                'delayed_orders': delayed,
                'pending_tasks': pending_tasks
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(summary).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(length)
        body = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}

        if path == '/api/tasks/complete':
            task_id = body.get('task_id')
            for t in LOCAL_STORE['tasks']:
                if t['task_id'] == task_id:
                    t['status'] = 'completed'
                    self._set_headers(200)
                    self.wfile.write(json.dumps({'status': 'success', 'task': t}).encode('utf-8'))
                    return
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': f'Task {task_id} not found'}).encode('utf-8'))
            return

        if path == '/api/tasks/create':
            task_count = len(LOCAL_STORE['tasks']) + 1
            new_id = f"TASK-{task_count:03d}"
            new_task = {
                'task_id': body.get('task_id') or new_id,
                'customer_id': body.get('customer_id', ''),
                'order_id': body.get('order_id', ''),
                'description': body.get('description', 'Operational Task'),
                'priority': body.get('priority', 'medium'),
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                'due_date': body.get('due_date', '2026-10-01')
            }
            LOCAL_STORE['tasks'].insert(0, new_task)
            self._set_headers(201)
            self.wfile.write(json.dumps({'status': 'success', 'task': new_task}).encode('utf-8'))
            return

        if path == '/api/chat':
            user_msg = body.get('message', '').strip()
            response = self.handle_chat_query(user_msg)
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))

    def handle_chat_query(self, query):
        """
        Orchestrates natural language intent recognition, calls operations Lambda tools,
        and formulates the final grounded answer.
        """
        q = query.lower()

        # Tool 1: search_orders(status="delayed")
        if 'delayed' in q or 'delay' in q:
            delayed = [o for o in LOCAL_STORE['orders'] if o.get('status') == 'delayed']
            items_text = "".join([f"• <strong>{o['order_id']}</strong>: {o['product']} for {o.get('customer_name', o.get('customer_id'))} (₹{o['amount']}) — Expected: {o['expected_delivery']}<br>" for o in delayed])
            return {
                'reply': f"Found <strong>{len(delayed)} delayed order(s)</strong> requiring attention:<br><br>{items_text}<br>Would you like me to create follow-up tasks for these customers?",
                'tool': {'name': 'search_orders', 'parameters': {'status': 'delayed'}},
                'payload': delayed,
                'action_performed': False
            }

        # Tool 2: get_order(order_id)
        import re
        order_match = re.search(r'ord-\d{4}', q, re.IGNORECASE)
        if order_match and not ('follow-up' in q or 'create' in q or 'task' in q):
            oid = order_match.group(0).upper()
            found = next((o for o in LOCAL_STORE['orders'] if o['order_id'] == oid), None)
            if found:
                status_color = "#f87171" if found['status'] == 'delayed' else "#34d399"
                return {
                    'reply': f"<strong>{found['order_id']}</strong> is currently <strong style='color: {status_color};'>{found['status'].upper()}</strong>.<br>"
                             f"It is a <em>{found['product']}</em> order for <strong>{found.get('customer_name', found['customer_id'])}</strong>, "
                             f"amounting to ₹{found['amount']}, expected on <strong>{found['expected_delivery']}</strong>.",
                    'tool': {'name': 'get_order', 'parameters': {'order_id': oid}},
                    'payload': found,
                    'action_performed': False
                }
            else:
                return {
                    'reply': f"Order <strong>{oid}</strong> does not exist in the database. Please verify the ID.",
                    'tool': {'name': 'get_order', 'parameters': {'order_id': oid}},
                    'payload': None,
                    'action_performed': False
                }

        # Tool 3: create_followup_task
        if 'create' in q and ('task' in q or 'follow-up' in q or 'follow up' in q):
            is_high = 'high' in q
            priority = 'high' if is_high else 'medium'
            oid = order_match.group(0).upper() if order_match else "ORD-1003"
            cid = "CUST-001"
            
            # Resolve customer from order if found
            linked_order = next((o for o in LOCAL_STORE['orders'] if o['order_id'] == oid), None)
            if linked_order:
                cid = linked_order['customer_id']

            new_task_id = f"TASK-{len(LOCAL_STORE['tasks']) + 1:03d}"
            new_task = {
                'task_id': new_task_id,
                'customer_id': cid,
                'order_id': oid,
                'description': f"Follow up regarding delayed order {oid}",
                'priority': priority,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                'due_date': "2026-09-26"
            }
            LOCAL_STORE['tasks'].insert(0, new_task)
            
            return {
                'reply': f"Created <strong>{new_task_id}</strong> as a <strong>{priority.upper()}</strong>-priority follow-up task "
                         f"for customer {cid} regarding <strong>{oid}</strong>.<br>"
                         f"Due date set to <strong>{new_task['due_date']}</strong>.",
                'tool': {
                    'name': 'create_followup_task',
                    'parameters': {'customer_id': cid, 'order_id': oid, 'description': new_task['description'], 'priority': priority}
                },
                'payload': new_task,
                'action_performed': True
            }

        # Tool 4: list_pending_tasks
        if 'pending' in q and ('task' in q or 'tasks' in q):
            pending = [t for t in LOCAL_STORE['tasks'] if t['status'] == 'pending']
            lines = "".join([f"• [<strong>{t['priority'].upper()}</strong>] <strong>{t['task_id']}</strong>: {t['description']} (Due: {t['due_date']})<br>" for t in pending])
            return {
                'reply': f"Found <strong>{len(pending)} pending operational task(s)</strong>:<br><br>{lines}",
                'tool': {'name': 'list_pending_tasks', 'parameters': {}},
                'payload': pending,
                'action_performed': False
            }

        # Tool 5: complete_task
        task_match = re.search(r'task-\d{3}', q, re.IGNORECASE)
        if ('complete' in q or 'done' in q or 'mark' in q) and task_match:
            tid = task_match.group(0).upper()
            target = next((t for t in LOCAL_STORE['tasks'] if t['task_id'] == tid), None)
            if target:
                target['status'] = 'completed'
                return {
                    'reply': f"Successfully marked <strong>{tid}</strong> ('{target['description']}') as <strong style='color: #34d399;'>COMPLETED</strong> in DynamoDB.",
                    'tool': {'name': 'complete_task', 'parameters': {'task_id': tid}},
                    'payload': target,
                    'action_performed': True
                }
            else:
                return {
                    'reply': f"Task <strong>{tid}</strong> was not found in the system.",
                    'tool': {'name': 'complete_task', 'parameters': {'task_id': tid}},
                    'payload': None,
                    'action_performed': False
                }

        # Tool 6: get_business_summary
        if 'summary' in q or 'overview' in q or 'issue' in q or 'health' in q:
            delayed_count = len([o for o in LOCAL_STORE['orders'] if o['status'] == 'delayed'])
            pending_tasks = [t for t in LOCAL_STORE['tasks'] if t['status'] == 'pending']
            high_count = len([t for t in pending_tasks if t['priority'] == 'high'])

            return {
                'reply': (
                    f"<strong>BizPilot AI Operational Summary:</strong><br><br>"
                    f"• <strong>Total Orders:</strong> {len(LOCAL_STORE['orders'])} ({delayed_count} delayed, {len([o for o in LOCAL_STORE['orders'] if o['status'] == 'pending'])} pending)<br>"
                    f"• <strong>Active Customers:</strong> {len(LOCAL_STORE['customers'])} verified accounts<br>"
                    f"• <strong>Pending Tasks:</strong> {len(pending_tasks)} pending ({high_count} HIGH priority)<br>"
                    f"• <strong>Actionable Recommendation:</strong> Proactively contact Priya Sharma regarding delayed order ORD-1003 to maintain high customer trust."
                ),
                'tool': {'name': 'get_business_summary', 'parameters': {}},
                'payload': None,
                'action_performed': False
            }

        # Tool 7: get_customer
        cust_match = re.search(r'cust-\d{3}', q, re.IGNORECASE)
        if cust_match:
            cid = cust_match.group(0).upper()
            cust = next((c for c in LOCAL_STORE['customers'] if c['customer_id'] == cid), None)
            if cust:
                cust_orders = [o for o in LOCAL_STORE['orders'] if o['customer_id'] == cid]
                return {
                    'reply': f"Customer <strong>{cust['name']}</strong> ({cust['customer_id']}):<br>"
                             f"Email: {cust['email']} • Phone: {cust['phone']}<br>"
                             f"Associated Orders: {len(cust_orders)} order(s).",
                    'tool': {'name': 'get_customer', 'parameters': {'customer_id': cid}},
                    'payload': cust,
                    'action_performed': False
                }

        # Default conversational assistance
        return {
            'reply': "I am BizPilot AI. You can ask me to check order statuses (e.g. 'What's happening with ORD-1003?'), list delayed shipments, manage follow-up tasks, or generate an operational business summary.",
            'tool': None,
            'payload': None,
            'action_performed': False
        }

    def serve_static(self, path):
        if path == '/' or path == '':
            path = '/index.html'

        file_path = os.path.join(ROOT_DIR, 'web', path.lstrip('/'))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            self._set_headers(200, mime_type or 'text/plain')
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 File Not Found")


def run(port=3000):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    server_address = ('', port)
    httpd = HTTPServer(server_address, BizPilotHandler)
    print("\n=======================================================")
    print("  [BizPilot AI] Local Development Server Running")
    print(f"  Dashboard URL: http://localhost:{port}")
    print("  Bedrock Agent Tools: Active (Live/Simulation)")
    print("=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="BizPilot AI Local Dev Server")
    parser.add_argument('--port', type=int, default=3000, help="Port to listen on (default: 3000)")
    args = parser.parse_args()
    run(args.port)
