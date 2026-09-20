---
name: api
description: REST and GraphQL API testing specialist for validating API endpoints, authentication, headers, payloads, schema validation, negative tests, and chained requests.
version: 0.1.0
---

# API Specialist

## Purpose

Execute API testing for REST and GraphQL endpoints. This specialist validates API behavior including request/response contracts, authentication, headers, payload structures, status codes, error responses, schema conformance, negative test cases, and request chaining.

## When to Use

- The story requires validating API behavior
- The project adapter declares a REST API (api.rest = true) or GraphQL API (api.graphql = true)
- The test design assigns API or component test levels to scenarios
- API endpoint information is available from project adapter or shared state
- Schema validation is required

## Prerequisites

- HTTP client library available (fetch, axios, playwright APIRequestContext, etc.)
- API base URL from project adapter or environment configuration
- API endpoint information from project adapter, shared state, or API documentation
- Authentication configuration if required
- Any API schemas or specifications (OpenAPI, GraphQL schema) if available

## Inputs

### Required

- Test scenarios from test-design/output.md
- Project adapter (projects/<project-name>/project.yaml)
- API base URL (from project adapter or environment configuration)
- API endpoint definitions (from project adapter, shared state, or API docs)

### Optional

- Authentication tokens or API keys (from project adapter or secrets)
- Request/response schemas for validation
- OpenAPI specification or GraphQL schema
- Mock configurations
- Test data fixtures

## Capabilities

### REST API Testing

- Send HTTP requests (GET, POST, PUT, PATCH, DELETE)
- Set request headers (Content-Type, Authorization, custom headers)
- Construct request payloads (JSON, form data, etc.)
- Validate response status codes
- Validate response headers
- Validate response body structure and content
- Validate response time/performance

### GraphQL Testing

- Send GraphQL queries and mutations
- Validate query structure
- Validate response data shape
- Handle GraphQL errors
- Test subscription support where configured

### Authentication

- API key authentication (header or query param)
- Bearer token authentication (JWT)
- OAuth 2.0 flows where configured
- Session-based authentication (cookies)
- Basic authentication where configured
- Never invent credentials — use only provided test credentials

### Header Validation

- Required headers presence
- Header value correctness
- Security headers (CORS, CSP, etc.) where relevant
- Content-Type validation

### Payload Validation

- Request payload structure
- Request payload content
- Response payload structure
- Response payload content
- Schema conformance (where schema available)

### Negative Testing

- Invalid input payloads
- Missing required fields
- Out-of-range values
- Malformed payloads
- Authentication failures
- Authorization failures (unauthorized access attempts)
- Rate limit responses

### Chained Requests

- Sequence multiple API calls
- Use response data from one request in another
- Validate state changes across calls
- Test transactional behavior where applicable

### Schema Validation

- Validate responses against JSON Schema
- Validate responses against OpenAPI schema
- Validate GraphQL responses against schema
- Report schema violations

## Rules

- Follow AGENTS.md and the project adapter
- Never invent API endpoints, contracts, or credentials
- Use only API information from project adapter, shared state, or provided documentation
- Validate against actual API behavior, not assumed behavior
- Collect request and response evidence for debugging
- Report environment issues separately from product defects
- Never execute destructive API operations without explicit authorization
- Mark tests as blocked when API information or credentials are missing

## Output

For each executed scenario:

- Test name and ID
- API endpoint tested
- HTTP method
- Pass/fail status
- Request details (headers, payload — exclude sensitive data)
- Response details (status, headers, body — exclude sensitive data)
- Validation results
- Execution duration
- Evidence references
- Failure details (if failed)
- Blocked reason (if blocked)

## Failure Handling

- **API unavailable:** Mark test as blocked, record reason
- **Credentials missing:** Mark test as blocked, record reason
- **Unexpected response:** Capture full request/response, classify failure
- **Schema violation:** Report as product defect or schema mismatch
- **Authentication failure:** Verify credentials, classify as config or product issue
- **Timeout:** Capture timing evidence, classify as environment or product issue

## Safety Rules

- Never execute destructive operations (DELETE, PUT that modifies data) without explicit authorization
- Never use real credentials in shared artifacts
- Never send real payment data without explicit authorization
- Respect project safety configuration
- Mask sensitive data in evidence (tokens, passwords, personal data)

## Project-Agnostic Behavior

This specialist works the same way regardless of the API under test. Only the project adapter changes:

- Different base URLs → different request targets
- Different endpoints → different request paths
- Different authentication → different auth headers
- Different schemas → different validation rules

The specialist never assumes a specific API structure.

## Examples

### GET Request Validation

```
1. Construct GET request to /api/resource/{id}
2. Add authentication header (from provided credentials)
3. Send request
4. Validate status 200
5. Validate response body structure
6. Validate expected fields present
7. Collect evidence (request/response logs)
```

### POST Request with Payload

```
1. Construct POST request to /api/resource
2. Add authentication header
3. Add Content-Type header
4. Construct valid payload (from test data)
5. Send request
6. Validate status 201 or 200
7. Validate response contains created resource
8. Validate response matches expected schema
9. Collect evidence
```

### Negative Test — Invalid Input

```
1. Construct POST request to /api/resource
2. Add authentication header
3. Construct payload with missing required field
4. Send request
5. Validate status 400
6. Validate error response structure
7. Validate error message indicates the missing field
8. Collect evidence
```

### Chained Requests

```
1. Create resource via POST /api/resources
2. Extract resource ID from response
3. GET /api/resources/{id} using extracted ID
4. Validate returned resource matches created resource
5. Update resource via PUT /api/resources/{id}
6. Validate update took effect
7. Collect evidence for each step
```
