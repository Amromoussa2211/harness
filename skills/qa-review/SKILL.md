---
name: qa-review
description: Independently reviews the complete QA work — discovery, analysis, grill, specification, and test design — to identify missing coverage, unsupported assumptions, weak or duplicate scenarios, incorrect test levels, and residual risks.
version: 0.1.0
---

# QA Review

## Purpose

Provide an independent review of the complete QA work produced for a story or change. The review does not defend the earlier steps and does not rubber-stamp them. It examines whether the work as a whole is sound, complete, appropriately leveled, and free of unsupported assumptions — and it produces a final QA review with concrete findings.

## Inputs

- The discovery artifacts for the project.
- The QA analysis artifacts, if any exist.
- The QA Grill output for the story under review.
- The QA Specification for the story under review.
- The Test Design for the story under review.
- Any test-implementation or execution artifacts that exist at review time.
- Any failure-analysis artifacts that exist at review time.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application, its contracts, its environments, its safety constraints, or its conventions.
- Any relevant shared-state artifacts from the current workflow.

If the body of QA work is missing key steps, the review must say so and treat the missing step as a finding, not as evidence that the step was completed satisfactorily.

## Process

### 1. Reconstruct the requirement context

Reconstruct what the QA work was supposed to cover:

- The requirement or story under test.
- The acceptance criteria.
- The application type, API types, database usage, environments, and safety constraints from the project adapter.
- Any clarification questions and answers that shaped the work.

If the requirement context cannot be reconstructed from the inputs, report that as a blocker.

### 2. Review discovery

Review the discovery work:

- Whether the technology stack, application architecture, API architecture, database, authentication, CI/CD, environments, existing tests, existing fixtures, and test utilities were identified or explicitly marked unknown.
- Whether anything material was assumed rather than discovered.
- Whether the discovery supports the later steps.

Flag discovery gaps that undermine later coverage.

### 3. Review analysis and grill

Review the analysis and grill work:

- Whether the requirement and acceptance criteria were challenged.
- Whether ambiguity, missing requirements, negative scenarios, edge cases, integration risks, and regression risks were identified.
- Whether clarification questions were generated where needed.
- Whether the grilled gaps were carried forward into the specification or silently dropped.

### 4. Review the specification

Review the QA specification:

- Whether the functional, negative, boundary, integration, and validation coverage is complete relative to the requirement and the grill output.
- Whether confirmed requirements are separated from assumptions.
- Whether required test data and environment dependencies are identified.
- Whether any missing requirement was invented to fill a gap.

### 5. Review the test design

Review the test design:

- Whether every scenario traces to a specification item.
- Whether the assigned test levels are appropriate and the lowest appropriate level was preferred.
- Whether automation candidates and manual-validation scenarios are correctly identified.
- Whether any scenarios are weak, overly broad, likely to pass for the wrong reasons, or duplicates of other scenarios.
- Whether scenarios blocked on missing data or environment are identified.
- Whether the design over-uses UI or end-to-end where a lower layer would do.

### 6. Review any implementation or execution that exists

If implementation or execution artifacts exist, review them briefly for consistency with the design:

- Do the implemented tests match the designed scenarios?
- Do the execution results align with the test design's expectations?
- Are there failures that were not analyzed, or analyses that do not match the evidence?

If no implementation or execution exists yet, say so and limit the review to discovery, analysis, grill, specification, and test design.

### 7. Identify missing coverage

Identify missing coverage:

- Requirement behavior with no corresponding test.
- Acceptance criteria that were not validated.
- Negative, boundary, integration, or error-handling scenarios that were omitted.
- Dependencies or boundaries that were overlooked.
- Safety or destructive-operation concerns that were not addressed.

Do not invent coverage beyond what the requirement, project adapter, and shared state justify. Report what is missing relative to what was promised.

### 8. Identify unsupported assumptions

Identify assumptions across the work:

- Assumptions presented as confirmed.
- Assumptions that are not supported by the project adapter or shared state.
- Assumptions that would break the tests if they are wrong.
- Assumptions that were never stated explicitly.

For each, state the assumption, where it appears, and why it is unsupported or risky.

### 9. Identify weak or duplicate scenarios

Identify weak scenarios:

- Scenarios with vague pass/fail criteria.
- Scenarios that assert too little to be meaningful.
- Scenarios that are likely to be flaky or environment-dependent.
- Scenarios that validate the wrong thing.

Identify duplicate scenarios:

- Scenarios that cover the same risk as another scenario without adding value.
- Redundant automation at different levels for the same behavior without justification.

### 10. Identify incorrect test levels

Identify test-level problems:

- Scenarios placed at UI or end-to-end when a lower level would be more appropriate and the project adapter supports that lower level.
- Scenarios placed at a level that cannot actually validate the intended behavior.
- Missing lower-level coverage where the risk would be cheaper and stronger to cover there.

### 11. Identify risks

Identify residual risks after the QA work:

- Business risk from under-tested behavior.
- Technical risk from fragile or weak tests.
- Environment risk from untested or unavailable environments.
- Data risk from untested or unvalidated data behavior.
- Regression risk from missing or thin coverage.
- Safety risk from execution in restricted environments.

### 12. Produce the final QA review

Produce a final QA review that summarizes the overall state of the work, the strongest findings, and what must be resolved before the work can be considered adequate.

## Rules

- Follow AGENTS.md.
- Never invent project-specific information.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Do not invent requirements, acceptance criteria, expected outcomes, API contracts, database schemas, selectors, credentials, or business rules to judge the work.
- Review independently. Do not assume earlier agents were correct.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The same review concerns apply to every project; only the project adapter contents differ.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured QA Review containing:

1. Project and requirement under review
2. Artifacts reviewed
3. Discovery review
4. Analysis and grill review
5. Specification review
6. Test-design review
7. Implementation/execution review, if applicable
8. Missing coverage
9. Unsupported assumptions
10. Weak or duplicate scenarios
11. Incorrect test levels
12. Residual risks
13. Overall review result
14. Recommended actions
15. Assumptions made in the review
16. Unknowns

The overall review result must be a clear judgment: for example, adequate with noted risks, inadequate with specific gaps, or blocked pending missing information. The judgment must be supported by the findings above it.

## Quality Checks

Before finalizing, verify:

- Every finding is tied to a specific artifact, requirement item, or project-adapter value.
- Missing coverage is stated relative to the requirement and specification, not invented.
- Unsupported assumptions are named and sourced.
- Weak and duplicate scenarios are identified with a reason.
- Incorrect test levels are identified with the better alternative and why.
- Risks are specific and actionable.
- The overall judgment follows from the findings.
- The review does not assume missing artifacts exist.
- No company-specific information appears that is not from the project adapter or shared state.
- Assumptions and unknowns in the review itself are labeled.
