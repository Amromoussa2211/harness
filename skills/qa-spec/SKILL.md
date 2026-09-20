---
name: qa-spec
description: Converts a reviewed QA story and grill output into a testable QA specification with functional, negative, boundary, integration, and validation coverage, plus required test data and environment dependencies.
version: 0.1.0
---

# QA Specification

## Purpose

Turn a reviewed QA story and its grill results into a testable QA specification. The specification defines what must be validated, at what level, with what data and environments — and it keeps confirmed requirements strictly separated from assumptions. It is the bridge between the grilled requirement and concrete test design.

## Inputs

- The QA story or requirement under test.
- The acceptance criteria attached to the story.
- The QA Grill output for the same story, if available.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application, its contracts, its environments, its safety constraints, its test data, or its conventions.
- Relevant shared-state artifacts from earlier workflow steps, including discovery findings and any analyst output.
- The clarification questions and answers produced during grilling, if any exist.

If the requirement, acceptance criteria, or grill results are missing, the specification must say so and must not silently proceed as if they were complete.

## Process

### 1. Restate the requirement

Restate the requirement and its acceptance criteria in testable terms. Use only what is confirmed by the inputs. If any acceptance criterion is ambiguous or missing, note that and do not convert it into a hard requirement.

### 2. Define functional coverage

Define the functional coverage for the story:

- The primary behaviors that must work.
- The acceptance criteria that map to each behavior.
- The confirmation method for each behavior, where determinable from the inputs.

Do not add functional coverage beyond what the requirement and acceptance criteria justify.

### 3. Define negative coverage

Define the negative coverage derived during grilling:

- Invalid, missing, malformed, or out-of-range inputs.
- Failed preconditions.
- Failed or unavailable dependencies.
- Permission, authentication, and authorization failures.
- Rate limits, quotas, and guardrail violations.

For each negative case, state the scenario and what must be validated. If the expected outcome is not defined in the inputs, mark the expected outcome as missing rather than inventing it.

### 4. Define boundary coverage

Define the boundary coverage:

- Empty, null, zero, maximum, and minimum values.
- Size, count, duration, and range limits.
- Transitional and intermediate states.
- Repeated, concurrent, or re-entrant operations where relevant.

For each boundary, state what is being bounded and why it matters. Use only data ranges and limits that appear in the project adapter, shared state, or the requirement itself.

### 5. Define integration coverage

Define the integration coverage:

- Which external systems, APIs, databases, webhooks, or downstream consumers are in scope.
- Which data flows cross a boundary.
- Which contracts, events, or states must remain consistent.
- Which failure and recovery paths must be validated.

Use only the dependencies and boundaries described in the project adapter or shared state. Do not invent integrations.

### 6. Define validation expectations

For each area of coverage, define the validation expectation:

- What evidence would satisfy the validation.
- What must be observable to call the behavior verified.
- Which layer the validation should occur at, where that is determinable.

If the validation expectation cannot be determined from the inputs, mark it as missing.

### 7. Identify required test data

Identify the test data required to execute the specification:

- Data that must exist before testing.
- Data that must be created, modified, or cleaned up.
- Data that must be stable, deterministic, or isolated.
- Data that must represent specific states or edge conditions.

Use only data requirements grounded in the project adapter or shared state. Do not invent test data values unless the project adapter provides a concrete source for them.

### 8. Identify required environment dependencies

Identify the environment dependencies required to validate the specification:

- Environments that must be available.
- Services, endpoints, databases, or external systems that must be reachable.
- Configuration, credentials, or access that must be present.
- Any safety constraints from the project adapter that affect where validation may occur.

If an environment dependency is missing or not declared, mark it as a blocking unknown.

### 9. Separate confirmed requirements from assumptions

Produce an explicit separation:

- Confirmed requirements: items grounded in the requirement text, acceptance criteria, project adapter, or shared state.
- Assumptions: items the specification relies on but that are not confirmed by the inputs.
- Unknowns: items that cannot be determined from the inputs.

The specification must not present assumptions as if they were confirmed requirements.

## Rules

- Follow AGENTS.md.
- Never invent project-specific information.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Do not invent requirements, acceptance criteria, expected outcomes, API contracts, database schemas, selectors, credentials, or business rules.
- Do not fill gaps by guessing. Mark missing information as missing.
- Keep confirmed requirements and assumptions strictly separated.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The same sections and process apply to every project; only the project adapter contents differ.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured QA Specification containing:

1. Requirement under specification
2. Functional coverage
3. Negative coverage
4. Boundary coverage
5. Integration coverage
6. Validation expectations
7. Required test data
8. Required environment dependencies
9. Confirmed requirements
10. Assumptions
11. Unknowns
12. Items blocked pending clarification

Each coverage area must be specific enough that a later test-design step can convert it into concrete scenarios. Each item must state its source: requirement, acceptance criterion, project adapter, shared state, or assumption.

## Quality Checks

Before finalizing, verify:

- Every coverage area is tied back to a requirement, acceptance criterion, project adapter value, or shared-state artifact.
- No invented expected outcomes appear as if they were confirmed.
- Negative coverage exists where the requirement implies failure paths.
- Boundary coverage names concrete boundaries, not vague phrases.
- Integration coverage names real dependencies from the inputs.
- Required test data and environment dependencies are stated concretely enough to act on.
- The confirmed/assumption/unknown separation is explicit and complete.
- No company-specific information appears that is not from the project adapter or shared state.
- The specification does not silently assume answers to open clarification questions.
