---
name: test-architecture
description: Designs the most appropriate testing strategy — test levels, test pyramid, automation strategy, test data strategy, environment strategy, mocking strategy, CI strategy, and reporting strategy — for a QA story.
version: 0.1.0
---

# Test Architecture

## Purpose

Design the most appropriate testing strategy for a software feature. Test architecture determines test levels, test types, automation approach, test data strategy, environment requirements, mocking strategy, CI strategy, and reporting strategy. It prefers the lowest appropriate test layer and does not use UI automation when API or integration testing provides better coverage.

## Inputs

- The QA Grill output for the story under review.
- The Requirement Analysis output for the same story.
- The Risk Analysis output for the same story.
- The Project Discovery report for the project.
- The project adapter at `projects/<project-name>/project.yaml`.
- Any project-specific information under `projects/<project-name>/` that defines the application type, API types, database usage, automation framework and language hints, environments, and safety constraints.

If the grill output, analysis output, risk output, or discovery report is missing, the architecture stage must say so and must not silently proceed as if they were complete.

## Process

### 1. Read all prior-stage outputs

Read the grill output, analysis output, risk output, discovery report, and project adapter. Understand the requirement, acceptance criteria, ambiguities, risks, and project configuration.

### 2. Determine test strategy

Define the primary test level and scope. The scope should cover the acceptance criteria plus the negative and edge cases identified in the grill and analysis.

### 3. Design the test pyramid

Allocate test coverage across layers:

- Unit layer: credential validation, session creation, error message generation, business rule enforcement.
- Integration layer: API endpoints, database interactions, external service integrations.
- E2E layer: full user journeys via UI automation.

Prefer the lowest appropriate layer. Use API or component-level validation instead of UI when the same risk can be covered there and the project adapter supports that layer.

### 4. Define automation strategy

Based on the project adapter's declared automation framework and language:

- Define the test organization (one file per acceptance criterion, shared fixtures, etc.).
- Define the approach (Page Object Model for UI, API client for API, fixtures for test data).
- Note any framework-specific conventions declared in the project adapter.

### 5. Define test data strategy

Identify the test data required:

- Pre-seeded entities (e.g., registered users, products, orders).
- Invalid or boundary data samples.
- Stable, deterministic data.
- Data that must be isolated or cleaned up between tests.

### 6. Define environment strategy

Based on the project adapter's environment declarations:

- Select the target environment (dev, staging, or production as enabled).
- Define environment isolation and cleanup requirements.
- If no environment is enabled, note this as a blocker.

### 7. Define mocking strategy

Identify external dependencies that should be mocked or stubbed:

- External services, SSO, email verification, third-party identity providers.
- API responses for downstream services.
- Database state where appropriate.

### 8. Define CI strategy

Based on the project adapter's CI provider declaration:

- Define run triggers (pull requests, merges to main).
- Define reporting integration.

### 9. Define reporting strategy

Define what test results and evidence should be reported:

- Pass/fail for each acceptance criterion and scenario.
- Evidence for failures (screenshots, API logs, console logs).
- Coverage metrics where applicable.

### 10. Identify architecture risks

Note any risks that affect the architecture itself:

- No environment available.
- No application under test.
- Login mechanism or integration point unknown.

### 11. Produce implementation plan

Produce a step-by-step implementation plan that is consistent with the specialist agents that exist. Each step should note whether it is blocked pending human clarification, project configuration, or agent availability.

## Rules

- Follow AGENTS.md.
- Never invent a specific application beyond what the project adapter declares.
- Do not assume a specific UI framework, backend framework, or database engine.
- Prefer the lowest appropriate test layer.
- Read the project adapter before acting.
- Read relevant shared-state artifacts before acting.
- Do not modify application code.
- Do not perform destructive production operations.
- Report assumptions explicitly.
- Mark unknown information as unknown.
- Keep the methodology company-independent. The same test layers and strategy sections apply to every project; only the project adapter contents differ.
- Use project-specific information only from `projects/<project-name>/`.

## Output

Produce a structured Test Architecture containing:

1. Test strategy
2. Test pyramid
3. Automation strategy
4. Test data strategy
5. Environment strategy
6. Mocking strategy
7. CI strategy
8. Reporting strategy
9. Risks
10. Implementation plan

The environment strategy must note when no environments are enabled and must not assume an environment exists.

## Quality Checks

Before finalizing, verify:

- The architecture is consistent with the project adapter's declared application type, API types, database usage, and environments.
- The architecture prefers the lowest appropriate test layer.
- The architecture does not assume a specific application beyond what the project adapter declares.
- The implementation plan is consistent with the specialist agents that exist.
- Environment dependencies are stated concretely.
- Risks are tied to specific findings from prior stages.
