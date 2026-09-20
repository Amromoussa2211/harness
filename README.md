# QA Agent Harness

A reusable, project-agnostic QA automation orchestration framework.

Drives a 14-stage workflow from a user story to a final QA report.

The stages are: story intake, discovery, analysis, grill, risk, architecture, specification, test design, delegation, execution, failure analysis, review, evidence, and final report.

Company-specific information belongs in `projects/<project-name>/`. The framework stays generic.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Project

```bash
mkdir -p projects/my-project/stories
```

### 3. Configure the Project

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

**Required:** `project.name`, `application`, `automation`, `safety`  
**Optional:** `target_repository`, `api`, `database`, `environments`, `performance`, `security`, `accessibility`, `visual`, `events`, `webhooks`, `ci`, `test_data`, `secrets`

### 4. Write a Story

Create `projects/my-project/stories/STORY-001.md`:

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
```

### 5. Run the Framework

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

Run repeatedly — each invocation advances one stage. Stop when you see:

```
All stages completed or skipped. Overall: completed
```

### 6. Read the Report

```bash
cat shared-state/STORY-001/final-report.md
```

---

## Workflow Stages

| # | Stage | Description |
|---|-------|-------------|
| 1 | Story Intake | Parse story file — title, user story, ACs, business rules, notes |
| 2 | Discovery | Project adapter inspects target repo: language, frameworks, config, env, test data |
| 3 | Analysis | Derive functional scenarios, negative cases, edge cases, integration risks from ACs |
| 4 | Grill | Identify ambiguities, missing requirements, clarification questions |
| 5 | Risk | Categorize and prioritize risks from grill + analysis + discovery |
| 6 | Architecture | Test strategy, pyramid, automation approach, test data and environment strategy |
| 7 | Specification | Test coverage, validation expectations, required test data, environment dependencies |
| 8 | Test Design | Concrete test scenarios with IDs, levels, automation candidacy, data requirements |
| 9 | Delegation | Dynamic skill selection, assign scenarios to specialist agents, check safety gates |
| 10 | Execution | Execute tests via specialist agents, collect results, capture evidence |
| 11 | Failure Analysis | Classify failures: product defect, automation defect, environment, dependency, data, network, timeout |
| 12 | Review | Independent QA review: coverage gaps, unsupported assumptions, weak scenarios, residual risks |
| 13 | Evidence | Consolidate screenshots, traces, logs, API responses, test results |
| 14 | Final Report | Comprehensive report: findings, risks, recommendations |

---

## Generated Artifacts

All artifacts live in `shared-state/<STORY-ID>/`:

```
shared-state/STORY-001/
├── stage-status.json       # Stage tracking
├── story-intake.md         # Stage 1
├── discovery/output.md     # Stage 2
├── analysis/output.md      # Stage 3
├── grill/output.md         # Stage 4
├── risk/output.md          # Stage 5
├── architecture/output.md  # Stage 6
├── specification/output.md # Stage 7
├── test-design/output.md   # Stage 8
├── delegation/output.md    # Stage 9 — includes skill-selection report
├── execution/              # Stage 10
│   ├── run-report.md
│   └── evidence-index.md
├── failure-analysis/       # Stage 11
├── review/                 # Stage 12
├── evidence/               # Stage 13
└── final-report.md         # Stage 14
```

---

## Dynamic Skill Selection

Stage 9 (Delegation) automatically selects skills based on:

1. **Story content** — keywords in the user story, ACs, business rules
2. **Target capability map** — detected capabilities from the target repository
3. **Project configuration** — enabled flags in project.yaml

**16 skills available:** Playwright, API, Webhook, Database, Authentication, Test Data, Contract Testing, Execution, Failure Analysis, Evidence, Security, Accessibility, Visual Testing, Mocking, Performance, CI/CD

**Example — login story selects:** Playwright, Authentication, Test Data, Execution, Evidence, Failure Analysis

---

## Target Project Integration

When `target_repository.path` is configured, the project adapter discovers and inspects the external target repository:

```yaml
target_repository:
  path: ../my-target-repo
  ci_workspace: false
```

**Discovers:** language, runtime, package manager, package.json, lock files, test frameworks (Playwright/Cypress/Selenium/Appium/pytest/JUnit), test directories, fixtures, CI config, Dockerfiles, OpenAPI specs, playwright.config.* (base URL, env var names), .env.example, test data locations.

**Safety:** secret values are never exposed (env vars reported by name only). Destructive and approval-required commands are blocked. Dependencies are never installed automatically. Target source code is never modified.

---

## Resume and Restart

**Resume** — run the same command again; picks up from the first incomplete stage:

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

**Restart** — delete the story's shared-state directory:

```bash
rm -rf shared-state/STORY-001
python3 qa-run projects/my-project/stories/STORY-001.md
```

---

## Safety Gates

```yaml
safety:
  production_execution: false
  real_payments: false
  destructive_database_operations: false
```

When `production_execution: true`, the framework warns before executing against production environments.

---

## Project Structure

```
/
├── qa-run                          # Main runtime — 14-stage workflow
├── workflow-stages.json            # Stage order
├── orchestrator/workflow.md        # Workflow documentation
├── adapters/
│   ├── project_adapter.py          # Target project discovery & integration
│   ├── skill_selector.py           # Dynamic skill selection engine
│   └── specialists.py              # Playwright & API specialist agents
├── agents/                         # Agent specifications (11 agents)
│   ├── analyst/ AGENT.md
│   ├── api/ AGENT.md
│   ├── architect/ AGENT.md
│   ├── data/ AGENT.md
│   ├── discovery/ AGENT.md
│   ├── execution/ AGENT.md
│   ├── failure-analysis/ AGENT.md
│   ├── review/ AGENT.md
│   ├── risk/ AGENT.md
│   ├── spec/ AGENT.md
│   └── web/ AGENT.md
├── skills/                         # 16 reusable skill definitions
│   ├── playwright/ SKILL.md
│   ├── api/ SKILL.md
│   ├── webhook/ SKILL.md
│   ├── database/ SKILL.md
│   ├── authentication/ SKILL.md
│   ├── test-data/ SKILL.md
│   ├── contract-testing/ SKILL.md
│   ├── execution/ SKILL.md
│   ├── failure-analysis/ SKILL.md
│   ├── evidence/ SKILL.md
│   ├── security/ SKILL.md
│   ├── accessibility/ SKILL.md
│   ├── visual-testing/ SKILL.md
│   ├── mocking/ SKILL.md
│   ├── performance/ SKILL.md
│   ├── ci-cd/ SKILL.md
│   ├── qa-run/ SKILL.md
│   ├── qa-orchestrator/ SKILL.md
│   ├── qa-grill/ SKILL.md
│   ├── qa-spec/ SKILL.md
│   ├── qa-review/ SKILL.md
│   └── risk/ SKILL.md
├── projects/
│   ├── demo/
│   │   ├── project.yaml
│   │   └── stories/
│   └── template/
│       └── project.yaml            # Clean reusable template
├── shared-state/                   # Runtime artifacts (git-ignored)
│   └── <STORY-ID>/
├── requirements.txt                # Python dependencies (PyYAML)
├── .gitignore
└── README.md                       # This file
```

---

## Troubleshooting

**"story path must be under projects/"** — story path must start with `projects/<project-name>/stories/<story-id>.md`

**"Stage X is already in progress"** — resume with the same command, or restart by deleting `shared-state/STORY-XXX`

**"All stages completed or skipped"** — workflow is done; check `shared-state/<STORY-ID>/final-report.md`

**Execution blocked** — ensure target repository is configured in project.yaml, has test infrastructure (node_modules, server), and specialist agents are ready (check delegation/output.md)

**Skill selection not appearing** — check delegation/output.md section "Dynamic Skill Selection"; ensure story content matches skill triggers and target capability map is populated

---

## Dependencies

- Python 3.x
- PyYAML >= 6.0.1

All other imports are Python standard library.

---

## Architecture Documents

- `INTEGRATION_REPORT.md` — target project integration architecture
- `STATUS_REPORT.md` — current state, completed items, missing items
- `adapters/project_adapter.py` — target discovery implementation
- `adapters/skill_selector.py` — skill selection implementation
- `adapters/specialists.py` — specialist agent implementations
