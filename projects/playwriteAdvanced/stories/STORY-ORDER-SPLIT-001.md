# STORY-ORDER-SPLIT-001

## User Story

As a customer using split payment,
I want to split my order by amount or by item,
so that I can pay for different parts of my order using different payment methods.

## Acceptance Criteria

### AC1 — Split Order by Amount
Given a customer with items in the cart totaling more than the split threshold
When the customer chooses to split by amount
Then the order is divided into multiple sub-orders based on the specified amount limits
And each sub-order is processed independently

### AC2 — Split Order by Item
Given a customer with multiple different items in the cart
When the customer chooses to split by item
Then each item is placed in a separate sub-order
And each sub-order can be paid independently

### AC3 — Split Order by Person
Given a customer with multiple items in the cart and multiple payers
When the customer chooses to split by person
Then the order is divided among the specified payers
And each payer receives their portion of the order

### AC4 — Order Without Split
Given a customer with items in the cart
When the customer places an order without split options
Then the order is processed as a single unified transaction
