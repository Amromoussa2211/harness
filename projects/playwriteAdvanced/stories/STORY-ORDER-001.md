# STORY-ORDER-001

## User Story

As a customer,
I want to place an order for products in my cart,
so that I can purchase items and receive an order confirmation.

## Acceptance Criteria

### AC1 — Place Order
Given a customer with items in the cart
When the customer submits the order
Then the order is created with the correct items and quantities
And the customer receives an order confirmation

### AC2 — Order Without Split
Given a customer with items in the cart
When the customer places an order without split options
Then the order is processed as a single transaction

### AC3 — Order Split by Amount
Given a customer with a large cart total
When the customer splits the order by amount
Then the order is divided into multiple transactions by the specified amount thresholds

### AC4 — Order Split by Item
Given a customer with multiple items in the cart
When the customer splits the order by item
Then each item is processed as a separate line item in the order
