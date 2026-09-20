---
name: qa-grill
description: Challenges a QA story and its acceptance criteria to surface ambiguity, missing requirements, negative scenarios, edge cases, integration risks, and regression risks before specification begins.
version: 0.1.0
---

# QA Grill

## Purpose

Stress-test a QA story and its acceptance criteria before anyone writes tests or specifications. The skill exists to find what is missing, unclear, risky, or untestable in the requirement as stated, and to generate focused clarification questions — not to answer them on the project's behalf.

## Inputs

- The QA story, user story, requirement, or change description under review.
- The acceptance criteria attached to that story, if any.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application, its contracts, its environments, or its safety constraints.
- Relevant shared-state artifacts from earlier workflow steps, if any exist (discovery, analysis, prior grill output).
- The requirement's context: what is changing, what is at risk, and what depends on it.

If the requirement itself cannot be obtained from the inputs, stop and report that the requirement is missing.

## Process

### 1. Read the requirement and acceptance criteria

Read the story and its acceptance criteria carefully. Restate each acceptance criterion in your own words to confirm understanding. If the requirement or acceptance criteria are missing, ambiguous, or contradictory, record that immediately and do not proceed as if they were complete.

### 2. Identify ambiguity

For each requirement and each acceptance criterion, ask:

- What terms are undefined or overloaded?
- What behavior is implied but not stated?
- What is left open to interpretation?
- Where could two reasonable reviewers read the requirement differently?

Record each ambiguity explicitly. Do not resolve ambiguity by guessing the intended meaning.

### 3. Identify missing requirements

Identify requirement-level gaps:

- Expected behavior that the story implies but does not state.
- Behavior that users or downstream systems depend on but that the story does not address.
- States, transitions, or outcomes that are missing.
- Error, failure, or exceptional behavior that is not covered.
- Security, privacy, compliance, or accessibility concerns that the story does not address but that the project adapter or shared state indicate are relevant.

Do not invent requirements to fill these gaps. Name the gap and mark it as missing.

### 4. Identify negative scenarios

Derive the negative space around the story:

- What happens when inputs are invalid, missing, malformed, or out of range?
- What happens when preconditions are not met?
- What happens when dependencies fail or are unavailable?
- What happens when the user lacks permission, authentication, or authorization?
- What happens when rate limits, quotas, or guardrails are hit?

For each, state the scenario and the risk it addresses. Do not fabricate expected outcomes unless the project adapter or a prior artifact explicitly defines them.

### 5. Identify edge cases

Identify edge cases:

- Empty, null, zero, maximum, minimum, and boundary values.
- Very large or very small inputs.
- Simultaneous or repeated operations.
- Intermediate, partially-complete, or transitional states.
- Idempotency and re-entrance where relevant.

For each, note why it matters and what would make it testable. Do not invent data values beyond what the project adapter or shared state provide.

### 6. Identify integration risks

Identify integration and dependency risks:

- External systems, APIs, databases, webhooks, or third-party services the story touches.
- Data flow across boundaries.
- Timing, ordering, and consistency concerns.
- Eventual consistency, retries, and failure recovery.
- Contracts that the story depends on but does not control.

Use only the dependencies described in the project adapter or shared state. Do not invent dependencies.

### 7. Identify regression risks

Identify regression risks:

- What existing behavior could this change break?
- What assumptions does the change rely on that may already be fragile?
- What areas are coupled to the changed behavior?
- What is the blast radius if the change is wrong?

Ground regression risks in the project adapter and shared state. Do not assume prior behavior that is not documented somewhere in the inputs.

### 8. Generate clarification questions

Produce a focused set of questions the stakeholder or product owner should answer before specification begins. Each question should be tied to a specific ambiguity, gap, risk, or missing acceptance criterion found above.

Do not invent answers. If a question cannot be answered from the inputs, leave it as a question and mark the dependency.

### 9. Separate confirmed from unconfirmed

Clearly separate:

- What is confirmed by the requirement and acceptance criteria as stated.
- What is implied but not confirmed.
- What is missing entirely.

Do not blur these categories.

## Rules

- Follow AGENTS.md.
- Never invent project-specific information.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Do not invent requirements, acceptance criteria, expected behaviors, API contracts, database schemas, selectors, credentials, or business rules to fill gaps.
- Do not answer your own clarification questions on the project's behalf.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The skill works the same way regardless of the project; only the project adapter changes.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured QA Grill report containing:

1. Requirement under review
2. Acceptance criteria reviewed
3. Ambiguities
4. Missing requirements
5. Negative scenarios
6. Edge cases
7. Integration risks
8. Regression risks
9. Clarification questions
10. Confirmed vs unconfirmed separation
11. Assumptions
12. Unknowns
13. Blockers for specification

Each section must state whether it is grounded in the project adapter, in shared state, in the requirement text, or in analysis — and must say when something could not be determined.

## Quality Checks

Before finalizing, verify:

- Every ambiguity is tied to a specific requirement or acceptance criterion.
- Every missing requirement is stated as missing, not silently filled in.
- Every negative scenario has a reason it matters.
- Every edge case has a trigger or condition, not just a vague mention.
- Every integration risk names the dependency or boundary involved.
- Every regression risk names what could break and why.
- Every clarification question is answerable by a human stakeholder, not by imagination.
- No invented answers appear in the output.
- The confirmed/unconfirmed separation is explicit.
- Assumptions and unknowns are clearly labeled.
- Nothing in the report depends on company-specific information that is not in the project adapter or shared state.
