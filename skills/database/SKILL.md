---
name: database
description: Database testing specialist for SQL and NoSQL validation, data integrity checks, state verification, and API/UI/database comparison.
version: 0.1.0
---

# Database Specialist

## Purpose

Execute database testing for SQL and NoSQL databases. This specialist validates database state, data integrity, schema conformance, data transformation correctness, and consistency between database state and API/UI behavior.

## When to Use

- The project adapter declares a database (database.enabled = true)
- The test design assigns database test levels to scenarios
- Database validation is required to verify API or UI behavior
- Data integrity checks are needed
- State verification requires direct database access

## Prerequisites

- Database connection details from project adapter or environment configuration
- Database client library appropriate to database type (SQL or NoSQL)
- Database credentials from project adapter or secrets (never invent)
- Database schema information if available
- Expected state definitions from test design or specification

## Inputs

### Required

- Test scenarios from test-design/output.md
- Project adapter (projects/<project-name>/project.yaml)
- Database connection details (from project adapter or environment)
- Database credentials (from project adapter or secrets)

### Optional

- Database schema definition
- Expected state definitions
- SQL queries or NoSQL collection operations (from project adapter or shared state)
- API/UI test results for comparison

## Capabilities

### SQL Database Testing

- Connect to SQL databases (PostgreSQL, MySQL, SQLite, etc.)
- Execute SELECT queries to verify state
- Execute INSERT/UPDATE/DELETE for test setup (with authorization)
- Validate query results against expected values
- Verify data types and constraints
- Check referential integrity
- Validate transaction behavior

### NoSQL Database Testing

- Connect to NoSQL databases (MongoDB, Redis, etc.)
- Query collections/documents
- Validate document structure
- Verify indexes where relevant
- Check data consistency

### Data Validation

- Verify record existence
- Verify record content (field values)
- Verify record counts
- Verify relationship integrity
- Verify computed values (aggregates, sums, etc.)
- Verify timestamp handling
- Verify null/missing field handling

### Integrity Checks

- Primary key uniqueness
- Foreign key constraints
- Unique constraints
- Check constraints
- Data type validation
- Required field validation

### State Verification

- Verify database state before test
- Verify database state after test
- Compare expected vs actual state
- Track state changes during test

### API/UI/Database Comparison

- Compare API response data with database state
- Compare UI display data with database state
- Identify discrepancies between layers
- Validate data flows correctly through layers

### Test Data Setup

- Create test records (with authorization)
- Modify test records (with authorization)
- Delete test records (with authorization)
- Clean up after tests
- Use transactions for isolation where supported

## Rules

- Follow AGENTS.md and the project adapter
- Never invent database schemas, credentials, or connection details
- Use only database information from project adapter or shared state
- Never execute destructive operations without explicit authorization
- Collect query and result evidence for debugging
- Report environment issues separately from data issues
- Mark tests as blocked when database access is unavailable
- Clean up test data after tests unless project configuration says otherwise

## Output

For each executed scenario:

- Test name and ID
- Database type and connection used
- Pass/fail status
- Queries executed (sanitized)
- Query results (sanitized)
- Validation results
- Evidence references
- Data state before/after (if relevant)
- Failure details (if failed)
- Blocked reason (if blocked)

## Failure Handling

- **Database unavailable:** Mark test as blocked, record reason
- **Credentials missing:** Mark test as blocked, record reason
- **Query failure:** Capture error, classify as environment or product issue
- **Data mismatch:** Capture expected vs actual, classify as product defect or test data issue
- **Connection failure:** Capture connection details (sanitized), classify as environment issue

## Safety Rules

- Never execute destructive operations (DELETE, DROP, TRUNCATE) on production without explicit authorization
- Never use real production credentials in shared artifacts
- Never expose sensitive data in evidence (PII, passwords, tokens)
- Respect project safety configuration (destructive_database_operations)
- Use transactions or test-specific data to avoid affecting production data
- Clean up test data after tests

## Project-Agnostic Behavior

This specialist works the same way regardless of the database under test. Only the project adapter changes:

- Different database types → different client libraries
- Different schemas → different queries
- Different credentials → different authentication
- Different data → different validation values

The specialist never assumes a specific database structure.

## Examples

### Verify Record Existence

```
1. Connect to database (connection from project adapter)
2. Execute SELECT query to find record by identifier
3. Validate record exists (or doesn't exist for negative test)
4. Validate record fields match expected values
5. Collect evidence (query, result)
```

### Verify Data Integrity After API Call

```
1. Execute API call that should create a record
2. Connect to database
3. Query for the created record
4. Validate record exists in database
5. Validate database fields match API response
6. Collect evidence (API response, database query, database result)
```

### Verify State Change

```
1. Capture database state before operation (SELECT)
2. Execute operation (API call or UI action)
3. Capture database state after operation (SELECT)
4. Compare before/after states
5. Validate expected changes occurred
6. Validate no unexpected changes occurred
7. Collect evidence
```

### Data Cleanup

```
1. Identify test data created during test
2. Delete test data (if project configuration allows)
3. Verify deletion took effect
4. Record cleanup in test output
```
