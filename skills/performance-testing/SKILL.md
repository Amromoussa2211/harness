---
name: performance-testing
description: >
  Reusable performance testing skill for the QA Agent Harness.
  Defines how HTTP request inventory, classification, sanitization,
  k6 script generation, load testing, stress testing, threshold
  evaluation, report generation, and graph generation work.
  Company-independent — contains no URLs, credentials, selectors,
  or business rules.
version: 0.2.0
---

# Performance Testing Skill

## Purpose

Provide a reusable, project-independent performance testing capability
that the QA Agent Harness execution flow can invoke after test execution
and network capture.

This skill defines **how** performance testing works. It does NOT contain
project-specific endpoints, payloads, credentials, or thresholds.

## When Invoked

The performance testing flow is invoked after:
  1. Test Execution has produced executable test specs and/or captured
     network activity.
  2. A request inventory has been generated from captured network data,
     OR an approved API request inventory is available from the project
     adapter or shared state.

The performance testing flow may also be invoked standalone when a story
explicitly requires performance validation and an approved request
inventory exists.

## Prerequisites

Before any performance test executes, ALL of these must be true:

- A performance testing tool (k6 preferred) is available.
- An approved request inventory exists in shared state.
- The target environment is declared in the project adapter and available.
- The project adapter's safety configuration permits performance execution.
- No company-specific information has been invented.

If any prerequisite is missing, the performance stage is **BLOCKED** with
the specific reason recorded. No results are fabricated.

## Tool Selection

### Preferred: k6

k6 is the preferred performance testing engine. It is a lightweight,
scriptable load testing tool that uses JavaScript for scenario definition.

Before using k6:
  1. Check whether k6 is installed (`k6 version`).
  2. If not installed, report as a **dependency blocker**.
  3. Do NOT install system-wide dependencies without explicit project
     permission.
  4. If k6 is unavailable, the performance stage is BLOCKED.

### Fallback

If k6 is not available and the project adapter does not permit installation,
the performance stage is BLOCKED. Do NOT replace k6 with a large custom
load-testing framework.

## Flow Overview

```
Request Inventory
  → Request Classification
  → Request Sanitization (already done at capture time)
  → Performance Scenario Generation
  → Load Test (k6)
  → Stress Test (k6)
  → Result Collection
  → Threshold Evaluation
  → Report Generation
  → Graph Generation
```

## Step 1: Request Inventory

**Source:** `shared-state/<story>/execution/network/network-requests.json`
(or equivalent captured request data)

**Output:** `shared-state/<story>/performance/request-inventory.json`

The request inventory is a structured list of all captured requests with
classification and performance selection flags.

### Inventory Fields

For each request:

```json
{
  "method": "GET|POST|PUT|DELETE|PATCH",
  "url": "sanitized URL with secrets replaced by <REDACTED>",
  "category": "business_api | authentication | static_asset | analytics | third_party | browser_internal | unknown",
  "selected_for_performance": true|false,
  "reason": "why selected or why excluded",
  "source_artifact": "shared-state/<story>/execution/network/network-requests.json"
}
```

### Request Classification Categories

| Category | Description | Performance Eligible |
|---|---|---|
| `business_api` | Application/business API endpoints | Yes — primary target |
| `authentication` | Login, token, session endpoints | Yes — if explicitly allowed |
| `static_asset` | CSS, JS, images, fonts | No — exclude |
| `analytics` | Google Analytics, telemetry, tracking | No — exclude |
| `third_party` | External services not owned by project | No — exclude |
| `browser_internal` | Browser-internal requests | No — exclude |
| `unknown` | Cannot classify | Review required |

### Selection Rules

Select for performance testing ONLY:
  - Business API requests related to the story.
  - Authentication requests when explicitly permitted by the project
    adapter or story scope.
  - Critical requests identified in the test design.

Do NOT select:
  - Static assets (images, CSS, JS, fonts).
  - Analytics/telemetry/tracking requests.
  - Third-party requests not owned by the project.
  - Browser-internal requests.

If a request requires a request body but the body cannot be safely
captured or reconstructed, mark `selected_for_performance: false` with
reason `"request body unavailable — cannot safely reconstruct"`.

## Step 2: Request Sanitization

**Note:** Sanitization is performed at capture time (see execution skill),
not repeated here. The performance skill verifies that captured data has
been sanitized before using it.

Before using any captured request data, verify:
  - No `Authorization` header values are present.
  - No `Cookie` or `Set-Cookie` header values are present.
  - No API keys, bearer tokens, session tokens, or passwords are present.
  - No payment secrets are present.

If unsanitized data is found, the request MUST be sanitized before use.
Replace secret values with `<REDACTED>`.

**NEVER** copy original secrets into:
  - k6 scripts
  - Performance reports
  - Graphs
  - Any artifact in shared state

## Step 3: Performance Scenario Generation

Generate k6 script(s) from the approved request inventory.

### Output Files

```
shared-state/<story>/performance/
  load-test.js       — k6 load test scenario
  stress-test.js     — k6 stress test scenario
```

### Script Structure

Each k6 script:
  - Imports only k6 stdlib modules.
  - Defines scenarios from the approved request inventory.
  - Uses configurable VUs and duration (see Step 5).
  - Does NOT hardcode company-specific endpoints.
  - Does NOT invent request payloads.
  - Includes clear comments marking where project-specific config
    (base URL, headers) must be supplied.

### When Script Generation Is Blocked

If a request is selected for performance but:
  - The HTTP method is unknown.
  - The URL path is unknown.
  - The request body is required but unavailable.

Then mark that request as blocked in the inventory and do NOT generate
a k6 scenario for it. Document the blocker.

## Step 4: Load Test

Execute a configurable load test scenario using k6.

### Load Test Configuration

Configuration comes from a performance config file or safe defaults.
Do NOT hardcode aggressive traffic values.

**Safe default conceptual values (actual values must be configurable):**

```
users:
  baseline: 1
  load: 5
  peak: 10
duration:
  ramp_up: 30s
  steady: 60s
  ramp_down: 30s
```

These are examples only. The project adapter or performance config file
must provide actual values when performance execution is permitted.

### Load Test Execution

```
k6 run shared-state/<story>/performance/load-test.js
```

Capture:
  - `http_req_duration` (p50, p90, p95, p99)
  - `http_reqs` (throughput)
  - `checks` (success/failure rate)
  - `iterations`
  - Error count and rate

### Load Test Output

```
shared-state/<story>/performance/results/
  load-summary.json   — parsed k6 output metrics
  raw/
    load-output.txt   — raw k6 stdout/stderr
```

## Step 5: Stress Test

Execute a separate stress test scenario using k6.

### Stress Test Configuration

Progressively increase load until ONE of:
  - Configured threshold reached.
  - Configured maximum load reached.
  - Error rate becomes unacceptable.
  - Latency exceeds configured threshold.
  - Environment becomes unavailable.

**Safe default conceptual progression:**

```
start: 1 VU
step: +1 VU every 15s
max: 20 VUs (or configured maximum)
duration per step: 15s
```

### Stress Test Execution

```
k6 run shared-state/<story>/performance/stress-test.js
```

### Stress Test Output

```
shared-state/<story>/performance/results/
  stress-summary.json  — parsed k6 output metrics
  raw/
    stress-output.txt  — raw k6 stdout/stderr
```

### Stress Test Rules

- Do NOT run uncontrolled traffic.
- Do NOT stress test against production.
- Do NOT stress test unless the project adapter explicitly permits
  performance execution against the target environment.
- If the environment becomes unavailable during stress test, stop and
  record the failure point.

## Step 6: Threshold Evaluation

### Supported Thresholds

- p50 (median latency)
- p90 latency
- p95 latency
- p99 latency
- Error rate
- Request rate
- Throughput
- Timeout rate

### Threshold Configuration

Thresholds come from:
  - The project adapter (if it defines performance thresholds).
  - A performance config file.
  - The story (if it specifies performance requirements).

### When No Thresholds Are Provided

If the project or story does not provide thresholds:
  - Report all measurements.
  - Do NOT claim pass/fail against invented SLA values.
  - The report must state:

    "Measured only — no project-specific performance threshold was provided."

### Threshold Evaluation Output

For each threshold:
  - Measured value.
  - Threshold value (if configured).
  - Pass/fail/unaffected status.
  - Note if threshold was not configured.

## Step 7: Result Collection

### Output Structure

```
shared-state/<story>/performance/
  request-inventory.json
  load-test.js
  stress-test.js
  results/
    load-summary.json
    stress-summary.json
    raw/
      load-output.txt
      stress-output.txt
  reports/
    performance-report.md
  graphs/
    latency.png
    throughput.png
    error-rate.png
```

Use the smallest reasonable set of artifacts. Do NOT create unnecessary files.

### Result Fields

For each result summary:
  - Test type (load or stress).
  - k6 version (if available).
  - Execution timestamp.
  - Target URL (sanitized).
  - VUs used.
  - Duration.
  - Total request count.
  - Success count.
  - Failure count.
  - Error rate.
  - Throughput (requests/second).
  - p50, p90, p95, p99 latency.
  - Min/max latency where available.
  - Status: executed | blocked | failed.

## Step 8: Performance Report

### Output

`shared-state/<story>/performance/reports/performance-report.md`

### Report Structure

```
# Performance Report — <story-id>

## Executive Summary
  - Environment: <environment used or blocker>
  - Test type: Load test / Stress test / Both / Neither
  - Duration: <total test duration>
  - Virtual users / load: <VUs or load profile>
  - Requests tested: <count of selected requests>
  - Overall execution status: executed | blocked | partial

## Request Coverage
  - Total captured requests: <N>
  - Selected for performance: <N>
  - Excluded: <N>
  - Exclusion reasons: <list of reasons>

## Load Test Results
  - Request count: <N>
  - Success count: <N>
  - Failure count: <N>
  - Error rate: <X%>
  - Throughput: <X req/s>
  - p50: <X ms>
  - p90: <X ms>
  - p95: <X ms>
  - p99: <X ms>
  - Min latency: <X ms> (if available)
  - Max latency: <X ms> (if available)

## Stress Test Results
  - Load progression: <description>
  - Latency progression: <described or table>
  - Error-rate progression: <described or table>
  - Observed degradation point: <if objectively identifiable from data>

## Findings
  - Observed facts: <facts from results>
  - Configured thresholds: <thresholds used or "none provided">
  - Missing thresholds: <what was not configured>
  - Blockers: <any blockers encountered>
  - Risks: <risks from results>

## Recommendations
  <Based ONLY on observed evidence. Do NOT invent root causes.>
```

### Rules for the Report

- Do NOT call something a "system breaking point" unless evidence
  objectively supports it.
- Do NOT invent root causes.
- Do NOT claim results represent production capacity.
- Separate observed facts from interpretation.
- If performance execution was blocked, the report must clearly state
  the blocker and what would be required to unblock it.

## Step 9: Graphs

### Output

```
shared-state/<story>/performance/graphs/
  latency.png       — latency over time
  throughput.png    — throughput over time
  error-rate.png    — error rate over time
```

### Graph Rules

- Generate graphs ONLY from actual performance results.
- If raw data does not support a graph, do NOT fabricate one.
- Prefer a simple plotting solution already available
  (e.g., matplotlib if Python is available, or k6's built-in output
  formats that can be post-processed).
- Do NOT add a large analytics framework.
- The performance report must reference generated graphs by filename.

### When Graphs Cannot Be Generated

If no performance execution occurred, or if raw data is insufficient:
  - Do NOT generate placeholder graphs.
  - Note in the report that graphs were not generated because no
    performance execution data is available.

## Safety Rules

Absolutely do NOT:
  - Run performance tests against production without explicit authorization.
  - Execute real financial transactions during performance tests.
  - Execute destructive operations during performance tests.
  - Send uncontrolled traffic.
  - Expose credentials in k6 scripts or reports.
  - Persist tokens in k6 scripts or reports.
  - Invent API endpoints.
  - Invent request bodies.
  - Fabricate performance results.

If the safety configuration does not explicitly permit performance
execution, BLOCK.

## Blocking Conditions

The performance stage is BLOCKED when:
  - k6 is not installed and installation is not permitted.
  - No request inventory exists.
  - No approved target environment is available.
  - Safety configuration blocks performance execution.
  - Selected requests have unavailable bodies or unknown methods.
  - The project adapter does not enable performance testing.

A blocked performance stage records:
  - The specific blocker.
  - What would be required to unblock it.
  - Which artifacts were generated before the block (if any).

## Project-Agnostic Behavior

This skill works the same way for every project. Only the project adapter
and shared state differ:
  - Different base URLs → different k6 script config.
  - Different endpoints → different request inventory.
  - Different thresholds → different pass/fail evaluation.
  - Different VUs/duration → different test intensity.

The skill itself contains NO company-specific information.

## Integration with QA Agent Harness

The performance testing skill is invoked by the execution stage or a
dedicated performance sub-stage. It reads from:
  - `shared-state/<story>/execution/network/` (captured requests)
  - `shared-state/<story>/test-design/output.md` (story scope)
  - `projects/<project>/project.yaml` (safety, environment, thresholds)

It writes to:
  - `shared-state/<story>/performance/`

The performance stage status is tracked in
`shared-state/<story>/stage-status.json` under a performance sub-stage
or as part of the execution stage status, depending on the workflow
integration chosen.

## Failure Analysis Trigger

Performance testing failures are eligible for cross-stage Failure Analysis.
Examples:
  - k6 script generation fails.
  - k6 execution fails.
  - Latency exceeds configured threshold.
  - Error rate increases under load.
  - Stress test causes environment unavailability.
  - Request inventory is incomplete or missing required requests.

See `orchestrator/workflow.md` Section B (Failure Analysis) for the
full failure analysis structure.

## Version History

- 0.1.0 — Initial foundation (specialist skill).
- 0.2.0 — Extended to full reusable performance testing skill with
          request inventory, classification, k6 generation, load/stress
          test, thresholds, reports, and graphs.
