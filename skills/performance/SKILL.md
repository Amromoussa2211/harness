---
name: performance
description: Performance testing foundation supporting k6, JMeter, Locust, and other performance testing tools for load, stress, endurance, and scalability testing.
version: 0.1.0
---

# Performance Testing Specialist

## Purpose

Provide a foundation for performance testing using tools like k6, JMeter, Locust, and others. This specialist handles test design for load, stress, endurance, and scalability scenarios, test execution, result collection, and performance metric analysis.

**Version 0.2.0 — Extended:** Now integrated with the QA Agent Harness execution flow. The execution stage generates request inventories from captured network data, generates k6 scripts, and attempts k6 execution. This specialist skill defines the capability; the execution stage implements the flow.

## When to Use

- The project adapter enables performance testing (performance.enabled = true)
- The story requires performance validation
- Performance requirements are defined
- Load, stress, endurance, or scalability testing is needed
- A request inventory is available from execution stage network capture

## Prerequisites

- Performance testing tool installed and configured (k6 preferred)
- Target environment available and configured for load testing
- Performance requirements or expectations defined
- Test data adequate for performance scenarios
- Monitoring/observability for the target system
- An approved request inventory from the execution stage

## Capabilities

### Load Testing

- Define expected load patterns
- Configure virtual users or requests per second
- Execute load tests via k6
- Collect response time metrics (p50, p90, p95, p99)
- Collect throughput metrics (http_reqs)
- Collect error rate metrics

### Stress Testing

- Define stress test boundaries
- Gradually increase load beyond normal
- Identify breaking points (only if evidence supports it)
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

### Network-to-Performance Pipeline (NEW in 0.2.0)

The execution stage now feeds performance testing via:

1. **Network Capture** — Playwright request/response events capture HTTP traffic during test execution.
2. **Sanitization** — All secrets (Authorization, Cookie, tokens, API keys) are replaced with `<REDACTED>` before persistence.
3. **Request Classification** — Captured requests are classified as business_api, authentication, static_asset, analytics, third_party, browser_internal, or unknown.
4. **Request Inventory** — Classified requests are written to `shared-state/<story>/performance/request-inventory.json`.
5. **k6 Script Generation** — k6 load-test.js and stress-test.js are generated from the approved request inventory.
6. **k6 Execution** — k6 tests are executed when k6 is available and the environment permits.

### Integration with Execution Stage

The performance testing flow is invoked as part of the Test Execution stage (Stage 10), specifically as sub-steps 10e–10g:

- 10e: Request Inventory Generation
- 10f: Performance Test Script Generation
- 10g: k6 Execution (Load Test + Stress Test)

The performance stage does NOT run as a separate top-level workflow stage. It is tracked as a sub-status within the execution stage: `execution.performance_status`.

## Rules

- Follow AGENTS.md and the project adapter
- Never run performance tests against production without explicit authorization
- Use dedicated performance test environments where possible
- Document performance test configuration
- Collect sufficient metrics for analysis
- Report performance results objectively
- Do NOT fabricate performance results
- Do NOT run k6 if k6 is not installed — report as BLOCKED

## Output

For each performance test:

- Test type (load, stress, endurance, etc.)
- Test configuration (VUs, duration, ramp-up)
- Metrics collected (response time, throughput, errors)
- Pass/fail against expectations (or "measured only — no threshold provided")
- Observations and anomalies
- Evidence references

## Failure Handling

- **Test environment unavailable:** Block performance testing
- **Tool not configured (k6 not installed):** Report as dependency blocker
- **Test inconclusive:** Report limitations, suggest improvements
- **Performance below expectations:** Report as finding, not failure
- **k6 scripts generated but not executed:** Report as blocked with reason

## Performance Test Artifacts

```
shared-state/<story>/performance/
  request-inventory.json    — classified request inventory
  load-test.js              — generated k6 load test script
  stress-test.js            — generated k6 stress test script
  results/
    load-summary.json       — parsed k6 load test output
    stress-summary.json     — parsed k6 stress test output
    raw/
      load-output.txt       — raw k6 stdout
      stress-output.txt     — raw k6 stdout
  reports/
    performance-report.md   — performance report
  graphs/
    latency.png             — latency over time (if data supports)
    throughput.png          — throughput over time (if data supports)
    error-rate.png          — error rate over time (if data supports)
```

## Safety Rules

- Never run performance tests that could affect production users
- Never use production credentials for load testing
- Respect rate limits and quotas
- Monitor test impact on target system
- Stop tests if target system shows distress
- Do NOT persist secrets in k6 scripts or reports

## Project-Agnostic Behavior

This specialist works the same way regardless of the target system. Only the project adapter changes:

- Different tools → different test syntax
- Different targets → different load patterns
- Different requirements → different pass criteria
- Different base URLs → different k6 script configuration

The skill itself contains NO company-specific information.

## k6 Dependency

k6 is the preferred performance testing engine. Before using k6:

1. Check whether k6 is installed (`k6 version`).
2. If not installed, report as a **dependency blocker**.
3. Do NOT install system-wide dependencies without explicit project permission.
4. If k6 is unavailable, performance testing is BLOCKED.

Do NOT replace k6 with a large custom load-testing framework.

## Examples

### k6 Load Test

```
1. Generate request inventory from captured network data
2. Classify requests (business_api selected, static_asset excluded)
3. Generate load-test.js from selected requests
4. Run: k6 run shared-state/<story>/performance/load-test.js
5. Collect metrics (http_req_duration, checks, iterations)
6. Compare against performance expectations or report "measured only"
7. Save results to shared-state/<story>/performance/results/
8. Generate performance-report.md
```

### k6 Stress Test

```
1. Use same request inventory as load test
2. Generate stress-test.js with increasing VU stages
3. Run: k6 run shared-state/<story>/performance/stress-test.js
4. Monitor latency progression, error rate progression
5. Identify degradation point only if evidence supports it
6. Save results to shared-state/<story>/performance/results/
```

### Performance Test Design

```
1. Identify performance-critical scenarios from requirement
2. Define expected response times (from project adapter or "not specified")
3. Define expected throughput (from project adapter or "not specified")
4. Define acceptable error rates (from project adapter or "not specified")
5. Design test data for realistic load
6. Configure test duration and ramp-up
```

### Network Capture to Request Inventory

```
1. Playwright execution captures requests via context.on('request') and context.on('response')
2. Each request is sanitized: Authorization → <REDACTED>, Cookie → <REDACTED>, tokens → <REDACTED>
3. Requests are classified: business_api, authentication, static_asset, analytics, third_party, browser_internal, unknown
4. Selected requests (business_api, eligible authentication) are written to request-inventory.json
5. Excluded requests are recorded with exclusion reasons
6. request-inventory.json is used to generate k6 scripts
```
