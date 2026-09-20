---
name: mocking
description: Test mocking capabilities for isolating tests from external dependencies, simulating API responses, stubbing services, and controlling test environment behavior.
version: 0.1.0
---

# Mocking Specialist

## Purpose

Provide test mocking capabilities for isolating tests from external dependencies. This specialist handles API response mocking, service stubbing, time manipulation, network condition simulation, and controlled test environment behavior.

## When to Use

- Tests need to isolate from external services
- API responses need to be controlled for test scenarios
- External dependencies are unavailable or unreliable for testing
- Specific response scenarios need to be tested (errors, delays, edge cases)
- Tests need to run without affecting real systems

## Prerequisites

- Understanding of what needs to be mocked from test design
- Mocking tool appropriate to the test framework
- Knowledge of the interfaces being mocked
- Expected mock behavior from specification

## Capabilities

### API Response Mocking

- Mock REST API responses
- Mock GraphQL responses
- Mock webhook callbacks
- Define mock response status, headers, and body
- Create mock variations for different scenarios

### Service Stubbing

- Stub external service calls
- Replace real service with test double
- Control stub behavior per test
- Validate calls made to stubs

### Time Manipulation

- Mock current time for time-dependent tests
- Simulate time passage
- Test expiry behavior
- Test timeout behavior
- Test time-based triggers

### Network Condition Simulation

- Simulate network delays
- Simulate network failures
- Simulate slow responses
- Simulate partial responses
- Test application behavior under network stress

### State Mocking

- Mock application state
- Mock user session state
- Mock feature flags
- Mock configuration values

### Mock Validation

- Verify mock was called
- Verify mock was called with correct parameters
- Verify mock was called expected number of times
- Verify order of mock calls where relevant

## Rules

- Follow AGENTS.md and the project adapter
- Use mocks to isolate tests, not to hide real problems
- Document what is mocked and why
- Prefer testing against real services where feasible
- Don't mock the system under test
- Clean up mocks after tests
- Validate that mocks represent realistic scenarios

## Output

For each mocked scenario:

- What was mocked
- Mock configuration (behavior, responses)
- Why the mock was used
- Validation that mocks behaved as expected

## Failure Handling

- **Mock not working:** Debug mock configuration, check framework compatibility
- **Mock leaking to other tests:** Ensure proper cleanup, check isolation
- **Mock unrealistic:** Adjust mock to better represent real behavior
- **Over-mocking:** Review if test should use real service instead

## Safety Rules

- Never mock production systems without authorization
- Never use mocks to hide security issues
- Never mock safety-critical validations
- Document all mocks for test review

## Project-Agnostic Behavior

This specialist works the same way regardless of the project. Only the project adapter changes:

- Different APIs → different mock targets
- Different services → different stub approaches
- Different frameworks → different mocking tools

## Examples

### API Response Mock

```
1. Identify API endpoint to mock
2. Configure mock response (status 200, expected body)
3. Run test that calls the API
4. Verify test uses mock response
5. Verify mock was called
6. Clean up mock
```

### Error Scenario Mock

```
1. Identify API endpoint to mock
2. Configure mock to return error (status 500)
3. Run test that handles the error
4. Verify application handles error gracefully
5. Clean up mock
```

### Time-Based Test

```
1. Mock current time to specific date
2. Run test that depends on time
3. Verify behavior for that time
4. Advance mocked time
5. Verify time-dependent behavior changes
6. Clean up mock
```
