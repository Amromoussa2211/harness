# STORY-PAYMENT-001

## User Story

As a customer,
I want to make a payment through the online payment system,
so that I can complete my purchase securely and receive confirmation.

## Acceptance Criteria

### AC1 — Successful Payment
Given a logged-in customer with a valid cart
When the customer submits valid payment details
Then the payment is processed successfully
And the customer receives a payment confirmation

### AC2 — Payment with Insufficient Funds
Given a logged-in customer with a valid cart
When the customer submits payment with insufficient funds
Then the payment is rejected
And the customer sees an error message about insufficient funds

### AC3 — Payment Card Validation
Given a logged-in customer with a valid cart
When the customer submits invalid card details (expired card)
Then the payment is rejected
And the customer sees a card validation error
