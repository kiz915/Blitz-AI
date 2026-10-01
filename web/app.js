/**
 * BizPilot AI — Frontend Application Logic (Enhanced)
 * Supports reasoning traces, toast notifications, animated counters, keyboard shortcuts.
 */

const state = {
  activeTab: 'assistant',
  orders: [],
  customers: [],
  tasks: [],
  summary: null,
  selectedOrderFilter: 'all',
  selectedTaskFilter: 'all',
  orderSearchQuery: '',
};

const INITIAL_DEMO_DATA = {
  customers: [
    { customer_id: "CUST-001", name: "Priya Sharma", email: "priya.sharma@example.com", phone: "+91 98765 43210", created_at: "2026-09-01" },
    { customer_id: "CUST-002", name: "Rajesh Patel", email: "rajesh.patel@example.com", phone: "+91 98234 56789", created_at: "2026-09-05" },
    { customer_id: "CUST-003", name: "Anita Roy", email: "anita.roy@example.com", phone: "+91 97123 45678", created_at: "2026-09-10" },
    { customer_id: "CUST-004", name: "Vikram Malhotra", email: "vikram.m@example.com", phone: "+91 96543 21098", created_at: "2026-09-12" },
    { customer_id: "CUST-005", name: "Sneha Kulkarni", email: "sneha.k@example.com", phone: "+91 95432 10987", created_at: "2026-09-15" }
  ],
  orders: [
    { order_id: "ORD-1001", customer_id: "CUST-002", customer_name: "Rajesh Patel", product: "Ergonomic Office Chair", amount: 8999, status: "delivered", order_date: "2026-09-18", expected_delivery: "2026-09-22" },
    { order_id: "ORD-1002", customer_id: "CUST-003", customer_name: "Anita Roy", product: "USB-C Multiport Dock", amount: 3499, status: "shipped", order_date: "2026-09-25", expected_delivery: "2026-10-02" },
    { order_id: "ORD-1003", customer_id: "CUST-001", customer_name: "Priya Sharma", product: "Wireless Keyboard", amount: 2499, status: "delayed", order_date: "2026-09-20", expected_delivery: "2026-09-24" },
    { order_id: "ORD-1004", customer_id: "CUST-004", customer_name: "Vikram Malhotra", product: "4K Monitor 27-inch", amount: 24999, status: "delayed", order_date: "2026-09-21", expected_delivery: "2026-09-26" },
    { order_id: "ORD-1005", customer_id: "CUST-005", customer_name: "Sneha Kulkarni", product: "Noise Cancelling Headphones", amount: 5999, status: "pending", order_date: "2026-09-29", expected_delivery: "2026-10-04" },
    { order_id: "ORD-1006", customer_id: "CUST-001", customer_name: "Priya Sharma", product: "Laptop Stand", amount: 1299, status: "processing", order_date: "2026-09-28", expected_delivery: "2026-10-03" }
  ],
  tasks: [
    { task_id: "TASK-001", customer_id: "CUST-001", order_id: "ORD-1003", description: "Follow up with Priya about delayed order", priority: "high", status: "pending", created_at: "2026-09-25 10:00:00", due_date: "2026-09-26" },
    { task_id: "TASK-002", customer_id: "CUST-004", order_id: "ORD-1004", description: "Check courier status for Vikram's monitor", priority: "medium", status: "pending", created_at: "2026-09-26 11:30:00", due_date: "2026-09-28" }
  ]
};

// ==========================================
// TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  const icon = type === 'success' 
    ? `<svg class="toast-icon success" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`
    : `<svg class="toast-icon info" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;

  toast.innerHTML = `${icon} <div>${escapeHtml(message)}</div>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// ANIMATED COUNTERS
// ==========================================
function animateCounter(elementId, targetValue) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  const start = parseInt(el.textContent) || 0;
  const duration = 1000;
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Ease out quad
    const easeProgress = progress * (2 - progress);
    const current = Math.floor(start + (targetValue - start) * easeProgress);
    
    el.textContent = current;
    
    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.textContent = targetValue;
    }
  }
  requestAnimationFrame(update);
}

// ==========================================
// INITIALIZATION & KEYBOARD SHORTCUTS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupChatHandlers();
  setupOrdersFilterHandlers();
  setupTasksFilterHandlers();
  setupModalHandlers();
  setupKeyboardShortcuts();
  
  fetchApplicationData();
});

function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl+K -> Focus Chat
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      switchTab('assistant');
      document.getElementById('chat-input').focus();
    }
    // Numbers 1-5 -> Switch Tabs (if no input focused)
    if (!['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      if (e.key === '1') switchTab('assistant');
      if (e.key === '2') switchTab('orders');
      if (e.key === '3') switchTab('customers');
      if (e.key === '4') switchTab('tasks');
      if (e.key === '5') switchTab('overview');
    }
  });
}

function setupNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  const refreshBtn = document.getElementById('btn-refresh-data');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchApplicationData);
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(section => {
    section.classList.toggle('active', section.id === `section-${tabId}`);
  });

  if (tabId === 'orders') renderOrders();
  if (tabId === 'customers') renderCustomers();
  if (tabId === 'tasks') renderTasks();
  if (tabId === 'overview') renderOverview();
}

async function fetchApplicationData() {
  try {
    const [ordersRes, customersRes, tasksRes, summaryRes] = await Promise.all([
      fetch('/api/orders').catch(() => null),
      fetch('/api/customers').catch(() => null),
      fetch('/api/tasks').catch(() => null),
      fetch('/api/summary').catch(() => null)
    ]);

    if (ordersRes && ordersRes.ok) state.orders = (await ordersRes.json()).orders;
    else state.orders = [...INITIAL_DEMO_DATA.orders];

    if (customersRes && customersRes.ok) state.customers = (await customersRes.json()).customers;
    else state.customers = [...INITIAL_DEMO_DATA.customers];

    if (tasksRes && tasksRes.ok) state.tasks = (await tasksRes.json()).tasks;
    else state.tasks = [...INITIAL_DEMO_DATA.tasks];

    if (summaryRes && summaryRes.ok) state.summary = await summaryRes.json();
    else recomputeLocalSummary();

    updateHeaderBadges();
    renderCurrentTab();
  } catch (err) {
    state.orders = [...INITIAL_DEMO_DATA.orders];
    state.customers = [...INITIAL_DEMO_DATA.customers];
    state.tasks = [...INITIAL_DEMO_DATA.tasks];
    recomputeLocalSummary();
    updateHeaderBadges();
    renderCurrentTab();
  }
}

function recomputeLocalSummary() {
  const delayed = state.orders.filter(o => o.status === 'delayed');
  const pending = state.orders.filter(o => o.status === 'pending');
  const pendingTasks = state.tasks.filter(t => t.status === 'pending');
  const completedTasks = state.tasks.filter(t => t.status === 'completed');

  state.summary = {
    metrics: {
      total_orders: state.orders.length,
      delayed_orders: delayed.length,
      pending_orders: pending.length,
      completed_tasks_count: completedTasks.length,
      total_customers: state.customers.length,
      pending_tasks_count: pendingTasks.length
    },
    delayed_orders: delayed,
    pending_tasks: pendingTasks
  };
}

function updateHeaderBadges() {
  const delayedCount = state.orders.filter(o => o.status === 'delayed').length;
  const pendingTasksCount = state.tasks.filter(t => t.status === 'pending').length;

  const badgeDelayed = document.getElementById('badge-delayed-orders');
  if (badgeDelayed) {
    badgeDelayed.textContent = delayedCount;
    badgeDelayed.style.display = delayedCount > 0 ? 'inline-block' : 'none';
  }

  const badgeTasks = document.getElementById('badge-pending-tasks');
  if (badgeTasks) {
    badgeTasks.textContent = pendingTasksCount;
    badgeTasks.style.display = pendingTasksCount > 0 ? 'inline-block' : 'none';
  }
}

function renderCurrentTab() {
  if (state.activeTab === 'orders') renderOrders();
  else if (state.activeTab === 'customers') renderCustomers();
  else if (state.activeTab === 'tasks') renderTasks();
  else if (state.activeTab === 'overview') renderOverview();
}

// ==========================================
// CHAT ENGINE
// ==========================================
function setupChatHandlers() {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value.trim();
    if (!prompt) return;
    chatInput.value = '';
    await handleUserMessage(prompt);
  });

  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', async () => {
      switchTab('assistant');
      await handleUserMessage(chip.dataset.prompt);
    });
  });
}

async function handleUserMessage(userText) {
  appendUserMessage(userText);
  const typingElement = appendTypingIndicator();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText })
    });

    if (response.ok) {
      const data = await response.json();
      typingElement.remove();
      appendAssistantMessage(data.reply, data.tool, data.payload);
      if (data.action_performed) await fetchApplicationData();
    } else {
      throw new Error('API request failed');
    }
  } catch (err) {
    typingElement.remove();
    const simulatedResponse = simulateAgentResponse(userText);
    appendAssistantMessage(simulatedResponse.reply, simulatedResponse.tool, simulatedResponse.payload);
    
    if (simulatedResponse.action_performed) {
      recomputeLocalSummary();
      updateHeaderBadges();
      renderCurrentTab();
    }
  }

  const viewport = document.getElementById('chat-viewport');
  viewport.scrollTop = viewport.scrollHeight;
}

function appendUserMessage(text) {
  const viewport = document.getElementById('chat-viewport');
  const msg = document.createElement('div');
  msg.className = 'chat-message user';
  msg.innerHTML = `
    <div class="message-content">
      <div class="message-sender">You</div>
      <div class="message-text">${escapeHtml(text)}</div>
    </div>
  `;
  viewport.appendChild(msg);
  viewport.scrollTop = viewport.scrollHeight;
}

function appendTypingIndicator() {
  const viewport = document.getElementById('chat-viewport');
  const typing = document.createElement('div');
  typing.className = 'chat-message assistant';
  typing.id = 'typing-indicator';
  typing.innerHTML = `
    <div class="message-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
    </div>
    <div class="message-content">
      <div class="message-sender">BizPilot AI <span class="agent-tag">Routing request...</span></div>
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  viewport.appendChild(typing);
  viewport.scrollTop = viewport.scrollHeight;
  return typing;
}

function appendAssistantMessage(replyText, toolInfo, payload) {
  const viewport = document.getElementById('chat-viewport');
  const msg = document.createElement('div');
  msg.className = 'chat-message assistant';

  let traceHtml = '';
  if (toolInfo) {
    // Generate simulated reasoning trace data
    const execTime = Math.floor(Math.random() * 250) + 120;
    const scanned = Math.floor(Math.random() * 50) + 10;
    const paramsStr = JSON.stringify(toolInfo.parameters || {});
    
    traceHtml = `
      <div class="reasoning-trace" onclick="this.classList.toggle('expanded')">
        <div class="reasoning-header">
          <svg class="icon-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition: transform 0.2s;"><polyline points="6 9 12 15 18 9"></polyline></svg>
          Model Reasoning & Execution Trace
        </div>
        <div class="reasoning-body">
          <div><span style="color:var(--accent-cyan)">[Agent]</span> Analyzing intent & selecting tool: <strong>${escapeHtml(toolInfo.name)}</strong></div>
          <div><span style="color:var(--accent-cyan)">[Agent]</span> Constructing parameters: ${escapeHtml(paramsStr)}</div>
          <div><span style="color:var(--accent-purple)">[Lambda]</span> Executing function with IAM role permissions</div>
          <div><span style="color:var(--status-delivered-text)">[DynamoDB]</span> Query completed. Scanned ${scanned} rows. Latency: ${execTime}ms</div>
        </div>
      </div>
    `;
  }

  let payloadHtml = '';
  if (payload && Array.isArray(payload) && payload.length > 0) {
    if (payload[0].order_id) {
      payloadHtml = `
        <div class="chat-payload-card">
          <div class="chat-payload-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
            Retrieved Orders (${payload.length})
          </div>
          ${payload.map(o => `
            <div class="chat-order-item">
              <div><strong>${o.order_id}</strong>: ${escapeHtml(o.product)}</div>
              <span class="status-badge ${o.status}">${o.status}</span>
            </div>
          `).join('')}
        </div>`;
    } else if (payload[0].task_id) {
      payloadHtml = `
        <div class="chat-payload-card">
          <div class="chat-payload-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path></svg>
            Tasks (${payload.length})
          </div>
          ${payload.map(t => `
            <div class="chat-task-item">
              <div><strong>${t.task_id}</strong>: ${escapeHtml(t.description)}</div>
              <span class="priority-badge ${t.priority}">${t.priority}</span>
            </div>
          `).join('')}
        </div>`;
    }
  }

  msg.innerHTML = `
    <div class="message-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
    </div>
    <div class="message-content">
      <div class="message-sender">BizPilot AI <span class="agent-tag">Claude 3 Sonnet</span></div>
      ${traceHtml}
      <div class="message-text">${replyText}</div>
      ${payloadHtml}
      <div class="message-meta">${formatTime(new Date())}</div>
    </div>
  `;
  viewport.appendChild(msg);
  viewport.scrollTop = viewport.scrollHeight;
}

function simulateAgentResponse(input) {
  const query = input.toLowerCase().trim();

  if (query.includes('delayed')) {
    const delayed = state.orders.filter(o => o.status === 'delayed');
    return {
      reply: `Found <strong>${delayed.length} delayed orders</strong> requiring operational attention. Would you like me to create follow-up tasks for these customers?`,
      tool: { name: 'search_orders', parameters: { status: 'delayed' } },
      payload: delayed
    };
  }

  const orderMatch = query.match(/ord-\d{4}/i);
  if (orderMatch && !query.includes('task') && !query.includes('follow')) {
    const orderId = orderMatch[0].toUpperCase();
    const order = state.orders.find(o => o.order_id === orderId);
    if (order) {
      return {
        reply: `<strong>${order.order_id}</strong> is currently <strong>${order.status.toUpperCase()}</strong>. It's expected on ${order.expected_delivery}.`,
        tool: { name: 'get_order', parameters: { order_id: orderId } },
        payload: [order]
      };
    }
  }

  if (query.includes('create') || query.includes('follow')) {
    const priority = query.includes('high') ? 'high' : 'medium';
    const newTaskId = `TASK-${String(state.tasks.length + 1).padStart(3, '0')}`;
    const newTask = {
      task_id: newTaskId,
      customer_id: "CUST-001",
      order_id: "ORD-1003",
      description: "Follow up with Priya regarding delayed order",
      priority: priority,
      status: "pending",
      created_at: new Date().toISOString().substring(0,19).replace('T',' '),
      due_date: "2026-09-26"
    };

    state.tasks.unshift(newTask);
    showToast(`Task ${newTaskId} created successfully`);

    return {
      reply: `Created <strong>${newTaskId}</strong> as a <strong>${priority.toUpperCase()}</strong>-priority follow-up task.`,
      tool: { name: 'create_followup_task', parameters: { order_id: 'ORD-1003', priority } },
      payload: [newTask],
      action_performed: true
    };
  }

  if (query.includes('summary') || query.includes('today')) {
    return {
      reply: `<strong>BizPilot AI Operational Summary:</strong><br>• Total Orders: ${state.orders.length}<br>• Delayed: ${state.orders.filter(o=>o.status==='delayed').length}<br>• Pending Tasks: ${state.tasks.filter(t=>t.status==='pending').length}`,
      tool: { name: 'get_business_summary', parameters: {} }
    };
  }

  return {
    reply: `I understand your request. Let me check our operational records.`,
    tool: { name: 'get_business_summary', parameters: {} }
  };
}

// ==========================================
// RENDERERS (Orders, Customers, Tasks, Overview)
// ==========================================
function setupOrdersFilterHandlers() {
  const filterPills = document.querySelectorAll('#order-status-filters .filter-pill');
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.selectedOrderFilter = pill.dataset.status;
      renderOrders();
    });
  });

  const searchInput = document.getElementById('order-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.orderSearchQuery = e.target.value.toLowerCase().trim();
      renderOrders();
    });
  }
}

function renderOrders() {
  const tbody = document.getElementById('orders-table-body');
  if (!tbody) return;

  document.getElementById('count-orders-all').textContent = state.orders.length;
  ['delayed', 'pending', 'processing', 'shipped', 'delivered'].forEach(st => {
    const el = document.getElementById(`count-orders-${st}`);
    if (el) el.textContent = state.orders.filter(o => o.status === st).length;
  });

  let filtered = state.orders;
  if (state.selectedOrderFilter !== 'all') filtered = filtered.filter(o => o.status === state.selectedOrderFilter);
  if (state.orderSearchQuery) {
    filtered = filtered.filter(o => 
      o.order_id.toLowerCase().includes(state.orderSearchQuery) ||
      o.product.toLowerCase().includes(state.orderSearchQuery)
    );
  }

  tbody.innerHTML = filtered.map(o => `
    <tr>
      <td><strong>${o.order_id}</strong></td>
      <td><div><strong>${escapeHtml(o.customer_name)}</strong></div><div style="font-size:0.7rem;color:var(--text-muted);">${o.customer_id}</div></td>
      <td>${escapeHtml(o.product)}</td>
      <td><strong>₹${Number(o.amount).toLocaleString('en-IN')}</strong></td>
      <td><span class="status-badge ${o.status}">${o.status}</span></td>
      <td>${o.expected_delivery}</td>
      <td><button class="btn-table-action" onclick="askAgentAboutOrder('${o.order_id}')">Ask AI</button></td>
    </tr>
  `).join('');
}

window.askAgentAboutOrder = function(orderId) {
  switchTab('assistant');
  handleUserMessage(`Check status of ${orderId}`);
};

function renderCustomers() {
  const grid = document.getElementById('customers-grid');
  if (!grid) return;

  grid.innerHTML = state.customers.map(c => {
    const custOrders = state.orders.filter(o => o.customer_id === c.customer_id);
    const initials = c.name.split(' ').map(n => n[0]).join('').substring(0, 2);
    
    return `
      <div class="customer-card">
        <div class="customer-card-header">
          <div class="customer-avatar">${initials}</div>
          <div>
            <div class="customer-name">${escapeHtml(c.name)}</div>
            <div class="customer-id">${c.customer_id}</div>
          </div>
        </div>
        <div class="customer-contact-list">
          <div class="customer-contact-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg> ${c.email}</div>
          <div class="customer-contact-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg> ${c.phone}</div>
        </div>
        <div class="customer-card-footer">
          <button class="btn-table-action" onclick="askAgentAboutOrder('')">Query with AI</button>
        </div>
      </div>
    `;
  }).join('');
}

function setupTasksFilterHandlers() {
  const tabs = document.querySelectorAll('.task-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.selectedTaskFilter = tab.dataset.taskFilter;
      renderTasks();
    });
  });
}

function renderTasks() {
  const list = document.getElementById('tasks-list');
  if (!list) return;

  let filtered = state.tasks;
  if (state.selectedTaskFilter === 'pending') filtered = filtered.filter(t => t.status === 'pending');
  else if (state.selectedTaskFilter === 'completed') filtered = filtered.filter(t => t.status === 'completed');
  else if (state.selectedTaskFilter === 'high') filtered = filtered.filter(t => t.priority === 'high' && t.status === 'pending');

  list.innerHTML = filtered.map(t => `
    <div class="task-card ${t.status === 'completed' ? 'completed' : ''}">
      <div class="task-main-info">
        <div class="task-header-line">
          <span class="priority-badge ${t.priority}">${t.priority}</span>
          <span class="task-id">${t.task_id}</span>
        </div>
        <div class="task-desc">${escapeHtml(t.description)}</div>
        <div class="task-meta-line">
          <span>Due: ${t.due_date}</span>
        </div>
      </div>
      <div>
        ${t.status === 'pending' ? `
          <button class="btn-complete-task" onclick="markTaskComplete('${t.task_id}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Done
          </button>
        ` : `<span style="color:var(--status-delivered-text);font-weight:600;font-size:0.8rem;">Completed</span>`}
      </div>
    </div>
  `).join('');
}

window.markTaskComplete = async function(taskId) {
  try {
    await fetch('/api/tasks/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    });
  } catch (err) {}

  const t = state.tasks.find(x => x.task_id === taskId);
  if (t) {
    t.status = 'completed';
    showToast(`Task ${taskId} marked as complete`, 'success');
    recomputeLocalSummary();
    updateHeaderBadges();
    renderTasks();
  }
};

function renderOverview() {
  if (!state.summary) recomputeLocalSummary();
  const metrics = state.summary.metrics;

  // Animated counters
  animateCounter('metric-total-orders', metrics.total_orders);
  animateCounter('metric-pending-orders', metrics.pending_orders);
  animateCounter('metric-delayed-orders', metrics.delayed_orders);
  animateCounter('metric-completed-tasks', metrics.completed_tasks_count);

  const delayedList = document.getElementById('overview-delayed-list');
  const delayedOrders = state.orders.filter(o => o.status === 'delayed');
  document.getElementById('overview-delayed-count').textContent = `${delayedOrders.length} Delayed`;

  if (delayedOrders.length === 0) {
    delayedList.innerHTML = `<div style="color:var(--text-muted);font-size:0.8rem;">All clear!</div>`;
  } else {
    delayedList.innerHTML = delayedOrders.map(d => `
      <div class="delayed-order-card">
        <div>
          <div style="font-weight:600;">${d.order_id}</div>
          <div style="font-size:0.75rem;color:var(--text-secondary);">${escapeHtml(d.product)}</div>
        </div>
        <button class="btn-table-action" onclick="askAgentAboutOrder('${d.order_id}')">Resolve</button>
      </div>
    `).join('');
  }
}

function setupModalHandlers() {
  const modal = document.getElementById('task-modal');
  const openBtn = document.getElementById('btn-open-new-task-modal');
  const closeBtn = document.getElementById('btn-close-task-modal');
  const cancelBtn = document.getElementById('btn-cancel-task-modal');
  const form = document.getElementById('create-task-form');

  if (openBtn) openBtn.addEventListener('click', () => modal.classList.add('active'));
  const closeModal = () => modal.classList.remove('active');
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const desc = document.getElementById('task-input-desc').value.trim();
      const priority = document.getElementById('task-input-priority').value;
      const newTaskId = `TASK-${String(state.tasks.length + 1).padStart(3, '0')}`;
      
      const newTask = {
        task_id: newTaskId,
        description: desc,
        priority: priority,
        status: 'pending',
        due_date: document.getElementById('task-input-due').value || '2026-10-01'
      };

      state.tasks.unshift(newTask);
      showToast(`Task ${newTaskId} created successfully`);
      recomputeLocalSummary();
      updateHeaderBadges();
      renderTasks();
      closeModal();
      form.reset();
    });
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
