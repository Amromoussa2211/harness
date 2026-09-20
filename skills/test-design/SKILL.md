---
name: test-design
description: Converts a QA specification into concrete test scenarios with test levels, automation candidates, and manual-validation markers, without implementing automation.
version: 0.1.0
---

# Test Design

## Purpose

Convert a QA specification into concrete test scenarios and decide, for each scenario, the most appropriate test level and execution approach. Test design is about deciding what to test and where to test it — not about implementing the automation yet.

## Inputs

- The QA Specification for the story under test.
- The QA Grill output and any clarification answers.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application type, API types, database usage, automation framework and language hints, environments, and safety constraints.
- Relevant shared-state artifacts from earlier workflow steps, including discovery findings, analyst output, and any test-architecture decisions.
- The test-architecture strategy from the architect agent, if available.

If the QA specification is missing or incomplete, the test design must say so and must not silently fill gaps.

## Process

### 1. Read the specification

Read the QA specification end to end. Identify each area of coverage the specification defines: functional, negative, boundary, integration, validation expectations, required test data, and required environment dependencies.

### 2. Convert coverage into concrete scenarios

For each coverage area, produce concrete test scenarios:

- Positive scenarios for the primary behaviors.
- Negative scenarios for invalid, missing, malformed, or failed inputs and preconditions.
- Boundary scenarios for edges, limits, and transitions.
- Validation scenarios for the specific evidence needed to confirm behavior.
- Integration scenarios for cross-boundary data flows, events, and consistency.
- Regression scenarios for behaviors at risk from the change.
- Error-handling scenarios for failures, fallbacks, retries, and recovery where the specification calls for them.

Each scenario must be concrete enough that someone could later implement it. Each scenario must trace back to a specific part of the specification. Do not invent scenarios that the specification does not support.

### 3. Assign the appropriate test level

For each scenario, assign the lowest appropriate test level:

- unit
- component
- API
- UI
- integration
- database
- end-to-end

Prefer the lowest level that can validly validate the scenario. Use API or component-level validation instead of UI when the same risk can be covered there and the project adapter supports that layer. Use UI or end-to-end only when user-visible behavior, browser state, or a full user journey is what must be validated.

Do not assign a test level based on convenience. Assign it based on what the scenario actually needs to validate and what the project adapter makes available.

### 4. Identify automation candidates

For each scenario, identify whether it is a good automation candidate:

- Deterministic behavior.
- Stable, observable outcomes.
- Repeatable setup and teardown.
- Clear pass/fail criteria.

Also identify scenarios that are poor automation candidates:

- Heavy manual judgment.
- Hard-to-stabilize timing or environment dependencies.
- Outcomes that are better verified by inspection or exploration.

Mark each scenario accordingly. Do not assume every scenario should be automated.

### 5. Identify scenarios requiring manual validation

Identify scenarios that require manual validation:

- Exploratory or judgment-heavy checks.
- Visual, usability, or experience concerns where the project adapter indicates they matter.
- Scenarios where the required evidence is not yet automatable given the project adapter's declared framework and environment.

For each, state what must be manually judged and why.

### 6. Map test data and environment needs

For each scenario, restate the test data and environment dependencies it needs, drawing from the specification. If a scenario needs data or an environment that the project adapter does not provide, mark that scenario as blocked on data or environment, not as implementable.

### 7. Keep scope honest

Separate:

- Scenarios that are in scope for this story.
- Scenarios that are adjacent but out of scope.
- Scenarios that are missing because the specification did not define them.

Do not expand scope silently. If a risk appears under-covered, flag it rather than inventing new requirements to cover it.

## Rules

- Follow AGENTS.md.
- Never invent project-specific information.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Do not invent requirements, acceptance criteria, expected outcomes, API contracts, database schemas, selectors, credentials, or business rules.
- Do not implement automation in this skill. Test design stops at scenario definition, test level, and automation candidacy.
- Prefer the lowest appropriate test level for each scenario.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The same scenario categories, test levels, and candidacy decisions apply to every project; only the project adapter contents differ.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured Test Design containing:

1. Requirement under design
2. Scenario list
   - For each scenario: name, description, linked specification item, test level, positive/negative/boundary/integration/regression/error-handling classification, automation candidate yes/no/maybe, manual validation required yes/no, required test data, required environment dependencies, notes
3. Test-level rationale summary
4. Automation candidates
5. Manual-validation scenarios
6. Scenarios blocked on missing data or environment
7. Out-of-scope scenarios
8. Assumptions
9. Unknowns

The scenario list is the core artifact. It must be specific, traceable, and level-assigned, but it must not contain implemented test code.

## Quality Checks

Before finalizing, verify:

- Every scenario traces to a specification item.
- Every scenario has an assigned test level with a rationale.
- Lower test levels were preferred where valid.
- Automation candidacy is marked per scenario, not assumed uniform.
- Manual-validation scenarios are called out explicitly.
- Scenarios blocked on missing data or environment are identified.
- Out-of-scope items are stated as out of scope, not silently omitted.
- No invented selectors, endpoints, schemas, credentials, or data values appear.
- Assumptions and unknowns are labeled.
- Nothing depends on company-specific information outside the project adapter or shared state.
