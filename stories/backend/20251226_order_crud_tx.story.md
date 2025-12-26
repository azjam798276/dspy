---
id: "20251226_order_crud_tx"
source_url: "https://sequelize.org/docs/v6/other-topics/transactions/"
difficulty: "hard"
tags: ["database", "transactions", "sequelize", "inventory", "consistency"]
tech_stack: "Node.js, Sequelize, PostgreSQL, Jest"
---

# User Story
As an e-commerce platform, I want to create orders that atomically deduct inventory and create order items, so that stock levels remain consistent even if the process partially fails.

# Context & Constraints
**Full Transaction Flow:**
1. Validate inventory availability for all items
2. Create Order record
3. Create OrderItem records  
4. Decrement Product stock atomically
5. **Single commit** or **full rollback**

**Data Models:**
Order: {id, userId, total, status}
OrderItem: {id, orderId, productId, quantity, price}
Product: {id, name, stock, price}

text

**Edge Cases:**
- Partial stock failure → rollback entire order
- Concurrent orders → row locking prevents oversell

# Acceptance Criteria
- [ ] **Transaction Scope:** Single `sequelize.transaction()` wraps all operations
- [ ] **Inventory Check:** Validate stock before creating order
- [ ] **Atomic Updates:** Stock decrement + OrderItem creation succeed or fail together
- [ ] **Concurrency:** `LOCK.UPDATE` prevents race conditions
- [ ] **Rollback Test:** Simulate stock failure → no partial order created
- [ ] **Integration Test:** Create order → verify stock decremented correctly
