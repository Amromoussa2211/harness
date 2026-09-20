---
name: qa-review
description: Independently reviews the complete QA work — discovery, analysis, grill, specification, and test design — to identify missing coverage, unsupported assumptions, weak or duplicate scenarios, incorrect test levels, and residual risks.
version: 0.1.0
---

# QA Review

## Purpose

Provide independent quality assurance review of the QA work produced by earlier workflow stages. The review examines whether the discovery, analysis, grill, specification, and test design are thorough, honest, and appropriate — without rubber-stamping them. It identifies gaps, weak spots, unsupported assumptions, and residual risks, and produces a clear overall judgment with recommended actions.

## Inputs

- All shared-state artifacts from the current workflow:
  - story-intake.md
  - discovery/output.md
  - analysis/output.md
  - grill/output.md and grill/questions.md
  - risk/output.md
  - architecture/output.md
  - specification/output.md
  - test-design/output.md
  - delegation/output.md (if delegation ran)
  - execution/run-report.md and execution/evidence-index.md (if execution ran)
  - failure-analysis/* (if failure analysis ran)
- The project adapter at `projects/<project-name>/project.yaml`
- Any clarification answers that were provided

If required artifacts are missing, the review treats their absence as a finding and proceeds with what is available.

## Process

### 1. Discoverability review

Examine the discovery report:
- Did discovery inspect the project adapter and story intake?
- Are technology stack, application architecture, API architecture, database, authentication, CI/CD, environments, test coverage, test utilities, and coding conventions covered?
- Are unknowns explicitly marked?
- Is there any invented project-specific information?

### 2. Analysis and grill review

Examine the analysis and grill outputs:
- Does the analysis correctly derive functional scenarios from the acceptance criteria?
- Are negative scenarios, edge cases, integration risks, data risks, and regression risks identified?
- Is missing information flagged?
- Does the grill identify ambiguities, missing requirements, negative scenarios, edge cases, integration risks, regression risks?
- Are clarification questions generated and tied to specific gaps?
- Is the confirmed/unconfirmed separation clear?
- Are there any invented requirements, business rules, or expected outcomes?

### 3. Specification review

Examine the specification:
- Does every coverage area trace to a requirement, acceptance criterion, project adapter value, or shared-state artifact?
- Is the confirmed/assumption/unknown separation explicit?
- Are required test data and environment dependencies stated concretely?
- Does the specification avoid silently assuming answers to open clarification questions?
- Are expected outcomes invented or grounded?

### 4. Test-design review

Examine the test design:
- Does every scenario trace to a specification item?
- Does every scenario have an assigned test level with rationale?
- Were lower test levels preferred where valid?
- Is automation candidacy marked per scenario?
- Are manual-validation scenarios called out?
- Are scenarios blocked on missing data or environment identified?
- Are out-of-scope items stated as out of scope?
- Are there any invented selectors, endpoints, schemas, credentials, or data values?
- Are there weak or duplicate scenarios?
- Are there incorrect test levels?

### 5. Implementation/execution review

If execution ran, examine:
- Did execution run only implemented tests?
- Did execution use only declared environments?
- Were safety gates respected?
- Was evidence collected and indexed?
- Were failures honestly reported?
- Were any results invented?

### 6. Missing coverage

Identify coverage gaps:
- Requirements or acceptance criteria without coverage.
- Risks without corresponding test coverage.
- Integration points without validation.
- Negative or edge cases without coverage.
- Business rules without enforcement verification.

### 7. Unsupported assumptions audit

List every assumption found in the shared state:
- Flag assumptions not supported by the project adapter or story file.
- Flag assumptions that blur the line between confirmed and unconfirmed.
- Flag assumptions that should be clarified before execution.

### 8. Residual risks

Identify risks that remain after the workflow:
- Risks from the risk analysis that were not resolved.
- New risks identified during review.
- Risks that require human follow-up.

### 9. Overall judgment

Produce an overall judgment:
- Whether the QA workflow produced satisfactory, thorough, and honest outputs.
- Whether the coverage is adequate for the stated requirement.
- Whether human follow-up is required before execution.
- Recommended actions with priority.

## Rules

- Follow AGENTS.md.
- Be independent — do not rubber-stamp earlier stages.
- Every finding must be tied to a specific artifact, requirement item, or project-adapter value.
- Do not invent findings. If something looks suspicious, state why and what would resolve it.
- Missing coverage is stated relative to the requirement and specification.
- The overall judgment must follow from the findings.
- Keep the methodology company-independent.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured review report containing:

1. Discovery review
2. Analysis and grill review
3. Specification review
4. Test-design review
5. Implementation/execution review (if applicable)
6. Missing coverage
7. Unsupported assumptions audit
8. Weak or duplicate scenarios
9. Incorrect test levels
10. Residual risks
11. Overall review result
12. Recommended actions

Also produce:
- `review/coverage-gap.md` — coverage gaps identified
- `review/assumption-audit.md` — assumptions flagged
- `review/risks.md` — residual risks
- `review/unknowns.md` — unknowns from review
- `review/assumptions.md` — assumptions from review

## Quality Checks

Before finalizing, verify:
- The review is independent and critical.
- Every finding is tied to a specific artifact or requirement.
- Missing coverage is stated relative to the requirement and specification.
- Unsupported assumptions are clearly flagged.
- The overall judgment follows from the findings.
- No company-specific information appears that is not from the project adapter or shared state.
- The review does not invent findings or expected outcomes.
