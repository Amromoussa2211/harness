---
name: authentication
description: Reusable authentication and authorization testing capabilities supporting session auth, cookies, JWT, API keys, OAuth, MFA/OTP, and RBAC permission testing.
version: 0.1.0
---

# Authentication & Authorization Specialist

## Purpose

Provide reusable capabilities for testing authentication and authorization mechanisms. This specialist handles session-based auth, cookie management, JWT token handling, API key authentication, OAuth flows where applicable, MFA/OTP strategies, and role-based access control (RBAC) permission testing.

## When to Use

- The story involves authentication or authorization
- The project requires testing login, token handling, or permission checks
- The test design identifies authentication or authorization scenarios
- API or UI tests require authenticated access

## Prerequisites

- Authentication mechanism information from project adapter or shared state
- Test credentials from project adapter or secrets (never invent)
- Understanding of the auth flow from discovery or specification
- Any required auth configuration (OAuth clients, API keys, etc.)

## Capabilities

### Session Authentication

- Handle session-based login flows
- Manage session cookies
- Validate session creation and destruction
- Test session timeout behavior
- Test concurrent session handling

### Cookie Management

- Set cookies in browser context
- Read cookies from response
- Validate cookie attributes (secure, httponly, samesite, expiry)
- Test cookie persistence
- Test cookie deletion on logout

### JWT Handling

- Obtain JWT tokens (via login or direct provision)
- Include JWT in request headers
- Validate JWT structure and claims
- Test expired token handling
- Test invalid token handling
- Test token refresh flows where applicable

### API Key Authentication

- Include API keys in requests (header, query param, body)
- Test invalid API key handling
- Test missing API key handling
- Test key rotation where applicable
- Validate key scoping/permissions

### OAuth Testing

- Test OAuth flow initiation
- Test OAuth callback handling
- Test OAuth token exchange
- Test OAuth user info retrieval
- Test OAuth logout/revocation
- Note: Full OAuth testing requires identity provider configuration

### MFA/OTP Strategy

- Test MFA challenge flows
- Test OTP generation and validation
- Test OTP expiry
- Test OTP retry limits
- Test MFA bypass scenarios (where authorized)
- Note: OTP delivery requires email/SMS/in-app integration

### RBAC Permission Testing

- Test access with different roles
- Test unauthorized access attempts
- Test privilege escalation attempts
- Validate role-based UI differences
- Validate role-based API access differences
- Test permission inheritance where applicable

### Permission Testing

- Verify authenticated users can access their own resources
- Verify users cannot access other users' resources
- Verify admin users have appropriate elevated access
- Test anonymous access restrictions
- Test authenticated but unauthorized access

## Rules

- Follow AGENTS.md and the project adapter
- Never invent credentials, tokens, or auth configuration
- Use only auth information from project adapter or shared state
- Never use real credentials in shared artifacts
- Mark tests as blocked when auth configuration is unavailable
- Respect project safety configuration
- Test auth failures without attempting to bypass security

## Output

For each executed scenario:

- Test name and ID
- Authentication mechanism tested
- Pass/fail status
- Auth setup used (description, not actual credentials)
- Validation results
- Evidence references
- Failure details (if failed)
- Blocked reason (if blocked)

## Failure Handling

- **Auth endpoint unavailable:** Mark test as blocked
- **Credentials missing:** Mark test as blocked
- **Unexpected auth behavior:** Capture evidence, classify as product defect or config issue
- **Token handling failure:** Capture token details (sanitized), classify appropriately
- **Permission unexpected:** Capture role/permission details, classify as product defect

## Safety Rules

- Never attempt to bypass authentication or authorization
- Never use real user credentials
- Never test auth attacks without explicit authorization
- Never expose tokens or credentials in shared artifacts
- Respect project safety configuration

## Project-Agnostic Behavior

This specialist works the same way regardless of the auth system. Only the project adapter changes:

- Different auth mechanisms → different handling approaches
- Different credentials → different test inputs
- Different permissions → different access tests
- The testing patterns are the same: authenticate, act, validate access

## Examples

### Session Login Test

```
1. Navigate to login page
2. Enter valid credentials (from test data)
3. Submit login form
4. Validate successful authentication (redirect, cookie, token)
5. Validate session is active
6. Perform authenticated action
7. Validate access granted
8. Log out
9. Validate session is destroyed
```

### JWT API Authentication

```
1. Obtain JWT token (via login API or direct provision)
2. Include token in Authorization header
3. Make authenticated API request
4. Validate request succeeds
5. Test with expired token
6. Validate expired token is rejected
7. Test with invalid token
8. Validate invalid token is rejected
```

### RBAC Permission Test

```
1. Authenticate as User A (role: standard)
2. Attempt to access User B's resource
3. Validate access is denied
4. Authenticate as Admin
5. Attempt to access User B's resource
6. Validate access is granted (if admin has access)
7. Collect evidence for each step
```

### MFA Login Flow

```
1. Navigate to login page
2. Enter valid credentials
3. Submit login form
4. Validate MFA challenge is presented
5. Enter valid OTP (from test data or generated)
6. Submit MFA challenge
7. Validate successful authentication
8. Collect evidence
```
