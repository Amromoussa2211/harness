# STORY-API-INTEGRATION-001

## User Story

As a system integrator,
I want to verify that the payment API integrations work correctly,
so that payments can be processed through external payment providers reliably.

## Acceptance Criteria

### AC1 — Create Charge Request
Given the payment API is available
When a charge creation request is sent with valid card details
Then the API returns a successful charge response with a charge ID

### AC2 — Webhook Notification
Given a charge is created successfully
When the payment provider sends a webhook notification
Then the application receives and processes the webhook payload correctly

### AC3 — API Error Handling
Given the payment API is available
When a charge request is sent with invalid card details
Then the API returns an appropriate error response
And the error is logged for debugging
