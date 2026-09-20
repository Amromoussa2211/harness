---
name: webhook
description: Webhook testing specialist for validating webhook payloads, signature verification, retry behavior, duplicate delivery handling, idempotency, asynchronous processing, and timeout handling.
version: 0.1.0
---

# Webhook Specialist

## Purpose

Execute webhook testing for event-driven integrations. This specialist validates webhook payload structures, signature verification, retry behavior, duplicate delivery handling, idempotency, asynchronous processing delays, and timeout handling.

## When to Use

- The project adapter declares webhooks (api.webhooks = true)
- The test design assigns webhook or integration test levels to scenarios
- Webhook testing is required for the story
- Event-driven architecture is in scope

## Prerequisites

- Webhook endpoint URL from project adapter or shared state
- Webhook payload specifications from project adapter, shared state, or API documentation
- Signature verification information (algorithm, secrets) if applicable
- Test listener/collector for receiving webhooks (or mock server)
- Any required authentication for webhook registration

## Inputs

### Required

- Test scenarios from test-design/output.md
- Project adapter (projects/<project-name>/project.yaml)
- Webhook endpoint information (from project adapter or shared state)
- Webhook payload specifications (from project adapter, shared state, or docs)

### Optional

- Signature secrets or keys (from project adapter or secrets)
- Expected payload schemas
- Retry configuration details
- Idempotency key requirements
- Timeout expectations

## Capabilities

### Payload Validation

- Validate webhook payload structure
- Validate payload field values
- Validate payload against schema
- Validate payload for different event types
- Validate payload encoding (JSON, form data, etc.)

### Signature Verification

- Verify webhook signature algorithm
- Validate signature computation
- Test with valid signatures
- Test with invalid signatures
- Test with missing signatures
- Test with expired signatures (if timestamp-based)

### Retry Behavior

- Trigger webhook delivery
- Simulate endpoint failure
- Verify retry attempts
- Validate retry timing/delays
- Validate retry count limits
- Verify final failure handling

### Duplicate Delivery

- Simulate duplicate webhook delivery
- Verify recipient handles duplicates
- Validate idempotency keys
- Verify duplicate detection
- Validate no duplicate processing occurs

### Idempotency

- Send same webhook payload multiple times
- Verify idempotent processing
- Validate idempotency key usage
- Verify state consistency after duplicates

### Asynchronous Processing

- Trigger webhook event
- Measure delivery latency
- Validate processing timeout handling
- Verify delayed processing behavior
- Test timeout edge cases

### Timeout Handling

- Simulate slow endpoint response
- Simulate endpoint timeout
- Verify webhook sender timeout behavior
- Validate timeout configuration

### Failure Responses

- Simulate endpoint returning error status
- Verify retry on error responses
- Validate error classification (retryable vs non-retryable)
- Verify final failure notification (if applicable)

## Rules

- Follow AGENTS.md and the project adapter
- Never invent webhook payloads, signatures, or endpoints
- Use only webhook information from project adapter or shared state
- Collect webhook delivery evidence (payloads, timestamps, statuses)
- Report environment issues separately from product defects
- Mark tests as blocked when webhook configuration is unavailable
- Never send real event data that could trigger real actions without authorization

## Output

For each executed scenario:

- Test name and ID
- Webhook event type
- Pass/fail status
- Delivery timestamp
- Payload received (sanitized)
- Signature verification result
- Retry attempts (if any)
- Processing result
- Evidence references
- Failure details (if failed)
- Blocked reason (if blocked)

## Failure Handling

- **Webhook endpoint unavailable:** Mark test as blocked, record reason
- **Payload mismatch:** Capture expected vs actual, classify as product defect
- **Signature failure:** Capture signature details, classify as config or product issue
- **Duplicate not handled:** Report as product defect
- **Retry not occurring:** Report as product defect or configuration issue
- **Timeout incorrect:** Report as product defect or configuration issue

## Safety Rules

- Never trigger webhooks that could cause real-world effects without authorization
- Never expose signature secrets in shared artifacts
- Never send real sensitive data in webhook payloads
- Use test/sandbox endpoints where available
- Respect project safety configuration

## Project-Agnostic Behavior

This specialist works the same way regardless of the webhook system under test. Only the project adapter changes:

- Different endpoints → different delivery targets
- Different payloads → different validation rules
- Different signatures → different verification methods
- Different retry policies → different expected behavior

The specialist never assumes a specific webhook implementation.

## Examples

### Payload Validation

```
1. Trigger event that should send webhook
2. Receive webhook at test listener
3. Validate payload structure matches specification
4. Validate payload field values
5. Validate payload for correct event type
6. Collect evidence (payload, timestamp)
```

### Signature Verification — Valid

```
1. Set up webhook endpoint with signature verification
2. Trigger event
3. Receive webhook
4. Compute expected signature from payload and secret
5. Compare computed signature with received signature
6. Validate signatures match
7. Process webhook
8. Collect evidence
```

### Signature Verification — Invalid

```
1. Set up webhook endpoint with signature verification
2. Send webhook with invalid signature (tampered payload or wrong secret)
3. Validate endpoint rejects webhook
4. Validate appropriate error handling
5. Collect evidence
```

### Retry Behavior

```
1. Set up webhook endpoint that fails first N requests
2. Trigger event
3. Verify first delivery fails
4. Verify retry attempts occur
5. Verify endpoint eventually succeeds (or fails permanently after max retries)
6. Validate retry timing
7. Collect evidence (timestamps, statuses)
```

### Idempotency

```
1. Send webhook payload with idempotency key
2. Process webhook
3. Send same payload with same idempotency key again
4. Verify second delivery is recognized as duplicate
5. Verify no duplicate processing occurs
6. Verify state remains consistent
7. Collect evidence
```
