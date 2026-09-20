# QA Agent Harness

## Mission

This repository contains a reusable, company-independent QA Agent Harness.

The harness must be portable across different companies and projects.

The core QA methodology must remain independent from project-specific data.

## Architecture

The system is composed of:

- QA Orchestrator
- Specialized QA Agents
- Reusable QA Skills
- Project Adapters
- Shared State
- QA Evidence and Reports

## Core Principle

Never hardcode company-specific information into the core framework.

Company-specific information belongs inside:

projects/<project-name>/

Examples:

- URLs
- credentials
- API endpoints
- database configuration
- selectors
- business rules
- test data
- CI/CD configuration
- framework-specific conventions

## QA Workflow

The default workflow is:

1. Project Discovery
2. Requirement Understanding
3. QA Grill
4. Risk Analysis
5. QA Specification
6. Test Design
7. Test Implementation
8. Test Execution
9. Failure Analysis
10. Independent QA Review
11. Evidence Generation

## Safety

Never:

- invent credentials
- invent API contracts
- invent database schemas
- invent selectors
- execute destructive production operations
- create real financial transactions without explicit authorization
- modify production data without explicit authorization

## Engineering Principles

Prefer:

- existing project patterns
- existing fixtures
- existing utilities
- reusable abstractions
- deterministic test data
- stable selectors
- API mocking where appropriate
- clear evidence
- minimal changes
- readable automation

Do not over-engineer.

Do not modify existing project architecture unless explicitly required.

## Agent Behavior

Agents must:

- inspect before modifying
- explain assumptions
- preserve project conventions
- produce artifacts
- validate their work
- report uncertainty
- stop and ask for clarification when critical information is missing
