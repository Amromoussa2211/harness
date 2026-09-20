---
name: playwright
description: Web UI automation specialist using Playwright for browser-based testing, including navigation, locators, assertions, authentication, fixtures, screenshots, traces, video, network interception, mocking, retries, and diagnostics.
version: 0.1.0
---

# Playwright Specialist

## Purpose

Execute web UI automation using Playwright. This specialist handles browser-based testing including navigation, element interaction, assertions, authentication flows, test fixtures, screenshots, traces, video recording, network interception, mocking, retries, and diagnostic collection.

## When to Use

- The story requires validating user-visible browser behavior
- The project adapter declares a web application (application.web = true)
- The automation framework is declared as Playwright
- The test design assigns UI or E2E test levels to scenarios
- Screenshots, traces, or video evidence are required

## Prerequisites

- Node.js environment with Playwright installed
- Playwright browsers installed (playwright install)
- Project adapter with web application configuration
- Test environment URL available (from project adapter or environment configuration)
- Locators or selectors defined in shared state or project adapter (never invent)

## Inputs

### Required

- Test scenarios from test-design/output.md
- Project adapter (projects/<project-name>/project.yaml)
- Application URL (from project adapter or environment configuration)
- Any defined selectors/locators from shared state or project adapter

### Optional

- Authentication configuration (cookies, JWT, API keys, OAuth)
- Test data fixtures (from test-data skill output)
- Mock configurations (from mocking skill output)
- Network interception rules

## Capabilities

### Browser Automation

- Launch browsers (chromium, firefox, webkit)
- Navigate to URLs
- Handle multiple tabs/windows
- Manage browser context (incognito-like isolation)

### Locators

- Use recommended Playwright locators (getByRole, getByText, getByLabel, getByPlaceholder, getByTestId)
- Prefer user-facing locators over XPath or CSS selectors
- Never invent selectors — use only those from project adapter or shared state
- Handle dynamic content with appropriate wait strategies

### Assertions

- Page assertions (URL, title, content, visibility, state)
- Element assertions (visible, hidden, enabled, disabled, checked, focused)
- Network assertions (response status, body content, timing)
- Accessibility assertions (where configured)

### Authentication

- Cookie-based authentication (set cookies in context)
- JWT token injection (if API-based auth)
- OAuth flow handling (where configured)
- Session persistence across tests (storage state)
- Never invent credentials — use only provided test credentials

### Fixtures

- Test fixtures for setup/teardown
- Shared test data setup
- Environment isolation per test
- Cleanup after tests

### Evidence Collection

- Screenshots on failure and on demand
- Trace recording for diagnostic playback
- Video recording where supported
- Console log capture
- Page load performance metrics

### Network Interception

- Intercept and mock API responses
- Block external domains
- Modify request/response headers
- Validate network traffic patterns

### Mocking

- Mock API endpoints
- Mock WebSocket connections
- Mock time/timeout behavior
- Mock third-party integrations

### Retries

- Configure retry logic for flaky scenarios
- Distinguish environment flakiness from product issues
- Report retry statistics

### Diagnostics

- Page errors (console errors, unhandled exceptions)
- Network failure analysis
- Performance bottleneck identification
- Accessibility violation reporting (where axe is configured)

## Rules

- Follow AGENTS.md and the project adapter
- Never invent selectors, URLs, or credentials
- Use only locators provided by the project adapter or shared state
- Prefer user-facing locators over implementation-specific ones
- Collect evidence for every test execution
- Report environment issues separately from product defects
- Never execute against production without explicit authorization
- Mark tests as blocked when environment or credentials are missing
- Do not hardcode waits — use Playwright's built-in waiting mechanisms

## Output

For each executed scenario:

- Test name and ID
- Pass/fail status
- Execution duration
- Evidence references (screenshot paths, trace paths, video paths)
- Console logs (if any errors)
- Network requests summary (if intercepted)
- Failure details (if failed)
- Blocked reason (if blocked)

## Failure Handling

- **Environment unavailable:** Mark test as blocked, record reason
- **Credentials missing:** Mark test as blocked, record reason
- **Selector not found:** Report as automation defect or product change
- **Flaky failure:** Retry per configuration, classify after retries exhausted
- **Browser crash:** Capture diagnostic evidence, mark as environment/infrastructure issue

## Safety Rules

- Never execute destructive actions without explicit authorization
- Never use real credentials in shared artifacts
- Never capture sensitive data in screenshots without masking
- Respect project safety configuration (production_execution, real_payments, destructive_database_operations)

## Project-Agnostic Behavior

This specialist works the same way regardless of the application under test. Only the project adapter changes:

- Different URLs → different navigation targets
- Different selectors → different element identification
- Different authentication → different auth approach
- Different test data → different fixture setup

The specialist never assumes a specific application structure.

## Examples

### Login Flow (generic)

```
1. Navigate to login page (URL from project adapter)
2. Fill email field (selector from shared state)
3. Fill password field (selector from shared state)
4. Click login button (selector from shared state)
5. Assert redirect to destination (URL from shared state)
6. Collect evidence (screenshot, trace)
```

### Form Validation

```
1. Navigate to form page
2. Submit form with empty required field
3. Assert validation error appears (selector from shared state)
4. Collect evidence
```

### API Interception

```
1. Set up route interception for API endpoint
2. Mock response (from mock configuration)
3. Trigger UI action that calls API
4. Assert UI behavior matches mock response
5. Validate request was made correctly
```
