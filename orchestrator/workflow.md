# QA Agent Harness — Execution Workflow

This document defines the execution workflow for the reusable, company-independent QA Agent Harness. It is the state machine that the QA Orchestrator drives. It is independent of any specific project; only the project adapter at `projects/<project-name>/` makes a run concrete.

## Overview

The workflow moves a QA story through fourteen stages, from intake to final report. Each stage produces shared-state artifacts and hands off to the next stage. The workflow can resume from the last completed stage after an interruption, a failure, or a human decision.

Conceptual flow:

```
STORY
  → DISCOVERY
  → ANALYSIS
  → GRILL
  → RISK
  → ARCHITECTURE
  → SPECIFICATION
  → TEST DESIGN
  → DELEGATION
  → EXECUTION
  → FAILURE ANALYSIS
  → REVIEW
  → EVIDENCE
  → FINAL REPORT
```

## Ground Rules

These rules apply at every stage, for every agent, always:

- Never invent requirements.
- Never invent credentials.
- Never invent URLs.
- Never invent selectors.
- Never invent API contracts.
- Never invent database schemas.
- Never invent business rules.
- Never execute destructive production operations unless the project safety configuration explicitly authorizes the specific action.
- Never perform real financial transactions without explicit authorization.
- Never use company-specific information that is not in the project adapter or in shared state from a prior stage.
- Read the project adapter before acting.
- Read the shared state from prior stages before acting.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Prefer existing project conventions, automation utilities, and fixtures.
- Do not over-engineer.
- Do not modify application code.
- Do not modify the project adapter.

## State Machine

The workflow is a linear sequence of stages with explicit completion markers in shared state. Each stage records its completion status and the artifacts it produced. The orchestrator inspects shared state at startup and resumes at the first incomplete stage.

### Stage Status

Each stage in `shared-state/workflow/stage-status.json` has one of these statuses:

- `pending` — not yet started.
- `in_progress` — started but not completed.
- `completed` — finished, artifacts present, handoff validated.
- `blocked` — cannot proceed; reason recorded.
- `failed` — the stage itself failed; reason recorded.
- `skipped` — deliberately skipped with a recorded justification.

### Resume Logic

On startup, the orchestrator:

1. Reads `shared-state/workflow/stage-status.json`.
2. Finds the first stage whose status is not `completed` and not `skipped`.
3. If that stage is `in_progress`, the orchestrator asks whether to resume or restart it.
4. If that stage is `blocked`, `failed`, or `pending`, the orchestrator proceeds to the handling rules below.
5. If all stages are `completed` or `skipped`, the orchestrator moves to final reporting.

A stage may be restarted from the beginning if its artifacts are incomplete, invalid, or if a human or prior stage flags them as unreliable. Restarting a stage invalidates the downstream stages, which are reset to `pending`.

### Shared State Root

All workflow artifacts live under `shared-state/<story-id>/`, where `<story-id>` is a stable identifier for the story under test. The orchestrator creates this directory at story intake and uses it throughout the run.

Required shared-state documents:

- `shared-state/<story-id>/story-intake.md` — the story as received.
- `shared-state/<story-id>/stage-status.json` — stage status for the whole run.
- `shared-state/<story-id>/<stage-name>/output.md` — the output of each completed stage.

## Safety Gates

Two global safety gates apply before any stage that may act on an environment:

### Gate A — Production Execution

Before acting on a production environment, the orchestrator checks `projects/<project-name>/project.yaml`, field `safety.production_execution`. If true, the orchestrator:

- Refuses destructive actions.
- Refuses real payment transactions.
- Requires explicit per-action authorization for any production operation beyond read-only validation.

If `safety.production_execution` is false, production execution is allowed only within the constraints of the other safety fields.

### Gate B — Real Payments

Before any step that could create a real financial transaction, the orchestrator checks `safety.real_payments`. If true, the step is blocked unless the project adapter explicitly authorizes the specific transaction. The orchestrator never invents authorization.

### Gate C — Destructive Database Operations

Before any step that could mutate a production database, the orchestrator checks `safety.destructive_database_operations`. If true, the step is blocked unless the project adapter explicitly authorizes the specific operation.

## Stage Definitions

### Stage 1 — Story Intake

**Responsible:** QA Orchestrator

**Required inputs:**
- The QA story, user story, requirement, or change description.
- Any acceptance criteria attached to the story.
- The project identifier, if already known.

**Shared-state inputs:**
- None required. This is the entry point.

**Expected output:**
- `shared-state/<story-id>/story-intake.md` containing the story text, acceptance criteria, source, and any initial context.

**Shared-state output:**
- `shared-state/<story-id>/story-intake.md`
- `shared-state/<story-id>/stage-status.json` with Stage 1 set to `completed`.

**Preconditions:**
- A story has been provided.
- A `<story-id>` has been assigned.

**Validation checks:**
- The story text is present and non-empty.
- The acceptance criteria are captured, even if empty.
- The `<story-id>` directory exists.

**Failure behavior:**
- If no story is provided, the workflow stops at intake and reports a missing story. No downstream stage runs.

**Human approval required:** No, unless the story itself is unclear enough that the orchestrator cannot proceed to discovery. In that case, the orchestrator records the ambiguity and asks for clarification before advancing.

**Handoff to Stage 2:**
The orchestrator passes the story, acceptance criteria, and `<story-id>` to the Discovery stage. Discovery does not need a completed story; it needs at least enough to identify the project and begin inspection.

---

### Stage 2 — Project Discovery

**Responsible:** Discovery Agent (`agents/discovery/AGENT.md`)

**Required inputs:**
- The story intake document.
- The project identifier, if known, or enough context to locate the project adapter.

**Shared-state inputs:**
- `shared-state/<story-id>/story-intake.md`

**Expected output:**
- A project discovery report covering technology stack, application architecture, frontend and backend frameworks, programming languages, package manager, test frameworks, existing automation, API architecture, database technology, authentication, CI/CD, environments, test data, fixtures, utilities, and coding conventions, with unknowns explicitly marked.

**Shared-state output:**
- `shared-state/<story-id>/discovery/output.md`
- Any project-specific artifacts the discovery agent produces under `shared-state/<story-id>/discovery/`.

**Preconditions:**
- Stage 1 is `completed`.
- The project adapter exists at `projects/<project-name>/project.yaml`, or the project cannot be identified.

**Validation checks:**
- The project adapter was read.
- The discovery report covers all sections named in the Discovery Agent spec.
- Unknowns are explicitly marked, not silently skipped.
- The report does not contain invented project-specific information.

**Failure behavior:**
- If the project cannot be identified, the stage is marked `blocked` with the reason, and the workflow stops. The orchestrator reports that no project adapter was found and asks for one.
- If the project adapter exists but is empty or template-only, the stage is marked `blocked` with the reason that the project adapter is not configured. The workflow stops until a concrete project adapter is provided.

**Human approval required:** No, but a blocked project discovery requires human action to provide a project adapter before the workflow can continue.

**Handoff to Stage 3:**
The orchestrator passes the discovery report and the project identifier to the Analysis stage. The discovery report is the primary shared-state input for all downstream stages.

---

### Stage 3 — Requirement Analysis

**Responsible:** QA Analyst Agent (`agents/analyst/AGENT.md`)

**Required inputs:**
- The story intake document.
- The project discovery report.
- The project adapter.

**Shared-state inputs:**
- `shared-state/<story-id>/story-intake.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Requirement summary.
- Functional scenarios.
- Negative scenarios.
- Edge cases.
- Integration risks.
- Data risks.
- Regression risks.
- Missing information.
- Questions.
- QA recommendations.

**Shared-state output:**
- `shared-state/<story-id>/analysis/output.md`

**Preconditions:**
- Stage 2 is `completed`.
- The project adapter is configured and identifies an application type.

**Validation checks:**
- The analysis references the requirement and acceptance criteria from the intake.
- Scenarios are grounded in the requirement and the project adapter, not invented.
- Missing information and questions are explicitly recorded.
- No invented business rules appear.

**Failure behavior:**
- If the requirement cannot be understood from the intake, the stage is marked `blocked` with the reason, and the workflow stops. The orchestrator records the blocking ambiguity and asks for clarification.
- If the requirement is clear enough to proceed but incomplete, the stage completes with missing information flagged, and the workflow continues to Grill, which is designed to handle incomplete requirements.

**Human approval required:** No. Questions are generated for humans to answer, but the workflow does not block on unanswered questions at this stage. The Grill stage handles the same gaps more aggressively.

**Handoff to Stage 4:**
The orchestrator passes the analysis output and the shared state to the Grill stage. The Grill stage uses the same inputs plus the discovery report.

---

### Stage 4 — QA Grill

**Responsible:** QA Grill Skill (`skills/qa-grill/SKILL.md`)

**Required inputs:**
- The story intake document.
- The acceptance criteria.
- The analysis output, if available.
- The project adapter.
- The project discovery report.

**Shared-state inputs:**
- `shared-state/<story-id>/story-intake.md`
- `shared-state/<story-id>/analysis/output.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Ambiguities.
- Missing requirements.
- Negative scenarios.
- Edge cases.
- Integration risks.
- Regression risks.
- Clarification questions.
- Confirmed vs unconfirmed separation.
- Assumptions.
- Unknowns.
- Blockers for specification.

**Shared-state output:**
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/grill/questions.md` if there are clarification questions.

**Preconditions:**
- Stage 3 is `completed`.

**Validation checks:**
- Every ambiguity is tied to a specific requirement or acceptance criterion.
- Missing requirements are stated as missing, not filled in.
- Clarification questions are answerable by a human stakeholder.
- No invented answers appear.
- Confirmed and unconfirmed items are explicitly separated.

**Failure behavior:**
- If the requirement is so ambiguous that no testable scope can be identified, the stage is marked `blocked` with the reason, and the workflow stops. The orchestrator reports that the requirement must be clarified before specification can proceed.
- If the grill completes with open questions, the stage is marked `completed` and the workflow continues. Open questions are carried forward as shared-state inputs to later stages and to the final report.

**Human approval required:** No for completion. Yes for answering clarification questions. The workflow does not wait for answers before advancing; it advances with the questions as shared-state inputs and flags them in later stages.

**Handoff to Stage 5:**
The orchestrator passes the grill output to the Risk Analysis stage. The risk stage uses the grill output as a primary input for risk identification.

---

### Stage 5 — Risk Analysis

**Responsible:** Risk Analysis Agent (`agents/risk/AGENT.md`), invoked by the QA Orchestrator

**Required inputs:**
- The grill output.
- The analysis output.
- The project adapter.
- The project discovery report.

**Shared-state inputs:**
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/analysis/output.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Business risks.
- Technical risks.
- Integration risks.
- Data risks.
- Regression risks.
- Risk severity or priority, where determinable.
- Risks that must be addressed before testing.

**Shared-state output:**
- `shared-state/<story-id>/risk/output.md`

**Preconditions:**
- Stage 4 is `completed`.

**Validation checks:**
- Risks are tied to specific findings from the grill or analysis.
- No invented risks appear.
- Blocked risks that must be resolved before testing are clearly identified.
- Risks are distinguishable from the grill's raw findings — the risk stage should prioritize and contextualize, not merely repeat.

**Failure behavior:**
- If risk analysis cannot be performed because prior inputs are missing, the stage is marked `blocked` with the reason. The orchestrator reports the missing input and stops.
- If risks are identified but none block testing, the stage completes and the workflow continues.

**Human approval required:** No. High-severity risks are flagged in the shared state and in the final report, but the workflow does not wait for human approval to continue unless a risk blocks testing and no workaround exists.

**Handoff to Stage 6:**
The orchestrator passes the risk output to the Test Architecture stage. The architecture stage uses risks to inform test-level and strategy decisions.

---

### Stage 6 — Test Architecture

**Responsible:** Test Architect Agent (`agents/architect/AGENT.md`)

**Required inputs:**
- The grill output.
- The analysis output.
- The risk output.
- The project adapter.
- The project discovery report.

**Shared-state inputs:**
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/analysis/output.md`
- `shared-state/<story-id>/risk/output.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Test strategy.
- Test pyramid.
- Automation strategy.
- Test data strategy.
- Environment strategy.
- Mocking strategy.
- CI strategy.
- Reporting strategy.
- Risks.
- Implementation plan.

**Shared-state output:**
- `shared-state/<story-id>/architecture/output.md`

**Preconditions:**
- Stage 5 is `completed`.

**Validation checks:**
- The architecture is consistent with the project adapter's declared application type, API types, database usage, and environments.
- The architecture prefers the lowest appropriate test layer.
- The architecture does not assume a specific application beyond what the project adapter declares.
- The implementation plan is consistent with the specialist agents that exist.

**Failure behavior:**
- If the project adapter declares no testable application type, the stage is marked `blocked` with the reason. The orchestrator reports that there is nothing to architect tests against and stops.
- If the architecture cannot decide on a test strategy because required information is missing, the stage is marked `blocked` with the reason, and the workflow stops.

**Human approval required:** No, but the architecture output should be reviewable by a human before delegation. The workflow does not block on that review, but the Review stage later checks whether the architecture was sound.

**Handoff to Stage 7:**
The orchestrator passes the architecture output to the QA Specification stage. The specification stage uses the architecture to inform coverage and test data decisions.

---

### Stage 7 — QA Specification

**Responsible:** QA Specification Skill (`skills/qa-spec/SKILL.md`)

**Required inputs:**
- The story intake document.
- The acceptance criteria.
- The grill output.
- The analysis output.
- The risk output.
- The architecture output.
- The project adapter.
- Clarification answers, if any exist.

**Shared-state inputs:**
- `shared-state/<story-id>/story-intake.md`
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/analysis/output.md`
- `shared-state/<story-id>/risk/output.md`
- `shared-state/<story-id>/architecture/output.md`
- `projects/<project-name>/project.yaml`
- `shared-state/<story-id>/grill/questions.md` and any answers, if present.

**Expected output:**
- Requirement under specification.
- Functional coverage.
- Negative coverage.
- Boundary coverage.
- Integration coverage.
- Validation expectations.
- Required test data.
- Required environment dependencies.
- Confirmed requirements.
- Assumptions.
- Unknowns.
- Items blocked pending clarification.

**Shared-state output:**
- `shared-state/<story-id>/specification/output.md`

**Preconditions:**
- Stage 6 is `completed`.

**Validation checks:**
- Every coverage area is tied to a requirement, acceptance criterion, project adapter value, or shared-state artifact.
- No invented expected outcomes appear as confirmed.
- The confirmed/assumption/unknown separation is explicit.
- Required test data and environment dependencies are stated concretely enough to act on.
- The specification does not silently assume answers to open clarification questions.

**Failure behavior:**
- If the specification cannot be produced because the requirement or acceptance criteria are missing, the stage is marked `blocked` with the reason. The orchestrator reports that specification requires a requirement and stops.
- If the specification can be produced but has open clarifications or unknowns, the stage completes with those flagged and the workflow continues.

**Human approval required:** No for completion. Yes for answering clarification questions that the specification depends on. If the specification depends on an unanswered question to define coverage, the orchestrator may mark the affected coverage area as blocked rather than stopping the whole workflow.

**Handoff to Stage 8:**
The orchestrator passes the specification output to the Test Design stage. The test design stage uses the specification as its primary input.

---

### Stage 8 — Test Design

**Responsible:** Test Design Skill (`skills/test-design/SKILL.md`)

**Required inputs:**
- The specification output.
- The grill output and any clarification answers.
- The architecture output.
- The project adapter.
- The project discovery report.

**Shared-state inputs:**
- `shared-state/<story-id>/specification/output.md`
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/architecture/output.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Requirement under design.
- Scenario list with per-scenario: name, description, linked specification item, test level, classification, automation candidate, manual validation required, required test data, required environment dependencies, notes.
- Test-level rationale summary.
- Automation candidates.
- Manual-validation scenarios.
- Scenarios blocked on missing data or environment.
- Out-of-scope scenarios.
- Assumptions.
- Unknowns.

**Shared-state output:**
- `shared-state/<story-id>/test-design/output.md`

**Preconditions:**
- Stage 7 is `completed`.

**Validation checks:**
- Every scenario traces to a specification item.
- Every scenario has an assigned test level with a rationale.
- Lower test levels were preferred where valid.
- Automation candidacy is marked per scenario.
- Manual-validation scenarios are called out.
- Scenarios blocked on missing data or environment are identified.
- No invented selectors, endpoints, schemas, credentials, or data values appear.

**Failure behavior:**
- If the specification is missing or incomplete such that scenarios cannot be designed, the stage is marked `blocked` with the reason. The orchestrator reports that test design requires a specification and stops.
- If scenarios can be designed but some are blocked on data or environment, the stage completes with those scenarios flagged as blocked. The workflow continues.

**Human approval required:** No. The test design is a plan, not executed tests. Human review happens later in the Review stage.

**Handoff to Stage 9:**
The orchestrator passes the test-design output to the Delegation stage. The delegation stage uses the scenario list to decide which specialist agents to engage.

---

### Stage 9 — Specialist Delegation

**Responsible:** QA Orchestrator

**Required inputs:**
- The test-design output.
- The project adapter.
- The project discovery report.
- The architecture output.
- The shared state from all prior stages.

**Shared-state inputs:**
- `shared-state/<story-id>/test-design/output.md`
- `shared-state/<story-id>/architecture/output.md`
- `shared-state/<story-id>/discovery/output.md`
- `projects/<project-name>/project.yaml`
- All prior stage outputs.

**Expected output:**
- A delegation plan mapping scenarios to specialist agents.
- For each delegation: the agent, the scenarios assigned, the environment, the safety gate checks performed, and the expected shared-state output location.

**Shared-state output:**
- `shared-state/<story-id>/delegation/output.md`
- Per-agent delegation records under `shared-state/<story-id>/delegation/`.

**Preconditions:**
- Stage 8 is `completed`.
- The relevant specialist agents exist for the scenarios to be delegated.

**Validation checks:**
- Every scenario that requires a specialist is assigned to an agent that exists.
- No scenario is assigned to an agent that cannot handle its test level or type.
- Safety gates were checked before delegating any environment-affecting work.
- No company-specific information was passed to a specialist agent except through the project adapter or shared state.

**Failure behavior:**
- If a scenario requires a specialist agent that does not exist, the orchestrator marks that scenario as `blocked` with the reason and continues delegating the remaining scenarios. The blocked scenario is flagged in the final report.
- If all scenarios are blocked because no specialist agents exist, the stage is marked `blocked` and the workflow stops at delegation.

**Human approval required:** No for normal delegation. Yes if a delegation would act on a production environment and the safety gate requires explicit per-action authorization. In that case, the orchestrator blocks the delegation until authorization is recorded.

**Handoff to Stage 10:**
The orchestrator passes each delegation record to the assigned specialist agent. Specialists execute in parallel where they do not depend on each other. The orchestrator tracks each specialist's status in `stage-status.json` under the delegation sub-stages.

---

### Stage 10 — Test Execution

**Responsible:** Execution Agent (`agents/execution/AGENT.md`) and the delegated specialist agents

**Required inputs:**
- The delegation records.
- The test-design output (scenarios).
- The project adapter.
- The shared state from all prior stages.

**Shared-state inputs:**
- `shared-state/<story-id>/delegation/output.md`
- `shared-state/<story-id>/test-design/output.md`
- `projects/<project-name>/project.yaml`
- All prior stage outputs.

**Expected output:**
- Executable Playwright spec file (if web tests are in scope).
- Network capture data (if web execution is possible).
- Request inventory (from captured network data or approved API inventory).
- Performance test scripts (k6 load-test.js and stress-test.js, if performance
  is enabled and requests are available).
- Which tests ran.
- Which environment was used.
- Pass/fail summary.
- Evidence index.
- Blocked or skipped tests with reasons.
- Execution status: `generated | ready | running | passed | failed | blocked`.
- Performance status: `not_attempted | scripts_generated | ready | running |
  passed | failed | blocked`.

**Shared-state output:**
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- `shared-state/<story-id>/execution/spec/<story-id>.spec.js` (if generated)
- `shared-state/<story-id>/execution/network/network-requests.json` (if captured)
- `shared-state/<story-id>/execution/network/network-summary.md` (if useful)
- `shared-state/<story-id>/performance/request-inventory.json` (if generated)
- `shared-state/<story-id>/performance/load-test.js` (if generated)
- `shared-state/<story-id>/performance/stress-test.js` (if generated)
- `shared-state/<story-id>/performance/results/load-summary.json` (if executed)
- `shared-state/<story-id>/performance/results/stress-summary.json` (if executed)
- `shared-state/<story-id>/performance/reports/performance-report.md` (if generated)
- `shared-state/<story-id>/performance/graphs/*.png` (if generated)

**Preconditions:**
- Stage 9 is `completed`.
- Implemented tests exist for the delegations that are scheduled to run,
  OR the execution stage can generate executable specs from the test-design
  scenarios.
- The target environment is declared in the project adapter and available.
- Safety gates permit the intended execution.

**Execution sub-flow:**

The execution stage consists of the following sub-steps, executed in order:

#### 10a. Spec Generation

Before executing any tests, the execution agent attempts to generate an
executable Playwright test spec from the test-design scenarios.

**Process:**
1. Read `shared-state/<story-id>/test-design/output.md` and extract scenarios.
2. Read the project adapter for the application base URL (if declared).
3. Generate a real Playwright spec file using the execution skill helper
   `generate_playwright_spec`.
4. Save the spec to `shared-state/<story-id>/execution/spec/<story-id>.spec.js`.

**Spec generation status values:**
- `generated` — spec file was created successfully.
- `blocked` — spec could not be generated (e.g., no scenarios, no base URL).

**Generated spec requirements:**
- Must be a real, syntactically valid JavaScript file.
- Must include network capture instrumentation (Playwright request/response
  events or HAR capture).
- Must clearly mark placeholder selectors, URLs, and test data as placeholders.
- Must NOT contain invented credentials, API contracts, or business rules.
- If critical information is missing (base URL, selectors), the spec must
  clearly identify the missing dependency and set execution status to `blocked`.

#### 10b. Playwright Execution

Execute the generated Playwright test when ALL of these are true:
- The project is configured for Playwright (automation.framework = playwright).
- An approved environment exists (environments.dev or staging = true).
- Required credentials/configuration exist (or are not required for the test).
- Required information is available (base URL, selectors — or placeholders
  are acceptable for a first execution attempt).

**Rules:**
- Use real Playwright execution via the existing specialist mechanism.
- Do NOT simulate execution.
- Do NOT generate fake pass/fail results.
- Do NOT mark execution completed just because the spec was generated.
- If the environment is unavailable, execution status = `blocked` and a
  truthful run report explains the blocker.

**Execution status values:**
`generated | ready | running | passed | failed | blocked`

#### 10c. Network Request Capture

During Web Playwright execution, capture network activity using Playwright's
request/response events or HAR capture.

**Collect at minimum:**
- Request URL (sanitized).
- HTTP method.
- Resource type.
- Response status.
- Response timing.
- Request timing.
- Response size (when available).

**Sanitization is MANDATORY before persisting:**

Captured network data may contain: Authorization headers, cookies, tokens,
session IDs, API keys, personal data, payment information.

Before writing any captured request to shared state, sanitize:
- `Authorization` → `<REDACTED>`
- `Cookie` → `<REDACTED>`
- `Set-Cookie` → `<REDACTED>`
- API keys, bearer tokens, session tokens → `<REDACTED>`
- Passwords → `<REDACTED>`
- Payment secrets → `<REDACTED>`
- Sensitive query parameters (`token`, `access_token`, `session`, `sig`,
  `apikey`, `api_key`, `key`, `secret`, `password`) → `<REDACTED>`

The original secret must NEVER be copied into: HAR, JSON, Markdown, k6 scripts,
reports, or logs.

**Network capture output:**
- `shared-state/<story-id>/execution/network/network-requests.json`
- `shared-state/<story-id>/execution/network/network-summary.md` (if useful)

#### 10d. Request Classification

Do NOT automatically convert every browser request into a performance test.

Classify captured requests into categories:
- `business_api` — application/business API endpoints.
- `authentication` — login, token, session endpoints.
- `static_asset` — CSS, JS, images, fonts (exclude from performance).
- `analytics` — Google Analytics, telemetry, tracking (exclude).
- `third_party` — external services not owned by the project (exclude).
- `browser_internal` — browser-internal requests (exclude).
- `unknown` — cannot classify (review required).

Performance testing focuses on application/business APIs, relevant
authentication APIs when explicitly allowed, and critical requests related
to the story. Do NOT load-test static assets, analytics, third-party
services, or browser internals.

#### 10e. Request Inventory Generation

Generate a request inventory from classified and sanitized network data:

`shared-state/<story-id>/performance/request-inventory.json`

Fields per request:
- `method`
- `sanitized_url`
- `category`
- `selected_for_performance`
- `reason`
- `source_artifact`

#### 10f. Performance Test Script Generation

Generate k6 scripts from the approved request inventory:

- `shared-state/<story-id>/performance/load-test.js`
- `shared-state/<story-id>/performance/stress-test.js`

**Rules:**
- Generate from captured/approved requests only.
- Do NOT hardcode company-specific endpoints.
- Do NOT invent request payloads.
- If a request body is required but cannot be safely captured or
  reconstructed, mark that request as blocked.
- Do NOT guess the payload.

**Performance script generation status:**
- `scripts_generated` — k6 scripts were created.
- `blocked` — scripts could not be generated (no requests, no k6, etc.).

#### 10g. k6 Execution (Performance Testing)

**k6 availability check:**
1. Check whether k6 is installed (`k6 version`).
2. If not installed, report as a **dependency blocker**.
3. Do NOT install system-wide dependencies without explicit project permission.
4. If k6 is unavailable, the performance stage is **BLOCKED**.

**If k6 is available and execution is permitted:**
1. Run load test: `k6 run shared-state/<story-id>/performance/load-test.js`.
2. Run stress test: `k6 run shared-state/<story-id>/performance/stress-test.js`.
3. Parse k6 output for metrics (p50, p90, p95, p99, throughput, error rate).
4. Save results to `shared-state/<story-id>/performance/results/`.
5. Generate performance report: `shared-state/<story-id>/performance/reports/performance-report.md`.
6. Generate graphs if data supports them.

**If k6 is unavailable:**
- Performance status = `blocked`.
- Reason: `"k6 not installed — install k6 to enable performance testing.
  Installation requires explicit project permission."`
- Do NOT fabricate performance results.
- k6 scripts are still generated (valid artifacts even if not executed).

**Performance thresholds:**
Support configurable thresholds: p50, p90, p95, p99, error rate, request rate,
throughput, timeout rate. If the project/story does not provide thresholds,
report measurements without claiming pass/fail against invented SLA. The report
must state: "Measured only — no project-specific performance threshold was provided."

**Safety:**
- Do NOT run performance tests against production.
- Do NOT execute real financial transactions.
- Do NOT send uncontrolled traffic.
- Do NOT expose credentials in k6 scripts or reports.

**Performance execution status values:**
`not_attempted | scripts_generated | ready | running | passed | failed | blocked`

#### 10h. Execution Report

Build the execution run report covering:
- Spec generation status and path.
- Playwright execution status, tests passed/failed/blocked.
- Network capture status and request count.
- Request inventory status and path.
- Performance script generation status.
- k6 execution status (if attempted).
- Performance metrics (if k6 executed).
- Blockers (with specific reasons).
- Evidence index.

**Example execution summary in run-report.md:**

```
Execution:
  - Spec generated: YES — shared-state/<story>/execution/spec/<story>.spec.js
  - Playwright executed: YES/NO/BLOCKED
  - Tests passed: X
  - Tests failed: Y
  - Network captured: YES/NO
  - Requests captured: X

Performance:
  - Request inventory generated: YES/NO
  - Load test script generated: YES/NO
  - Load test executed: YES/NO/BLOCKED
  - Stress test script generated: YES/NO
  - Stress test executed: YES/NO/BLOCKED
  - p95: X ms (if executed)
  - p99: X ms (if executed)
  - Error rate: X% (if executed)
  - Graphs generated: YES/NO
```

If blocked:

```
Execution: BLOCKED  Reason: no approved environment / no base URL / k6 not installed
Performance: BLOCKED  Reason: k6 not installed / no executable performance target
```

NEVER replace BLOCKED with PASSED or COMPLETED.

**Failure behavior:**
- If the target environment is unavailable, the execution stage marks the
  affected tests as `blocked` with the reason `environment unavailable`.
- If no implemented tests exist for a delegation, the execution stage marks
  that delegation as `blocked` with the reason `no implemented tests`.
- If execution fails due to a runtime error not caused by the application,
  the execution stage records the failure and continues with remaining tests
  where possible.
- If Playwright spec generation fails, the execution stage records the failure
  and the spec generation status as `blocked`.
- If k6 is unavailable, the performance sub-stage is marked `blocked` with the
  specific reason. No performance results are fabricated.
- If execution is blocked by a safety gate, the stage marks the affected tests
  as `blocked` with the safety constraint.

**Human approval required:** Yes for any execution that the safety gates require
explicit authorization for. No for read-only execution in allowed environments.

**Handoff to Stage 11:**
The orchestrator passes the execution run report, evidence index, network capture
artifacts, request inventory, and performance artifacts (if any) to the Failure
Analysis stage. If there are no failures, the orchestrator may skip Stage 11 and
proceed directly to Stage 12, recording that failure analysis was skipped because
there were no failures.

---

### Stage 11 — Failure Analysis (Cross-Stage)

**Responsible:** Failure Analysis Agent (`agents/failure-analysis/AGENT.md`)

**Required inputs:**
- The execution run report.
- The evidence index.
- The network capture artifacts (if any).
- The request inventory (if any).
- The performance artifacts (if any).
- The test-design output.
- The specification output.
- The project adapter.

**Shared-state inputs:**
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- `shared-state/<story-id>/test-design/output.md`
- `shared-state/<story-id>/specification/output.md`
- `projects/<project-name>/project.yaml`
- All execution/performance artifacts as applicable.

**Expected output:**
- Number of failures analyzed (including non-test failures).
- Classification counts by category: product defect, test defect, environment
  issue, data issue, infrastructure issue, parsing error, data integrity,
  requirement gap, automation failure, network failure, performance failure,
  artifact failure, configuration failure, dependency failure, unknown.
- Per-failure detail with evidence, reasoning, root cause assessment, and
  alternative explanations.
- Failures that could not be classified and what is missing.
- Impact chain for cross-stage failures.

**Shared-state output:**
- `shared-state/<story-id>/failure-analysis/failure-analysis.md`
- `shared-state/<story-id>/failure-analysis/issues.json`

**Preconditions:**
- Stage 10 is `completed`.
- At least one failure, blocker, or unexpected result exists to analyze, or
  the stage is skipped with a recorded reason.

**Failure Analysis is MANDATORY and is NOT limited to failed automated tests.**

It is a cross-stage failure investigation capability. Any meaningful failure,
unexpected result, blocker, execution error, data-integrity issue, validation
mismatch, environment problem, or quality issue detected anywhere in the
workflow is eligible for Failure Analysis.

**Trigger sources (any stage):**

Failures originating from any stage are eligible:
1. Story Intake — story cannot be parsed, missing required sections.
2. Discovery — cannot inspect target, target repository missing.
3. Requirement Analysis — requirement conflict, missing critical information.
4. QA Grill — ambiguity that blocks specification.
5. Risk Analysis — risk that blocks testing.
6. Test Architecture — architecture cannot be produced.
7. QA Specification — specification incomplete or blocked.
8. Test Design — scenarios cannot be designed.
9. Specialist Delegation — no specialist available for a scenario.
10. Test Execution — Playwright test fails, API returns unexpected status,
    spec generation fails, network capture fails, request inventory generation
    fails, k6 execution fails.
11. Performance Testing — k6 script generation fails, k6 execution fails,
    latency exceeds configured threshold, error rate increases under load,
    stress test causes environment unavailability.
12. Independent QA Review — artifact mismatch, missing coverage, unsupported
    assumption detected.
13. Evidence Collection — evidence incomplete or corrupted.
14. Final QA Report — downstream artifact contradicts upstream artifact.

**Examples of eligible failures:**
- Story cannot be parsed.
- Required section is missing from a stage output.
- Discovery cannot inspect target repository.
- Requirement conflict detected between stages.
- Hardcoded information contaminates another story's artifacts.
- Required environment unavailable.
- Test generation fails (spec file not created).
- Playwright test fails.
- API returns unexpected status code.
- Network request missing from capture.
- Performance test fails (k6 error, threshold exceeded).
- Latency exceeds configured threshold.
- Error rate increases under load.
- Evidence is incomplete.
- Downstream artifact contradicts upstream artifact.
- A stage produces invalid or inconsistent output.
- Stale state detected (artifacts from a previous run reused).
- Incorrect stage status recorded.
- Incorrect routing (stage executed out of order).

**Failure Analysis Artifact Structure:**

For every detected issue, create a structured record:

```
Issue ID       — e.g. FA-001
Source Stage   — e.g. Test Execution, Performance Testing, Discovery
Failure Type   — one of:
                   parsing_error, data_integrity, requirement_gap,
                   execution_failure, environment_blocker,
                   automation_failure, network_failure,
                   performance_failure, artifact_failure,
                   configuration_failure, dependency_failure, unknown
What Failed    — exactly what failed. Do not generalize.
Expected       — what the workflow was expected to produce/do.
Actual         — what actually happened.
Evidence       — reference actual available evidence (artifact path, test
                   output, Playwright error, HTTP response, k6 output,
                   performance metric, stage state, log, screenshot, HAR,
                   report). Do NOT fabricate evidence.
Root Cause     — exactly one of: Confirmed | Probable | Unknown
                   (never invent a root cause)
```

**Root Cause Rules:**

Distinguish Observed from Root Cause.

Observed: "Playwright spec was generated but execution failed with 'no tests found'."

Root Cause (only if implementation/evidence proves it):
"Test-design scenarios did not map to any existing test file in the target repository."

If evidence only shows symptom:
Root Cause: Unknown — insufficient evidence.

Then provide:
Recommended Investigation:
  1. Inspect the generated spec file.
  2. Inspect the target repository's test directory.
  3. Compare scenario IDs to test file names.
  4. Reproduce the execution.
  5. Identify the responsible component.

**Impact:**

For every issue, explain impact. Examples:
- Downstream stage received incomplete requirements.
- Test generation became unreliable.
- Execution could not start.
- Performance testing could not proceed.
- Result cannot be considered valid.
- Regression confidence is reduced.
- Artifact cannot be trusted.

Do NOT exaggerate impact.

**Recommended Solution:**

Must be based on evidence. Examples:
- If parser confirmed as cause: Fix parser to recognize supported Markdown
  heading structure and add regression coverage.
- If environment missing: Configure an approved non-production test environment
  and required credentials.
- If k6 unavailable: Install k6 with explicit project permission, or accept
  performance testing as blocked until k6 is available.
- If root cause unknown: Collect missing evidence before changing implementation.

Do NOT recommend changing timeouts, retry counts, or test logic merely to make
a failure disappear.

**Retest / Verification:**

Every actionable failure must include a verification plan:

Retest:
  1. Apply proposed fix.
  2. Delete/reset affected stage state if required.
  3. Re-run affected stage.
  4. Verify original failure no longer occurs.
  5. Re-run directly dependent downstream stages.
  6. Confirm no regression in a second story where practical.

Failure Analysis must NOT mark an issue resolved merely because a proposed fix
exists.

**Issue Lifecycle:**

Supported states:
`detected | investigating | blocked | fix_proposed | fixed |
retest_required | verified | unresolved`

A failure must NOT become "verified" without actual verification evidence.

**Cross-Stage Propagation:**

If a failure affects downstream stages, record the dependency chain.

Example:

```
FA-001
Source: Test Execution (spec generation)
Failure Type: automation_failure
What Failed: Playwright spec file was not generated for story STORY-BASIC-001
Expected:   Executable spec at shared-state/STORY-BASIC-001/execution/spec/STORY-BASIC-001.spec.js
Actual:    Spec generation returned blocked — no scenarios could be extracted
           from test-design/output.md
Evidence:  shared-state/STORY-BASIC-001/test-design/output.md
           (scenario table missing or unparseable)
Root Cause: Unknown — insufficient evidence to determine why scenarios
           could not be extracted
Impact chain:
  Test Design
    ↓
  incomplete scenario list
    ↓
  Spec Generation
    ↓
  no executable spec
    ↓
  Playwright Execution blocked
    ↓
  Network capture not attempted
    ↓
  Performance testing blocked

Recommended Investigation:
  1. Inspect test-design/output.md format.
  2. Inspect the spec generation helper's scenario parsing logic.
  3. Determine whether the scenario table format changed.
  4. Reproduce the spec generation with the same inputs.
```

The first observed failure may not be the final visible symptom.

**Classification counts:**

Failure Analysis produces classification counts across all categories,
not just product defects and test defects:

| Category | Count | Notes |
|----------|-------|-------|
| Product defect | N | Application behavior does not match expected |
| Test defect | N | Test or automation has a bug |
| Environment issue | N | Target environment problem |
| Data issue | N | Test data or precondition problem |
| Infrastructure issue | N | CI, tooling, or platform problem |
| Parsing error | N | Stage output could not be parsed |
| Data integrity | N | Artifact mismatch or corruption |
| Requirement gap | N | Required information missing from requirement |
| Automation failure | N | Test generation or execution failure |
| Network failure | N | Network capture or API communication failure |
| Performance failure | N | k6 execution failure or threshold exceeded |
| Artifact failure | N | Stage produced invalid/inconsistent output |
| Configuration failure | N | Project adapter misconfigured |
| Dependency failure | N | Required tool or dependency unavailable |
| Unknown | N | Cannot classify with available evidence |

**Failure behavior:**
- If a failure cannot be classified, it is marked `unknown` with the missing
  information recorded. The workflow does not stop on an unknown classification.
- If failure analysis itself fails, the stage is marked `failed` with the
  reason, and the orchestrator records that failure analysis was incomplete.
  The workflow continues to Review, which treats the missing analysis as a
  finding.
- If no failures exist from any stage, the stage is skipped with a recorded
  reason.

**Human approval required:** No. Failure analysis is diagnostic. Human action
may be needed to resolve a product defect or environment issue, but that is
outside the workflow's control.

**Handoff to Stage 12:**
The orchestrator passes the failure-analysis output to the Review stage. If
failure analysis was skipped, the orchestrator passes a note that no failures
were present across any stage.

---

### Stage 12 — Independent QA Review

**Responsible:** Review Agent (`agents/review/AGENT.md`)

**Required inputs:**
- All shared-state artifacts from the current workflow.
- The project adapter.
- The project discovery report.

**Shared-state inputs:**
- `shared-state/<story-id>/story-intake.md`
- `shared-state/<story-id>/discovery/output.md`
- `shared-state/<story-id>/analysis/output.md`
- `shared-state/<story-id>/grill/output.md`
- `shared-state/<story-id>/risk/output.md`
- `shared-state/<story-id>/architecture/output.md`
- `shared-state/<story-id>/specification/output.md`
- `shared-state/<story-id>/test-design/output.md`
- `shared-state/<story-id>/delegation/output.md`
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- `shared-state/<story-id>/failure-analysis/classifications.md`
- `shared-state/<story-id>/failure-analysis/failure-details.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Discovery review.
- Analysis and grill review.
- Specification review.
- Test-design review.
- Implementation/execution review, if applicable.
- Missing coverage.
- Unsupported assumptions.
- Weak or duplicate scenarios.
- Incorrect test levels.
- Residual risks.
- Overall review result.
- Recommended actions.

**Shared-state output:**
- `shared-state/<story-id>/review/review-report.md`
- `shared-state/<story-id>/review/coverage-gap.md`
- `shared-state/<story-id>/review/assumption-audit.md`
- `shared-state/<story-id>/review/risks.md`
- `shared-state/<story-id>/review/unknowns.md`
- `shared-state/<story-id>/review/assumptions.md`

**Preconditions:**
- Stage 11 is `completed` or `skipped`.
- At least discovery, analysis, grill, specification, and test design outputs exist. If some are missing, the review treats their absence as a finding.

**Validation checks:**
- The review is independent and does not rubber-stamp earlier stages.
- Every finding is tied to a specific artifact, requirement item, or project-adapter value.
- Missing coverage is stated relative to the requirement and specification.
- The overall judgment follows from the findings.

**Failure behavior:**
- If the review cannot be completed because required artifacts are missing, the stage is marked `blocked` with the missing artifacts listed. The orchestrator records the gap and proceeds to evidence collection with the review marked incomplete.
- If the review completes with a negative overall judgment, the workflow continues to evidence collection and final reporting; it does not stop. The negative judgment is recorded in the final report.

**Human approval required:** No. The review is advisory. Human action may be needed to address findings, but the workflow records them and continues.

**Handoff to Stage 13:**
The orchestrator passes the review output to the Evidence Collection stage. The evidence stage uses the review to identify any additional evidence that should be collected.

---

### Stage 13 — Evidence Collection

**Responsible:** QA Orchestrator

**Required inputs:**
- The execution run report and evidence index.
- The failure-analysis output.
- The review output.
- The project adapter.

**Shared-state inputs:**
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- `shared-state/<story-id>/failure-analysis/classifications.md`
- `shared-state/<story-id>/review/review-report.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- A consolidated evidence package listing all evidence artifacts, their locations, and what they support.
- Any additional evidence collected at the review's request.
- A note on evidence that could not be collected and why.

**Shared-state output:**
- `shared-state/<story-id>/evidence/consolidated.md`
- Any additional evidence artifacts collected.

**Preconditions:**
- Stage 12 is `completed` or `skipped`.
- Execution evidence exists, or the stage records that no execution was performed.

**Validation checks:**
- The evidence package references real artifacts that exist.
- Missing evidence is noted with the reason it is missing.
- The evidence package is sufficient to support the final report.

**Failure behavior:**
- If evidence cannot be collected because execution did not run, the stage records that fact and continues. The final report reflects that no execution evidence exists.
- If evidence artifacts are missing or corrupted, the stage records the gap and continues.

**Human approval required:** No.

**Handoff to Stage 14:**
The orchestrator passes the consolidated evidence package and all prior stage outputs to the Final QA Report stage.

---

### Stage 14 — Final QA Report

**Responsible:** QA Orchestrator

**Required inputs:**
- All shared-state artifacts from the current workflow.
- The project adapter.

**Shared-state inputs:**
- All stage outputs listed in Stage 12's inputs, plus:
- `shared-state/<story-id>/evidence/consolidated.md`

**Expected output:**
- A final QA report containing:
  - Story and project.
  - Scope covered.
  - Scope not covered and why.
  - Requirement coverage summary.
  - Tests executed and results.
  - Failures and classifications.
  - Root causes.
  - Evidence summary.
  - Review result.
  - Residual risks.
  - Assumptions.
  - Unknowns.
  - Remaining actions.
  - Whether human follow-up is required.

**Shared-state output:**
- `shared-state/<story-id>/final-report.md`

**Preconditions:**
- Stage 13 is `completed`.
- All prior stages are `completed`, `skipped`, or `blocked` with recorded reasons.

**Validation checks:**
- The final report accounts for every stage, including those that were blocked, skipped, or failed.
- The final report does not present assumptions as confirmed facts.
- The final report clearly separates what was done from what was not done and why.
- The final report does not invent results that were not produced.

**Failure behavior:**
- If the final report cannot be produced because required stage outputs are missing, the orchestrator produces a partial report that records the missing outputs and the stage status of the workflow. The workflow ends with a partial report rather than no report.

**Human approval required:** No. The final report is the deliverable. Human action may be required to address remaining actions, but the workflow's job is to produce the report.

**Handoff:**
There is no further stage. The workflow ends. The orchestrator sets the overall run status to `completed` in `stage-status.json` and records the final report location.

## Handoff Summary

|| From | To | Handoff contents |
||---|---|---|
|| Story Intake | Project Discovery | Story, acceptance criteria, story-id |
|| Project Discovery | Requirement Analysis | Discovery report, project identifier, story-id |
|| Requirement Analysis | QA Grill | Analysis output, discovery report, story-id |
|| QA Grill | Risk Analysis | Grill output, analysis output, discovery report, story-id |
|| Risk Analysis | Test Architecture | Risk output, grill output, analysis output, discovery report, story-id |
|| Test Architecture | QA Specification | Architecture output, risk output, grill output, analysis output, discovery report, story-id |
|| QA Specification | Test Design | Specification output, grill output, architecture output, discovery report, story-id |
|| Test Design | Specialist Delegation | Test-design output, architecture output, discovery report, project adapter, story-id |
|| Specialist Delegation | Test Execution | Delegation records, test-design output, project adapter, story-id |
|| Test Execution | Failure Analysis | Execution run report, evidence index, network artifacts, request inventory, performance artifacts, test-design output, specification output, project adapter, story-id |
|| Failure Analysis | Independent QA Review | Failure-analysis output, execution run report, evidence index, all prior outputs, project adapter, story-id |
|| Independent QA Review | Evidence Collection | Review output, execution run report, evidence index, failure-analysis output, project adapter, story-id |
|| Evidence Collection | Final QA Report | Consolidated evidence package, all prior outputs, project adapter, story-id |

## Error and Block Behavior

### Required information is missing

If a stage requires information that is not in the project adapter or shared state, the stage is marked `blocked` with the specific missing item recorded. The workflow does not invent the information. Downstream stages are not started until the block is resolved or the workflow is restarted with the missing information provided.

### An agent fails

If an agent fails in a way that prevents it from completing its stage, the stage is marked `failed` with the reason recorded. The orchestrator:

- Does not silently continue as if the stage succeeded.
- Treats downstream stages as `pending` so they do not run on incomplete input.
- Allows the workflow to be resumed after the agent failure is resolved, restarting the failed stage and any downstream stages.

### A test fails

If a test fails during execution, the execution stage records the failure and continues with the remaining tests where possible. The failure is handed to the Failure Analysis stage for classification. A test failure does not stop the workflow unless it blocks all remaining execution and there is no way to proceed.

### An environment is unavailable

If the target environment is unavailable, the execution stage marks the affected tests as `blocked` with `environment unavailable`. The orchestrator:

- Does not invent an environment.
- Does not proceed with execution against an environment not declared in the project adapter.
- Continues with any executions that do not depend on the unavailable environment.
- Records the environment problem in the final report.

### Credentials are missing

If credentials required for a step are missing from the project adapter, the step is marked `blocked` with the reason `credentials missing`. The orchestrator:

- Does not invent credentials.
- Does not ask the user to invent credentials in the workflow output.
- Records the blocking dependency and stops the affected path.

### The project safety configuration blocks an action

If the project safety configuration blocks an action, the step is marked `blocked` with the safety constraint recorded. The orchestrator:

- Does not override the safety configuration.
- Does not proceed with the blocked action.
- Records the block and continues with actions that are not blocked.

### The agent detects a product defect

If a failure is classified as a product defect, the Failure Analysis stage records the classification, the evidence, and the expected behavior it violated. The workflow continues. The product defect is recorded in the final report and flagged for human follow-up. The workflow does not fix the product defect.

### The agent detects a test defect

If a failure is classified as a test defect, the Failure Analysis stage records the classification and the specific defect in the test or automation. The workflow continues. The test defect is recorded in the final report. If the test defect invalidates the test results, the execution stage's affected results are flagged as unreliable.

### The agent detects an environment problem

If a failure is classified as an environment issue, the Failure Analysis stage records the classification and the environment problem. The workflow continues. The environment problem is recorded in the final report. If the environment problem blocks execution, the execution stage's affected tests are marked as blocked.

## Resume and Restart

### Resume

The workflow resumes from the first stage whose status is not `completed` and not `skipped`. If that stage is `in_progress`, the orchestrator asks whether to resume or restart it. If the stage is `blocked` or `failed`, the orchestrator reports the block or failure and waits for resolution before resuming.

### Restart a stage

A stage may be restarted from the beginning. Restarting a stage:

- Resets that stage to `pending`.
- Resets all downstream stages to `pending`.
- Preserves upstream completed stages.
- Requires the restarted stage to re-validate its preconditions and re-run its validation checks.

### Abort

The workflow may be aborted at any stage by a human decision. Abort sets the overall run status to `aborted` and records the stage at which it was aborted and the reason. Partial artifacts already produced are preserved.

## Final Status

The workflow ends with one of these overall statuses:

- `completed` — all stages completed or were deliberately skipped with recorded reasons.
- `partial` — the workflow ended with a partial report because some stage outputs were missing.
- `blocked` — the workflow stopped at a stage that could not proceed and the block was not resolved.
- `failed` — the workflow stopped because a stage failed and the failure was not resolved.
- `aborted` — the workflow was aborted by human decision.

The final status, the final report location, and the stage status of every stage are recorded in `shared-state/<story-id>/stage-status.json`.
