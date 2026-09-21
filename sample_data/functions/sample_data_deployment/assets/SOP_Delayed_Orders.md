# Standard Operating Procedure: Handling Delayed Customer Orders

**Document ID:** SOP-OPS-001  
**Version:** 2.0  
**Effective Date:** October 2026  
**Audience:** Customer Support, Fulfillment Operations, AI Agents (BizPilot AI)

---

## 1. Objective
Ensure proactive communication, rapid issue resolution, and high customer retention whenever a customer order is delayed past its `expected_delivery` date.

## 2. Delay Classification & Priority Assignment
When an order transitions to `delayed` status:
- **High Priority (`high`):**
  - Order amount > ₹5,000 OR
  - Order has been delayed by more than 2 business days OR
  - High-demand electronics or sensitive client deliverables.
- **Medium Priority (`medium`):**
  - Order amount between ₹1,500 and ₹5,000 OR
  - Carrier transit delay reported by courier partner within 24 hours.
- **Low Priority (`low`):**
  - Minor delay with confirmed revised delivery within 24 hours.

## 3. Required Action Steps for Operations / BizPilot AI
1. **Detect Delayed Orders:** Run daily morning sweeps using `search_orders(status="delayed")`.
2. **Identify Impacted Customer:** Retrieve customer profile using `get_customer(customer_id)`.
3. **Generate Follow-Up Task:** Automatically or upon manager prompt, generate a follow-up task via `create_followup_task`:
   - Specify Customer ID, Order ID, and clear description of reason.
   - Set due date within 24 hours of delay detection.
4. **Customer Communication SLA:**
   - Contact customer via registered email or WhatsApp/SMS with an honest timeline and courier tracking reference.
5. **Closure:** Once customer is contacted and alternative fulfillment or timeline confirmed, mark task complete using `complete_task`.
