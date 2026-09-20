# How To Use Hermes QA Agent Harness

## Overview

Hermes is a reusable, company-independent QA Agent Harness that drives a 14-stage workflow from a user story to a final QA report. It is designed to be project-agnostic — never hardcoding company-specific information.

**Key principle:** Company-specific information belongs in `projects/<project-name>/`. The harness stays generic.

---

## Quick Start

### 1. Add a Project

Create a project directory under `projects/`:

```bash
mkdir -p projects/my-project/stories
```

### 2. Configure the Project Adapter

Create `projects/my-project/project.yaml`:

```yaml
project:
  name: my-project
  description: My application description

application:
  web: true
  api: true
  mobile: false

automation:
  framework: playwright
  language: javascript

api:
  rest: true
  graphql: false
  webhooks: false

database:
  enabled: false
  type: none

target_repository:
  path: ../my-target-repo
  ci_workspace: false

environments:
  dev: true
  staging: false
  production: false

safety:
  production_execution: false
  real_payments: false
  destructive_database_operations: false
```

**Required fields:** `project.name`, `application`, `automation`, `safety`

**Optional fields:** `target_repository` (for external target project discovery), `api`, `database`, `environments`, `performance`, `security`, `accessibility`, `visual`, `events`, `webhooks`, `ci`, `test_data`, `secrets`

### 3. Provide a Story

Create a story markdown file: `projects/my-project/stories/STORY-001.md`

```markdown
# STORY-001

## User Story

As a <role>,
I want <feature>,
so that <benefit>.

## Acceptance Criteria

### AC1 — <Name>
Given <precondition>
When <action>
Then <outcome>

### AC2 — <Name>
Given <precondition>
When <action>
Then <outcome>

## Business Rules

- <rule 1>
- <rule 2>

## Notes

<context>
```

### 4. Run Hermes

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

Run repeatedly until all stages complete:

```bash
# First run: Story Intake
python3 qa-run projects/my-project/stories/STORY-001.md

# Subsequent runs: advance one stage at a time
python3 qa-run projects/my-project/stories/STORY-001.md
python3 qa-run projects/my-project/stories/STORY-001.md
# ... repeat until:
# "All stages completed or skipped. Overall: completed"
```

Each invocation advances exactly one stage. The stage-status.json tracks progress.

### 5. Review Generated Artifacts

All artifacts are stored in `shared-state/<STORY-ID>/`:

```
shared-state/STORY-001/
├── stage-status.json       # Stage status tracking
├── story-intake.md         # Stage 1: Story intake
├── discovery/              # Stage 2: Project discovery
│   └── output.md
├── analysis/               # Stage 3: Requirement analysis
│   └── output.md
├── grill/                  # Stage 4: QA grill
│   ├── output.md
│   └── questions.md
├── risk/                   # Stage 5: Risk analysis
│   └── output.md
├── architecture/           # Stage 6: Test architecture
│   └── output.md
├── specification/          # Stage 7: Test specification
│   └── output.md
├── test-design/            # Stage 8: Test design
│   └── output.md
├── delegation/             # Stage 9: Specialist delegation
│   └── output.md
├── execution/              # Stage 10: Test execution
│   ├── run-report.md
│   └── evidence-index.md
├── failure-analysis/       # Stage 11: Failure analysis
│   ├── classifications.md
│   ├── failure-details.md
│   ├── unknowns.md
│   └── assumptions.md
├── review/                 # Stage 12: Independent QA review
│   ├── review-report.md
│   ├── coverage-gap.md
│   ├── assumption-audit.md
│   ├── risks.md
│   ├── unknowns.md
│   └── assumptions.md
├── evidence/               # Stage 13: Evidence collection
│   └── consolidated.md
└── final-report.md         # Stage 14: Final report
```

### 6. Read the Final Report

```bash
cat shared-state/STORY-001/final-report.md
```

The final report contains:
- Story and project summary
- Scope covered and not covered
- Requirement coverage analysis
- Test results summary
- Failure summary and root causes
- Evidence summary
- Review result
- Residual risks, assumptions, and unknowns
- Recommended actions

---

## Workflow Stages

| # | Stage | Description |
|---|-------|-------------|
| 1 | Story Intake | Parse story file, extract title, user story, ACs, business rules, notes |
| 2 | Discovery | Inspect project adapter and target repository for capabilities, environments, test frameworks |
| 3 | Analysis | Derive functional scenarios, negative scenarios, edge cases, integration risks from ACs |
| 4 | Grill | Identify ambiguities, missing requirements, negative scenarios, edge cases, clarification questions |
| 5 | Risk | Categorize and prioritize risks from grill + analysis + discovery |
| 6 | Architecture | Design test strategy, pyramid, automation approach, test data strategy, environment strategy |
| 7 | Specification | Define test coverage, validation expectations, required test data, environment dependencies |
| 8 | Test Design | Create concrete test scenarios with IDs, levels, automation candidacy, data requirements |
| 9 | Delegation | Dynamically select skills, assign scenarios to specialist agents, check safety gates |
| 10 | Execution | Execute tests via specialist agents, collect results, capture evidence |
| 11 | Failure Analysis | Classify failures: product defect, automation defect, environment, dependency, data, network, timeout |
| 12 | Review | Independent QA review: coverage gaps, unsupported assumptions, weak scenarios, residual risks |
| 13 | Evidence | Consolidate all evidence: screenshots, traces, logs, API responses, test results |
| 14 | Final Report | Comprehensive report with all findings, risks, recommendations |

---

## Dynamic Skill Selection

The delegation stage (Stage 9) automatically selects skills based on:

1. **Story content** — keywords in the user story, ACs, business rules
2. **Target capability map** — detected capabilities from target repository (via project adapter)
3. **Project configuration** — enabled flags in project.yaml

**Example selections:**

| Story Type | Selected Skills |
|------------|----------------|
| UI Login story | Playwright, Authentication, Test Data, Execution, Evidence, Failure Analysis |
| REST API story | API, Test Data, Execution, Evidence, Failure Analysis |
| Payment webhook story | API, Webhook, Database, Authentication, Execution, Evidence, Failure Analysis |
| Full-stack E2E | Playwright, API, Database, Authentication, Test Data, Contract Testing, Execution, Evidence, Failure Analysis |

**Skills available (16 total):**
- Playwright, API, Webhook, Database, Authentication, Test Data, Contract Testing, Execution, Failure Analysis, Evidence, Security, Accessibility, Visual Testing, Mocking, Performance, CI/CD

---

## Target Project Integration

When a `target_repository.path` is configured in `project.yaml`, Hermes can discover and interact with an external target project:

```yaml
target_repository:
  path: ../my-target-repo
  ci_workspace: false
```

**What Hermes discovers:**
- Language and package manager (from package.json, requirements.txt, pom.xml, etc.)
- Test frameworks (Playwright, Cypress, Selenium, Appium, pytest, JUnit)
- Test directories and existing test files
- Environment configuration (base URL from playwright.config.js, .env.example variables)
- Test data locations (test-data/, fixtures/, seed scripts)
- CI configuration (.github/workflows, .gitlab-ci.yml, etc.)
- Webhook indicators, Dockerfiles, OpenAPI specs

**Safety boundaries:**
- Never exposes secret values (environment variables reported by name only)
- Command classification: SAFE / REQUIRES APPROVAL / DESTRUCTIVE / UNKNOWN
- Destructive commands (rm -rf, docker rm, git reset --hard) are blocked
- Approval-required commands (git push, kubectl apply, terraform apply) are blocked
- Never installs dependencies automatically
- Never modifies target project source code

---

## Resume and Restart

**Resume:** Run the same command again. Hermes picks up from the first incomplete stage.

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

**Restart:** Delete the shared-state directory for the story to start over.

```bash
rm -rf shared-state/STORY-001
python3 qa-run projects/my-project/stories/STORY-001.md
```

---

## Safety Gates

Project.yaml safety configuration:

```yaml
safety:
  production_execution: false   # Block production execution
  real_payments: false          # Block real payment transactions
  destructive_database_operations: false  # Block destructive DB ops
```

When `production_execution: true`, Hermes will warn before executing against production environments.

---

## Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Current dependencies:
- PyYAML >= 6.0.1 (for parsing project.yaml)

All other imports (json, datetime, pathlib, subprocess, re, urllib) are Python standard library.

---

## Project Structure

```
qa-agent-harness/
├── qa-run                      # Main runtime entry point (14-stage workflow)
├── workflow-stages.json        # Stage order definition
├── orchestrator/
│   └── workflow.md             # Workflow documentation
├── adapters/
│   ├── project_adapter.py      # Target project discovery & integration
│   ├── skill_selector.py       # Dynamic skill selection engine
│   └── specialists.py          # Playwright & API specialist agents
├── agents/                     # Agent specifications (11 agents)
│   ├── analyst/
│   ├── api/
│   ├── architect/
│   ├── data/
│   ├── discovery/
│   ├── execution/
│   ├── failure-analysis/
│   ├── review/
│   ├── risk/
│   ├── spec/
│   └── web/
├── skills/                     # Reusable skill definitions (16+ skills)
│   ├── playwright/
│   ├── api/
│   ├── webhook/
│   ├── database/
│   ├── authentication/
│   ├── test-data/
│   ├── contract-testing/
│   ├── execution/
│   ├── failure-analysis/
│   ├── evidence/
│   ├── security/
│   ├── accessibility/
│   ├── visual-testing/
│   ├── mocking/
│   ├── performance/
│   └── ci-cd/
├── projects/
│   ├── demo/
│   │   ├── project.yaml
│   │   └── stories/
│   └── template/
│       └── project.yaml        # Clean reusable template
├── shared-state/               # Runtime artifacts (created per story)
│   └── <STORY-ID>/
├── requirements.txt            # Python dependencies
└── HOW_TO_USE.md               # This file
```

---

## Troubleshooting

**"Error: story path must be under projects/"**
- Ensure your story path starts with `projects/<project-name>/stories/<story-id>.md`

**"Stage 'X' is already in progress"**
- Run resume: `python3 qa-run projects/.../stories/STORY-XXX.md`
- Or restart: `rm -rf shared-state/STORY-XXX`

**"All stages completed or skipped"**
- The workflow is done. Check `shared-state/<STORY-ID>/final-report.md`

**Execution is blocked**
- Ensure a target repository is configured in project.yaml
- Ensure the target repository has test infrastructure (node_modules for Playwright, server for API)
- Ensure specialist agents can execute (check delegation/output.md for agent readiness)

**Dynamic skill selection not appearing**
- Ensure `SKILL_SELECTOR_AVAILABLE` is True (skill_selector.py imports correctly)
- Ensure the story has content that matches skill triggers
- Check delegation/output.md section "## 1. Dynamic Skill Selection"

---

## Example: End-to-End Run

```bash
# 1. Create project
mkdir -p projects/demo/stories

# 2. Configure project adapter
cat > projects/demo/project.yaml << 'EOF'
project:
  name: demo
  description: Demo project for QA Harness validation

application:
  web: true
  api: true
  mobile: false

automation:
  framework: playwright
  language: javascript

api:
  rest: true
  graphql: false
  webhooks: false

database:
  enabled: false
  type: none

target_repository:
  path: ../demo-target-project

environments:
  dev: true
  staging: false
  production: false

safety:
  production_execution: false
  real_payments: false
  destructive_database_operations: false
EOF

# 3. Create story
cat > projects/demo/stories/STORY-001.md << 'EOF'
# STORY-001

## User Story

As a user, I want to log in with my email and password, so that I can access my account.

## Acceptance Criteria

### AC1 — Successful Login
Given a registered user with valid email and valid password
When the user performs the login action
Then the user is redirected to the Dashboard

### AC2 — Invalid Password
Given a registered user with valid email
When the user provides an invalid password
Then the action is rejected
EOF

# 4. Run Hermes (repeat until complete)
python3 qa-run projects/demo/stories/STORY-001.md
python3 qa-run projects/demo/stories/STORY-001.md
# ... repeat

# 5. Read the report
cat shared-state/STORY-001/final-report.md
```

---

*For detailed information about the architecture, see INTEGRATION_REPORT.md and the adapter source files.*
