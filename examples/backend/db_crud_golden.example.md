---
id: "db_crud_golden"
source_story: "stories/backend/order_crud.story.md"
tags: ["database", "crud", "transactions", "sequelize", "validation"]
---

## Problem

Implement Order CRUD with inventory validation:
- POST /orders - Create order + deduct inventory atomically
- GET /orders/:id - Fetch single order with relations
- PUT /orders/:id/status - Update with audit trail
- Use transactions for data consistency

## Solution

// path: src/services/orderService.js
const { sequelize, Order, OrderItem, Product, User } = require('../models');

class OrderService {
static async createOrder(userId, items) {
const transaction = await sequelize.transaction();

text
try {
  // Validate inventory first
  for (const item of items) {
    const product = await Product.findByPk(item.productId, { transaction });
    if (!product || product.stock < item.quantity) {
      throw new Error(`Insufficient stock for ${product?.name}`);
    }
  }

  // Create order
  const order = await Order.create(
    { userId, total: items.reduce((sum, i) => sum + i.price * i.quantity, 0) },
    { transaction }
  );

  // Create items + deduct stock atomically
  const orderItems = await Promise.all(
    items.map(async (item) => {
      await Product.decrement('stock', {
        by: item.quantity,
        where: { id: item.productId },
        transaction
      });
      
      return OrderItem.create({ orderId: order.id, ...item }, { transaction });
    })
  );

  await transaction.commit();
  return { order, items: orderItems };
} catch (error) {
  await transaction.rollback();
  throw error;
}
}

static async updateStatus(orderId, status, adminId) {
return sequelize.transaction(async (t) => {
const order = await Order.findByPk(orderId, {
include: [User],
transaction: t,
lock: t.LOCK.UPDATE
});

text
  if (!order) throw new Error('Order not found');
  
  order.status = status;
  order.updatedBy = adminId;
  await order.save({ transaction: t });
  
  return order;
});
}
}

module.exports = OrderService;

text

## Key Techniques
- **Atomic Transactions**: `sequelize.transaction()` ensures consistency
- **Inventory Lock**: Validate stock before creating order
- **Cascade Updates**: Single commit for order + items + stock
- **Row Locking**: `LOCK.UPDATE` prevents race conditions
