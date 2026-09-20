---
name: risk-analysis
description: Identifies and prioritizes business, technical, integration, data, and regression risks for a QA story based on grill output, analysis, discovery, and project adapter.
version: 0.1.0
---

# Risk Analysis

## Purpose

Identify and prioritize risks to the successful delivery and testing of a software feature. Risk analysis cross-references findings from the grill, analysis, discovery, and project adapter to produce a structured risk assessment that distinguishes blocking risks from noted-but-non-blocking risks.

## Inputs

- The QA Grill output for the story under review.
- The Requirement Analysis output for the same story.
- The Project Discovery report for the project.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application, its contracts, its environments, or its safety constraints.

If the grill output, analysis output, or discovery report is missing, the risk stage must say so and must not silently proceed as if they were complete.

## Process

### 1. Read all prior-stage outputs

Read the grill output, analysis output, discovery report, and project adapter. Understand the ambiguities, missing requirements, negative scenarios, edge cases, integration risks, regression risks, data risks, and blockers identified by prior stages.

### 2. Identify business risks

Look for risks that affect the business value of the feature:

- Undefined or ambiguous requirements that block test scope determination.
- Missing error message text or validation expectations that prevent test confirmation.
- Undefined destinations or states that block pass/fail criteria.
- Behavior for edge-case inputs that is unspecified.
- Security or compliance concerns not addressed.

### 3. Identify technical risks

Look for risks that affect the ability to implement and execute tests:

- No environments enabled.
- No application under test.
- No test framework or automation in place.
- Ambiguous authentication or session management.
- Missing test credentials.

### 4. Identify integration risks

Look for risks that affect integration points:

- REST API declared but endpoints unknown.
- Database disabled but credential storage may need one.
- No CI/CD pipeline.
- External service dependencies not specified.

### 5. Identify data risks

Look for risks that affect test data and state:

- No test credentials available.
- Precondition data dependencies undefined (e.g., "registered user exists").
- No test data management strategy.
- Data privacy or storage concerns not addressed.

### 6. Identify regression risks

Look for risks that affect regression safety:

- Feature is a core user journey with no existing tests.
- High-change-risk entry points (validation fields, session management).
- No regression safety net.

### 7. Categorize and prioritize

For each risk, assign a category (Business, Technical, Integration, Data, Regression) and a severity where determinable (Critical, High, Medium, Low).

### 8. Separate blocking from non-blocking

Clearly separate risks that must be resolved before testing can proceed from risks that are noted but do not block testing.

### 9. Record assumptions and unknowns

State every assumption made and every piece of information that could not be determined.

## Rules

- Follow AGENTS.md.
- Never invent risks. Every risk must be tied to a specific finding from a prior stage or the project adapter.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The same risk categories and process apply to every project; only the project adapter contents differ.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured Risk Analysis containing:

1. Purpose
2. Risk identification methodology
3. Business risks
4. Technical risks
5. Integration risks
6. Data risks
7. Regression risks
8. Risks that must be addressed before testing
9. Risks that do not block testing
10. Assumptions
11. Unknowns

Each risk must state its category, source, impact, mitigation, and severity where determinable. Risks that must be addressed before testing must be clearly identified in a dedicated section.

## Quality Checks

Before finalizing, verify:

- Every risk is tied to a specific finding from a prior stage or the project adapter.
- No invented risks appear.
- Blocking risks are clearly separated from non-blocking risks.
- Severity assignments are grounded in the impact described.
- Risks are distinguishable from the grill's raw findings — the risk stage should prioritize and contextualize, not merely repeat.
- Assumptions and unknowns are clearly labeled.
- Nothing in the report depends on company-specific information that is not in the project adapter or shared state.
