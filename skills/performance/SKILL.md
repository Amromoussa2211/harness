---
name: performance
description: Performance testing foundation supporting k6, JMeter, Locust, and other performance testing tools for load, stress, endurance, and scalability testing.
version: 0.1.0
---

# Performance Testing Specialist

## Purpose

Provide a foundation for performance testing using tools like k6, JMeter, Locust, and others. This specialist handles test design for load, stress, endurance, and scalability scenarios, test execution, result collection, and performance metric analysis.

## When to Use

- The project adapter enables performance testing (performance.enabled = true)
- The story requires performance validation
- Performance requirements are defined
- Load, stress, endurance, or scalability testing is needed

## Prerequisites

- Performance testing tool installed and configured
- Target environment available and configured for load testing
- Performance requirements or expectations defined
- Test data adequate for performance scenarios
- Monitoring/observability for the target system

## Capabilities

### Load Testing

- Define expected load patterns
- Configure virtual users or requests per second
- Execute load tests
- Collect response time metrics
- Collect throughput metrics
- Collect error rate metrics

### Stress Testing

- Define stress test boundaries
- Gradually increase load beyond normal
- Identify breaking points
- Document system behavior under stress
- Validate graceful degradation

### Endurance Testing

- Define endurance test duration
- Run sustained load for extended period
- Monitor for memory leaks or degradation
- Validate stable performance over time

### Scalability Testing

- Define scaling scenarios
- Test with increasing load
- Validate scaling behavior
- Measure resource utilization

### Spike Testing

- Test sudden load increases
- Validate system response to spikes
- Test recovery after spikes

### Test Design

- Define performance scenarios from requirements
- Set performance expectations (response time, throughput, error rate)
- Design test data for performance scenarios
- Configure test duration and ramp-up patterns

## Rules

- Follow AGENTS.md and the project adapter
- Never run performance tests against production without explicit authorization
- Use dedicated performance test environments where possible
- Document performance test configuration
- Collect sufficient metrics for analysis
- Report performance results objectively

## Output

For each performance test:

- Test type (load, stress, endurance, etc.)
- Test configuration (VUs, duration, ramp-up)
- Metrics collected (response time, throughput, errors)
- Pass/fail against expectations
- Observations and anomalies
- Evidence references

## Failure Handling

- **Test environment unavailable:** Block performance testing
- **Tool not configured:** Report as setup issue
- **Test inconclusive:** Report limitations, suggest improvements
- **Performance below expectations:** Report as finding, not failure

## Safety Rules

- Never run performance tests that could affect production users
- Never use production credentials for load testing
- Respect rate limits and quotas
- Monitor test impact on target system
- Stop tests if target system shows distress

## Project-Agnostic Behavior

This specialist works the same way regardless of the target system. Only the project adapter changes:

- Different tools → different test syntax
- Different targets → different load patterns
- Different requirements → different pass criteria

## Examples

### k6 Load Test

```
1. Write k6 script defining VUs and test scenario
2. Configure target URL from project adapter
3. Run: k6 run script.js
4. Collect metrics (http_req_duration, checks, iterations)
5. Compare against performance expectations
6. Report results
```

### JMeter Test

```
1. Create JMeter test plan
2. Define thread group (users, ramp-up, duration)
3. Define HTTP requests
4. Add listeners for metrics
5. Run test
6. Collect results from listeners
7. Analyze and report
```

### Performance Test Design

```
1. Identify performance-critical scenarios
2. Define expected response times
3. Define expected throughput
4. Define acceptable error rates
5. Design test data for realistic load
6. Configure test duration and ramp-up
```
