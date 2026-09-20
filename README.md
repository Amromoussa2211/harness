# QA Agent Harness

A reusable, project-agnostic QA automation orchestration framework.

Drives a 14-stage workflow from a user story to a final QA report.

The stages are: story intake, discovery, analysis, grill, risk, architecture, specification, test design, delegation, execution, failure analysis, review, evidence, and final report.

Company-specific information belongs in `projects/<project-name>/`. The framework stays generic.

---

## What This Framework Does

The QA Agent Harness is an **orchestration layer** — it sits above your existing automation and drives the full QA process around it. It does NOT replace Playwright, Cypress, pytest, or any test framework you already use.

**The harness:**

- Reads your user story and acceptance criteria
- Discovers your target project's technology stack, existing tests, config, and environment
- Analyzes your story to derive test scenarios (functional, negative, edge cases)
- Identifies ambiguities, risks, and gaps
- Dynamically selects skills (Playwright, API, etc.) based on your story and target capabilities
- Delegates scenarios to specialist agents
- Runs tests via your existing automation (e.g., `npx playwright test`)
- Collects results, classifies failures, reviews coverage
- Produces a final QA report

**The harness does NOT:**

- Rewrite or move your existing test specs
- Auto-generate new test files into your target project (not yet built — see "What's Missing")
- Install dependencies into your target project
- Modify your target project's source code

---

## How It Works With an External Playwright Repo

If you have a separate repository with Playwright specs (1 or 2 files, or many), the harness works with it as an external target project. Your Playwright specs stay where they are.

**Your setup:**

```
qa-agent-harness/          # This framework (orchestration)
target-playwright-repo/    # Your separate repo with Playwright specs
```

**Step 1 — Configure your project:**

Create `projects/my-project/project.yaml`:

```yaml
project:
  name: my-project
  description: My application

application:
  web: true
  api: false

automation:
  framework: playwright
  language: javascript

target_repository:
  path: ../target-playwright-repo
  ci_workspace: false

safety:
  production_execution: false
  real_payments: false
  destructive_database_operations: false
```

The `target_repository.path` points to your separate Playwright repo (relative to this framework's location).

**Step 2 — Write a story:**

Create `projects/my-project/stories/STORY-001.md`:

```markdown
# STORY-001

## User Story

As a user, I want to log in with my email and password, so that I can access my account.

## Acceptance Criteria

### AC1 — Successful Login
Given a registered user with valid email and valid password
When the user performs the login action
Then the user is redirected to the Dashboard
```

**Step 3 — Run the framework:**

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

Run repeatedly — each invocation advances one stage.

**What happens with your existing Playwright specs:**

| Stage | What the harness does with your 1-2 specs |
|-------|------------------------------------------|
| **Discovery** | Scans your target repo. Finds `package.json`, `playwright.config.js`, your spec files, test directory, test command (`npx playwright test`), base URL, env var names. Reports: "Playwright detected, N spec files found." |
| **Analysis → Test Design** | Reads your story, derives test scenarios from it. Compares against what your existing specs cover. Reports gaps: "your specs cover login flow, but the story requires additional negative cases." |
| **Delegation** | Dynamic skill selection picks Playwright. PlaywrightSpecialist is assigned. |
| **Execution** | PlaywrightSpecialist runs `npx playwright test` in your target repo (if your specs are relevant to the story). Reports results. If your specs don't cover the story, reports: "existing specs do not cover story ACs — additional tests needed." |
| **Final Report** | Tells you what was tested, what passed/failed, what's covered by your existing specs, what's missing. |

**The harness never touches your spec files.** It discovers them, runs them if relevant, and reports on coverage gaps.

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

If you have an external target project (Playwright repo, API service, etc.), set `target_repository.path`. If you don't, leave it out — the framework runs in analysis/design mode without execution.

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

### AC2 — <Name>
Given <precondition>
When <action>
Then <outcome>
```

A story needs at minimum: a title (`# STORY-xxx`), a User Story section, and at least one Acceptance Criterion.

### 5. Run the Framework

```bash
python3 qa-run projects/my-project/stories/STORY-001.md
```

Run repeatedly — each invocation advances exactly one stage. Stop when you see:

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
| 2 | Discovery | Project adapter inspects target repo: language, frameworks, config, env, test data, existing specs |
| 3 | Analysis | Derive functional scenarios, negative cases, edge cases, integration risks from ACs |
| 4 | Grill | Identify ambiguities, missing requirements, clarification questions |
| 5 | Risk | Categorize and prioritize risks from grill + analysis + discovery |
| 6 | Architecture | Test strategy, pyramid, automation approach, test data and environment strategy |
| 7 | Specification | Test coverage, validation expectations, required test data, environment dependencies |
| 8 | Test Design | Concrete test scenarios with IDs, levels, automation candidacy, data requirements |
| 9 | Delegation | Dynamic skill selection, assign scenarios to specialist agents, check safety gates |
| 10 | Execution | Execute tests via specialist agents (runs your existing `npx playwright test` etc.), collect results, capture evidence |
| 11 | Failure Analysis | Classify failures: product defect, automation defect, environment, dependency, data, network, timeout |
| 12 | Review | Independent QA review: coverage gaps, unsupported assumptions, weak scenarios, residual risks |
| 13 | Evidence | Consolidate screenshots, traces, logs, API responses, test results |
| 14 | Final Report | Comprehensive report: findings, risks, recommendations |

---

## Generated Artifacts

All artifacts live in `shared-state/<STORY-ID>/` (git-ignored, recreated each run):

```
shared-state/STORY-001/
├── stage-status.json       # Stage tracking
├── story-intake.md         # Stage 1
├── discovery/output.md     # Stage 2 — target repo discovery report
├── analysis/output.md      # Stage 3
├── grill/output.md         # Stage 4
├── risk/output.md          # Stage 5
├── architecture/output.md  # Stage 6
├── specification/output.md # Stage 7
├── test-design/output.md   # Stage 8 — derived test scenarios
├── delegation/output.md    # Stage 9 — skill selection report + specialist assignments
├── execution/              # Stage 10
│   ├── run-report.md
│   └── evidence-index.md
├── failure-analysis/       # Stage 11
├── review/                 # Stage 12
├── evidence/               # Stage 13
└── final-report.md         # Stage 14 — the final QA report
```

The most important artifacts:
- `discovery/output.md` — what the harness found in your target repo
- `delegation/output.md` — which skills were selected and why
- `execution/run-report.md` — test results
- `final-report.md` — complete QA report

---

## Dynamic Skill Selection

Stage 9 (Delegation) automatically selects skills based on:

1. **Story content** — keywords in the user story, ACs, business rules
2. **Target capability map** — detected capabilities from the target repository (via discovery)
3. **Project configuration** — enabled flags in project.yaml

**16 skills available:** Playwright, API, Webhook, Database, Authentication, Test Data, Contract Testing, Execution, Failure Analysis, Evidence, Security, Accessibility, Visual Testing, Mocking, Performance, CI/CD

**Example selections:**
- UI login story → Playwright, Authentication, Test Data, Execution, Evidence, Failure Analysis
- REST API story → API, Test Data, Execution, Evidence, Failure Analysis
- Payment webhook → API, Webhook, Database, Authentication, Execution, Evidence, Failure Analysis

---

## Target Project Integration

When `target_repository.path` is configured, the project adapter discovers and inspects the external target repository.

```yaml
target_repository:
  path: ../my-target-repo
  ci_workspace: false
```

**What it discovers:**

- Language, runtime, package manager (from `package.json`, `requirements.txt`, `pom.xml`, etc.)
- Test frameworks: Playwright, Cypress, Selenium, Appium, pytest, JUnit, etc.
- Test directories and existing test files (your Playwright specs, pytest tests, etc.)
- Configuration: `playwright.config.*` (base URL, env var names via regex), `.env.example`, CI workflows
- Test data locations: `test-data/`, `fixtures/`, seed scripts
- CI configuration: `.github/workflows/`, `.gitlab-ci.yml`, etc.
- Dockerfiles, OpenAPI specs, webhook indicators

**What it does NOT do:**

- Never exposes secret values (env vars reported by name only, never values)
- Never installs dependencies automatically (no `npm install`, no `pip install`)
- Never modifies target project source code
- Blocks destructive commands (rm -rf, docker rm, git reset --hard)
- Blocks approval-required commands (git push, kubectl apply, terraform apply)

**Execution with existing specs:**

When the PlaywrightSpecialist runs, it executes your target project's test command (`npx playwright test` by default, or whatever is configured in `package.json` scripts). It captures the JSON reporter output and normalizes the results. If your existing specs cover the story's acceptance criteria, they run and results are reported. If they don't, the report flags the coverage gap.

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

When `production_execution: true`, the framework warns before executing against production environments. The other gates block real payment transactions and destructive database operations.

---

## Project Structure

```
/
├── qa-run                          # Main runtime — 14-stage workflow (run this)
├── workflow-stages.json            # Stage order definition
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
│   │   ├── project.yaml            # Demo project config (has target_repository)
│   │   └── stories/                # (demo stories removed — add your own)
│   └── template/
│       └── project.yaml            # Clean reusable template (start from this)
├── shared-state/                   # Runtime artifacts (git-ignored)
│   └── <STORY-ID>/
├── requirements.txt                # Python dependencies (PyYAML)
├── .gitignore
├── INTEGRATION_REPORT.md           # Target project integration architecture
├── STATUS_REPORT.md                # Current state, completed items, missing items
└── README.md                       # This file
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `"story path must be under projects/"` | Story path must start with `projects/<project-name>/stories/<story-id>.md` |
| `"Stage X is already in progress"` | Resume with the same command, or restart: `rm -rf shared-state/STORY-XXX` |
| `"All stages completed or skipped"` | Workflow is done; read `shared-state/<STORY-ID>/final-report.md` |
| **Execution blocked / no tests run** | Ensure `target_repository.path` is set in project.yaml. Ensure target repo has `node_modules` (run `npm install` there). Ensure a server is running if tests need one. Check `delegation/output.md` for specialist readiness. |
| **Playwright browser not available** | The PlaywrightSpecialist detects Playwright config and runs `npx playwright test`. If the browser can't be installed in this environment, the execution stage reports blocked. Run on a supported OS or use API mocking. |
| **No existing specs in target repo** | The harness still runs the full workflow (discovery, analysis, test design, delegation). Execution stage reports "no existing tests to run — additional test implementation needed." |
| **Skill selection not appearing** | Check `delegation/output.md` section "Dynamic Skill Selection". Ensure story content matches skill triggers and target capability map is populated (target_repository must be configured). |

---

## Dependencies

- Python 3.x
- PyYAML >= 6.0.1

All other imports are Python standard library.

---

## What's Missing (Not Yet Built)

The framework is functional for the analysis, design, delegation, and reporting stages. These items are not yet implemented:

1. **Test Implementation stage** — the framework derives test scenarios but does not yet write actual Playwright spec files, API test scripts, or other test code into your target project. Execution runs your *existing* specs; it does not create new ones.

2. **Additional specialist agents** — only Playwright and API specialists are implemented. The remaining 14 skills (Webhook, Database, Authentication, Test Data, Contract Testing, Security, Accessibility, Visual Testing, Mocking, Performance, CI/CD, etc.) have skill definitions but no execution agents.

3. **Remote/CI workspace support** — the `target_repository.ci_workspace` flag exists but workspace provisioning (git clone, env injection, container execution) is not implemented.

4. **Live target server** — if your tests need a running server/API, you must start it yourself before running the framework. The framework does not start target services.

For details, see `STATUS_REPORT.md`.

---

## Architecture Documents

- `INTEGRATION_REPORT.md` — target project integration architecture (how discovery, capability detection, and safe execution work)
- `STATUS_REPORT.md` — current state, what's done, what's missing
- `adapters/project_adapter.py` — target discovery implementation
- `adapters/skill_selector.py` — skill selection implementation
- `adapters/specialists.py` — Playwright and API specialist implementations
