---
name: contract-testing
description: Contract testing capabilities for validating API contracts, OpenAPI schema conformance, GraphQL schema validation, Pact-style consumer-driven contracts, and interface agreement verification.
version: 0.1.0
---

# Contract Testing Specialist

## Purpose

Provide contract testing capabilities for validating that APIs and services conform to their defined contracts. This specialist handles OpenAPI schema validation, GraphQL schema validation, Pact-style consumer-driven contract testing, and interface agreement verification between services.

## When to Use

- API contracts are defined (OpenAPI, GraphQL schema, etc.)
- Consumer-driven contract testing is required
- Interface agreement between services needs validation
- Schema conformance testing is needed
- API evolution impact needs assessment

## Prerequisites

- API contract definitions (OpenAPI spec, GraphQL schema, Pact files, etc.)
- Understanding of consumer expectations
- Contract testing tool appropriate to the project
- Access to API or service under test

## Capabilities

### OpenAPI Schema Validation

- Validate API responses against OpenAPI schema
- Validate request formats against OpenAPI schema
- Check for schema violations
- Identify deprecated or removed endpoints
- Validate parameter types and constraints

### GraphQL Schema Validation

- Validate GraphQL queries against schema
- Validate GraphQL response shapes
- Check for schema changes
- Validate type conformance
- Identify breaking schema changes

### Consumer-Driven Contract Testing

- Define consumer expectations as contracts
- Validate provider satisfies contracts
- Identify contract violations
- Track contract versions
- Support Pact or similar frameworks

### Interface Agreement Verification

- Validate service-to-service interfaces
- Check request/response agreements
- Verify data format agreements
- Validate error handling agreements

### Breaking Change Detection

- Compare contract versions
- Identify breaking changes
- Flag incompatible changes
- Suggest migration paths where possible

## Rules

- Follow AGENTS.md and the project adapter
- Use actual contract definitions, not assumed contracts
- Validate against the contract, not against assumed behavior
- Report contract violations clearly
- Document contract version used for testing
- Never invent contract definitions

## Output

For each contract validation:

- Contract used (name, version)
- Validation result (pass/fail)
- Violations found (if any)
- Breaking changes identified (if any)
- Evidence references

## Failure Handling

- **Contract not found:** Report as missing information, block testing
- **Schema validation fails:** Report violation, classify as product defect or contract mismatch
- **Contract version mismatch:** Report version discrepancy
- **Breaking change detected:** Report as risk, flag for review

## Safety Rules

- Never modify contracts without authorization
- Never ignore contract violations
- Document all contract assumptions
- Version contracts appropriately

## Project-Agnostic Behavior

This specialist works the same way regardless of the contract format. Only the project adapter changes:

- Different contract formats → different validation tools
- Different services → different contract targets
- Different consumers → different contract expectations

## Examples

### OpenAPI Response Validation

```
1. Load OpenAPI specification
2. Make API request
3. Validate response status matches spec
4. Validate response body matches schema
5. Validate response headers match spec
6. Report any violations
```

### GraphQL Query Validation

```
1. Load GraphQL schema
2. Validate query against schema
3. Execute query
4. Validate response shape matches schema
5. Validate field types are correct
6. Report any violations
```

### Consumer Contract Validation

```
1. Load consumer contract (Pact file)
2. Run provider verification against contract
3. Validate all interactions pass
4. Report any contract violations
5. Flag breaking changes if detected
```
