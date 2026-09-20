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

**Responsible:** QA Orchestrator, using the grill output and analyst output

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
- The implemented tests produced by the delegated specialists.
- The project adapter.
- The shared state from all prior stages.

**Shared-state inputs:**
- `shared-state/<story-id>/delegation/output.md`
- All specialist outputs.
- `projects/<project-name>/project.yaml`
- All prior stage outputs.

**Expected output:**
- Which tests ran.
- Which environment was used.
- Pass/fail summary.
- Evidence index.
- Blocked or skipped tests with reasons.

**Shared-state output:**
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- Per-test evidence artifacts as referenced in the evidence index.

**Preconditions:**
- Stage 9 is `completed`.
- Implemented tests exist for the delegations that are scheduled to run.
- The target environment is declared in the project adapter and available.
- Safety gates permit the intended execution.

**Validation checks:**
- Only tests that were implemented are executed. The execution stage does not create new tests.
- Execution uses only environments declared in the project adapter.
- Safety gates are respected.
- Evidence is collected and indexed.

**Failure behavior:**
- If the target environment is unavailable, the execution stage marks the affected tests as `blocked` with the reason `environment unavailable`. The orchestrator records the environment problem and continues with any executions that do not depend on that environment.
- If no implemented tests exist for a delegation, the execution stage marks that delegation as `blocked` with the reason `no implemented tests`. The orchestrator records the gap.
- If execution fails due to a runtime error not caused by the application, the execution stage records the failure as a test or environment issue and continues with the remaining tests where possible.
- If execution is blocked by a safety gate, the stage marks the affected tests as `blocked` with the safety constraint and continues with others.

**Human approval required:** Yes for any execution that the safety gates require explicit authorization for. No for read-only execution in allowed environments.

**Handoff to Stage 11:**
The orchestrator passes the execution run report and evidence index to the Failure Analysis stage. If there are no failures, the orchestrator may skip Stage 11 and proceed directly to Stage 12, recording that failure analysis was skipped because there were no failures.

---

### Stage 11 — Failure Analysis

**Responsible:** Failure Analysis Agent (`agents/failure-analysis/AGENT.md`)

**Required inputs:**
- The execution run report.
- The evidence index.
- The test-design output.
- The specification output.
- The project adapter.

**Shared-state inputs:**
- `shared-state/<story-id>/execution/run-report.md`
- `shared-state/<story-id>/execution/evidence-index.md`
- `shared-state/<story-id>/test-design/output.md`
- `shared-state/<story-id>/specification/output.md`
- `projects/<project-name>/project.yaml`

**Expected output:**
- Number of failures analyzed.
- Classification counts by category: product defect, test defect, environment issue, data issue, infrastructure issue, unknown.
- Per-failure detail with evidence, reasoning, and alternative explanations.
- Failures that could not be classified and what is missing.

**Shared-state output:**
- `shared-state/<story-id>/failure-analysis/classifications.md`
- `shared-state/<story-id>/failure-analysis/failure-details.md`
- `shared-state/<story-id>/failure-analysis/unknowns.md`
- `shared-state/<story-id>/failure-analysis/assumptions.md`

**Preconditions:**
- Stage 10 is `completed`.
- At least one failure exists to analyze, or the stage is skipped with a recorded reason.

**Validation checks:**
- Every classification is supported by evidence.
- No failure is classified as a product defect unless the expected behavior is confirmed from the project adapter or shared state.
- No failure is classified as a test defect without identifying the specific test defect.
- Unknown classifications record what additional information would be needed.

**Failure behavior:**
- If a failure cannot be classified, it is marked `unknown` with the missing information recorded. The workflow does not stop on an unknown classification.
- If failure analysis itself fails, the stage is marked `failed` with the reason, and the orchestrator records that failure analysis was incomplete. The workflow continues to Review, which treats the missing analysis as a finding.

**Human approval required:** No. Failure analysis is diagnostic. Human action may be needed to resolve a product defect or environment issue, but that is outside the workflow's control.

**Handoff to Stage 12:**
The orchestrator passes the failure-analysis output to the Review stage. If failure analysis was skipped, the orchestrator passes a note that no failures were present.

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

| From | To | Handoff contents |
|---|---|---|
| Story Intake | Project Discovery | Story, acceptance criteria, story-id |
| Project Discovery | Requirement Analysis | Discovery report, project identifier, story-id |
| Requirement Analysis | QA Grill | Analysis output, discovery report, story-id |
| QA Grill | Risk Analysis | Grill output, analysis output, discovery report, story-id |
| Risk Analysis | Test Architecture | Risk output, grill output, analysis output, discovery report, story-id |
| Test Architecture | QA Specification | Architecture output, risk output, grill output, analysis output, discovery report, story-id |
| QA Specification | Test Design | Specification output, grill output, architecture output, discovery report, story-id |
| Test Design | Specialist Delegation | Test-design output, architecture output, discovery report, project adapter, story-id |
| Specialist Delegation | Test Execution | Delegation records, implemented tests, project adapter, story-id |
| Test Execution | Failure Analysis | Execution run report, evidence index, test-design output, specification output, project adapter, story-id |
| Failure Analysis | Independent QA Review | Failure-analysis output, execution run report, evidence index, all prior outputs, project adapter, story-id |
| Independent QA Review | Evidence Collection | Review output, execution run report, evidence index, failure-analysis output, project adapter, story-id |
| Evidence Collection | Final QA Report | Consolidated evidence package, all prior outputs, project adapter, story-id |

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
