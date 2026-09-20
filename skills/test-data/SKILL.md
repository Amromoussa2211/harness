---
name: test-data
description: Reusable test data strategy supporting fixtures, generated data, deterministic data, unique data, cleanup, API setup, database setup, and environment-specific data.
version: 0.1.0
---

# Test Data Specialist

## Purpose

Provide a reusable test data strategy for QA automation. This specialist handles test fixtures, generated data, deterministic data, unique data generation, cleanup strategies, API-based data setup, database-based data setup where allowed, and environment-specific data management.

## When to Use

- Test scenarios require specific data inputs
- Test data setup is needed before execution
- Data cleanup is required after tests
- Unique or deterministic data is needed for test isolation
- API or database setup is required for test preconditions

## Prerequisites

- Test data requirements from specification or test design
- Data creation mechanisms from project adapter or shared state
- API access for data setup (if applicable)
- Database access for data setup (if applicable and authorized)
- Any existing fixtures or data utilities from the project

## Capabilities

### Fixtures

- Use existing project fixtures where available
- Create test fixtures for repeatable data states
- Organize fixtures by test scenario
- Version fixtures with test code

### Generated Data

- Generate data programmatically for tests
- Use deterministic generation for reproducible tests
- Use random generation where uniqueness is needed
- Generate valid data that meets business rules
- Generate invalid data for negative tests

### Deterministic Data

- Use fixed seeds for random generation
- Create predictable data sequences
- Ensure same data produces same test results
- Document data generation logic

### Unique Data

- Generate unique identifiers for test isolation
- Use timestamps, UUIDs, or counters for uniqueness
- Ensure test data does not conflict between tests
- Clean up unique data after tests

### Cleanup Strategies

- Clean up test data after each test
- Clean up test data after test suite
- Use transactions for automatic rollback where supported
- Use API delete endpoints where available
- Use database cleanup where authorized
- Document cleanup approach

### API Data Setup

- Create test data via API calls before tests
- Use API to set up preconditions
- Use API to clean up after tests
- Validate data creation via API response

### Database Data Setup

- Insert test data directly via database (where authorized)
- Use database scripts for complex setups
- Use database transactions for isolation
- Clean up database data after tests (where authorized)

### Environment-Specific Data

- Use different data for different environments
- Configure data via environment variables
- Adapt data to environment capabilities
- Document environment-specific data needs

## Rules

- Follow AGENTS.md and the project adapter
- Never invent test data values that could be real (use obvious test values)
- Never use real production data in tests
- Never create data that could affect real users without authorization
- Clean up test data after tests unless project configuration says otherwise
- Use deterministic data where reproducibility matters
- Use unique data where test isolation matters
- Document data dependencies clearly

## Output

For each data setup operation:

- Data created (description, not actual sensitive values)
- Creation method (API, database, fixture, generated)
- Data used by which tests
- Cleanup method and status
- Any data dependencies

## Failure Handling

- **Data setup fails:** Report as test data issue, block affected tests
- **Data cleanup fails:** Report, attempt recovery, document residual state
- **Data conflict:** Report as test data issue, adjust data strategy
- **Environment data mismatch:** Report as environment issue

## Safety Rules

- Never use real personal data (PII) in test data
- Never create real financial transactions without authorization
- Never modify production data without explicit authorization
- Never leave test data in production environments
- Use obvious test values (test@example.com, not real emails)
- Respect project safety configuration

## Project-Agnostic Behavior

This specialist works the same way regardless of the project. Only the project adapter changes:

- Different data models → different data structures
- Different creation mechanisms → different setup approaches
- Different cleanup requirements → different cleanup strategies
- The data management patterns are the same: create, use, clean up

## Examples

### Generated Unique User

```
1. Generate unique email: test-{timestamp}@example.com
2. Generate unique username: testuser-{counter}
3. Generate valid password meeting policy
4. Create user via API (or database if authorized)
5. Use user in tests
6. Clean up user after tests
```

### Deterministic Product Data

```
1. Use fixed seed for random generation
2. Generate product with specific attributes
3. Product name: "Test Product {sequence}"
4. Product price: fixed value
5. Product category: test category
6. Use product in tests
7. Clean up product after tests
```

### API-Based Precondition Setup

```
1. Identify required precondition (e.g., existing order)
2. Create order via API with test data
3. Capture order ID from response
4. Use order ID in test scenarios
5. Clean up order after tests via API delete
```

### Database Fixture Loading

```
1. Identify fixture file with test data
2. Load fixture into database (if authorized)
3. Verify data loaded correctly
4. Use fixture data in tests
5. Clean up fixture data after tests
```
