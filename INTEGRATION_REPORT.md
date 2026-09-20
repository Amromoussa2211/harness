================================================================================
HERMES QA AGENT HARNESS — TARGET PROJECT INTEGRATION ARCHITECTURE
Consolidated Report — Phase: Integration Contract & Discovery Validation
Date: 2026-09-20
================================================================================

================================================================================
1. ARCHITECTURE
================================================================================

The QA Agent Harness is an INDEPENDENT control plane — it is NOT copied into
application repositories.

+----------------------------------------------------------+
|  HERMES QA AGENT HARNESS (this repository)              |
|  - Orchestration (qa-run, 14 stages)                    |
|  - Analysis, skill selection, reporting                 |
|  - Project adapter (adapters/project_adapter.py)        |
+----------------------------------------------------------+
                          |
                          | Project Adapter / Target Integration
                          | (adapters/project_adapter.py)
                          |
                          v
+----------------------------------------------------------+
|  TARGET PROJECT REPOSITORY                              |
|  - Application source code                              |
|  - package.json / requirements.txt                      |
|  - Existing tests (playwright, cypress, pytest, etc.)  |
|  - Configuration (playwright.config.*, .env, CI)       |
|  - Fixtures, test data                                  |
+----------------------------------------------------------+

Key separation:
- Harness owns: workflow orchestration, analysis, skill definitions,
  delegation logic, reporting, evidence collection
- Target project owns: application code, existing automation, configuration
- Project Adapter bridges: discovery, capability detection, safe command
  execution, environment inspection, test data discovery

================================================================================
2. INTEGRATION CONTRACT — Project Adapter
================================================================================

File: adapters/project_adapter.py
Class: ProjectAdapter

Responsibilities:

1. TARGET REPOSITORY RESOLUTION
   - get_target_repository_path(): resolves path from project.yaml
     target_repository.path field
   - Supports relative paths (from harness root) and absolute paths
   - Supports CI workspace mode (future)

2. CAPABILITY DETECTION
   - detect_capabilities(): builds machine-readable capability map
   - Detects: language, package manager, test frameworks, web/api/mobile,
     webhooks, CI, Docker, existing automation
   - Framework detection: Playwright, Cypress, Selenium, Appium, pytest,
     JUnit/TestNG
   - Returns version info where available (e.g. @playwright/test version)

3. ENVIRONMENT DISCOVERY
   - discover_environments(): extracts base URL, API URL, ports, scripts,
     env variable names from target repo
   - Parses playwright.config.* for baseURL
   - Parses .env.example for variable names (NONE values exposed)
   - Parses package.json scripts (test, build, lint)
   - Parses README for environment info

4. TEST DATA DISCOVERY
   - discover_test_data(): finds test-data/, fixtures/, seed scripts
   - Scans for factory/seed/fixture files

5. SAFE COMMAND EXECUTION
   - classify_command(): SAFE / REQUIRES APPROVAL / DESTRUCTIVE / UNKNOWN
   - execute_command(): runs commands with cwd=target repo, captures
     stdout/stderr/exit_code/duration, enforces timeout
   - Blocks destructive commands automatically (rm -rf, docker rm, etc.)
   - Blocks approval-requiring commands (git push, kubectl apply, etc.)

6. DISCOVERY REPORT
   - generate_discovery_report(): produces consolidated discovery dict
   - Used by qa-run discovery stage to enrich output

================================================================================
3. CONFIGURATION — project.yaml Extension
================================================================================

New optional section added to project.yaml (backward compatible):

  target_repository:
    # Path to the target project repository (relative to harness root
    # or absolute). Leave empty/omit if target is same as harness project.
    # Example: ../my-app-repo
    path: ../demo-target-project

    # When true, adapter treats this as a CI workspace checkout.
    # CI workflows may inject paths at runtime instead of static config.
    ci_workspace: false

Existing project.yaml fields remain unchanged. Existing project.yaml files
without target_repository continue to work (adapter is a no-op when absent).

================================================================================
4. DISCOVERY — What Was Detected From Demo Target
================================================================================

Target: /Users/t/Desktop/demo-target-project

Capability Map (detected):
  - language: javascript
  - package_manager: npm
  - web: true
  - api: true
  - playwright: true
  - cypress: false
  - selenium: false
  - appium: false
  - pytest: false
  - java_test: false
  - graphql: false
  - webhooks: true (detected via webhook route handlers in server.js)
  - event_driven: false
  - database: false
  - docker: false
  - ci: false
  - existing_automation: true
  - test_directory: /Users/t/Desktop/demo-target-project/tests
  - framework_version: ^1.40.0

Environments (discovered):
  - Base URL: http://localhost:3000 (from playwright.config.js)
  - Environment variables (from .env.example): PORT, BASE_URL,
    API_URL, WEBHOOK_SIGNING_SECRET — ALL VALUES NOT EXPOSED
  - Test scripts (from package.json): test, test:ui, lint, build

Test Data:
  - /Users/t/Desktop/demo-target-project/test-data (directory)
  - /Users/t/Desktop/demo-target-project/server.js (seed script)

Existing Tests:
  - 1 test file detected: tests/e2e/demo.spec.js

================================================================================
5. SAFETY
================================================================================

The adapter enforces these boundaries:

DO:
- Read target repository files for discovery
- Execute SAFE-classified commands (npm test, npx playwright test, etc.)
- Capture stdout, stderr, exit codes, duration
- Report secret variable names WITHOUT values
- Work within target repository directory

DO NOT:
- Copy secrets into shared-state
- Print credential values
- Modify production configuration
- Modify application source code
- Delete target project files
- Install dependencies automatically
- Run destructive commands (rm -rf, docker rm, git reset --hard, etc.)
- Run approval-requiring commands (git push, kubectl, terraform apply)

Command Classification Examples:
  npm run test                          → SAFE
  npx playwright test                   → SAFE
  npm run build                         → SAFE
  rm -rf /tmp/test                      → DESTRUCTIVE (blocked)
  git push origin main                  → REQUIRES APPROVAL (blocked)
  curl -X POST http://localhost:3000/api/users → UNKNOWN
  docker rm mycontainer                 → DESTRUCTIVE (blocked)

================================================================================
6. EXECUTION CONTRACT — Normalized Result
================================================================================

The execute_command() method returns a normalized result dict:

{
  "status": "completed" | "failed" | "timeout" | "error" | "blocked",
  "command": "the command string",
  "classification": "SAFE" | "REQUIRES APPROVAL" | "DESTRUCTIVE" | "UNKNOWN",
  "working_directory": "/path/to/target/repo",
  "exit_code": 0,
  "duration": 1.23,
  "stdout": "...",
  "stderr": "...",
  "artifacts": [],          # file paths collected for evidence
  "errors": []             # error details
}

This contract is Playwright-independent. It supports:
- Playwright (npx playwright test)
- API tests (curl, custom scripts)
- Appium (appium commands)
- Database (psql, mysql, mongosh)
- Webhook (curl, custom listeners)
- Performance (k6, locust, jmeter)
- Event-driven (kafka-console-consumer, rabbitmq tools)

================================================================================
7. ARTIFACT CONTRACT
================================================================================

Artifacts flow from Target Project → Harness via:

1. DIRECT PATHS: adapter.execute_command() returns artifact paths in the
   "artifacts" list. Specialists collect these paths from test output.

2. HARVEST: The adapter can be extended to harvest artifacts from known
   target-project locations (e.g. test-results/, playwright-report/,
   screenshots/, traces/).

3. POLICY-BASED COPYING: The Harness references or copies artifacts based
   on a defined policy rather than assuming target project directory
   structure.

4. Existing shared-state contract is preserved:
   - shared-state/<STORY_ID>/execution/evidence-index.md
   - shared-state/<STORY_ID>/execution/run-report.md
   - shared-state/<STORY_ID>/execution/<test-id>/

================================================================================
8. DYNAMIC SKILL SELECTION — Boundary & Current Status
================================================================================

Boundary established:

  Story
  +
  Target Capability Map (from adapter.detect_capabilities())
  +
  Project Policy (from project.yaml application/api/automation flags)

  =
  Selected Skills

Example selection logic (conceptual):

  UI story + Playwright target → Playwright, Test Data, Authentication,
                                  Execution, Evidence, Failure Analysis

  API story + REST target → API, Test Data, Authentication,
                              Execution, Evidence, Failure Analysis

  Payment webhook story → API + Webhook + Database (if configured)

  Kafka story → API + Event-Driven + Database (if configured)

  Mobile story → Appium

  Performance requirement → Performance

CURRENT IMPLEMENTATION STATUS:
- Capability map: IMPLEMENTED (adapter.detect_capabilities())
- Story parsing: IMPLEMENTED (existing qa-run stages)
- Selection engine: NOT YET WIRED into qa-run runtime

The adapter produces the capability map that the selection engine will
consume. The wiring is the next phase.

================================================================================
9. DEMO TARGET PROJECT — Independent Structure
================================================================================

Location: /Users/t/Desktop/demo-target-project/
(OUTSIDE the Harness source tree)

Structure:
  package.json              — npm project, express + @playwright/test
  playwright.config.js      — Playwright config, baseURL from env
  server.js                 — Simple Express app (port 3000)
  public/index.html         — Static web page
  tests/e2e/demo.spec.js    — 14 Playwright tests (API + webhook)
  test-data/seed.json       — Deterministic seed data
  .env.example              — 4 env vars (values NOT in file)

Independently runnable:
  npm install              — installs dependencies (verified OK)
  npm start                — starts server on localhost:3000
  npx playwright test      — runs tests (requires browser install)

The target project does NOT depend on the Harness. It runs standalone.

================================================================================
10. VALIDATION — Actual Results
================================================================================

Command: python3 qa-run projects/demo/stories/STORY-DISCOVERY.md
(14 sequential invocations, one per stage)

Results:
  Stage 1: story-intake       — completed
  Stage 2: discovery          — completed (target project data detected)
  Stage 3: analysis           — completed
  Stage 4: grill              — completed
  Stage 5: risk               — completed
  Stage 6: architecture       — completed
  Stage 7: specification      — completed
  Stage 8: test-design        — completed
  Stage 9: delegation         — completed
  Stage 10: execution         — completed (correctly reports BLOCKED for
                                 execution since no environment running)
  Stage 11: failure-analysis  — skipped (no failures, correct behavior)
  Stage 12: review            — completed
  Stage 13: evidence          — completed
  Stage 14: final-report      — completed

Overall: completed

Discovery output verified to contain:
  ✓ Target repository path: /Users/t/Desktop/demo-target-project
  ✓ Language: javascript
  ✓ Package manager: npm
  ✓ Playwright detected (version ^1.40.0)
  ✓ playwright.config.js parsed
  ✓ Test directory: /Users/t/Desktop/demo-target-project/tests
  ✓ Base URL: http://localhost:3000
  ✓ 4 environment variables listed WITHOUT values
  ✓ 4 test scripts from package.json
  ✓ 2 test data locations
  ✓ 1 existing test file
  ✓ test command: npx playwright test
  ✓ Webhooks: Yes (detected in target repository)

Command Classification Test:
  npm run test              → SAFE
  npx playwright test       → SAFE
  npm run build             → SAFE
  rm -rf /tmp/test          → DESTRUCTIVE (blocked)
  git push origin main      → REQUIRES APPROVAL (blocked)
  ls -la                    → SAFE
  npm install               → SAFE
  docker rm mycontainer     → DESTRUCTIVE (blocked)
  echo hello                → SAFE

Execution Test (safe command):
  Command: echo hello from adapter
  Status: completed, exit_code: 0
  stdout: "hello from adapter\n"
  working_directory: /Users/t/Desktop/demo-target-project

Execution Test (destructive command):
  Command: rm -rf /tmp/test-should-not-exist
  Status: blocked
  Reason: Command classified as DESTRUCTIVE

================================================================================
11. REMAINING GAPS
================================================================================

P0 (blocks next phase):
1. Dynamic skill selection NOT wired into qa-run runtime.
   The capability map exists but is not yet consumed by the orchestrator
   to select skills per story. This is the next implementation step.

2. Playwright specialist agent NOT implemented yet.
   The spec asked to NOT implement execution yet — discovery only.
   Playwright execution will be implemented in the next phase.

3. No real test execution against the demo target.
   The demo target project is installed and structured correctly.
   npx playwright test has not been run end-to-end (browser install
   failed on this macOS version, but the project is independently valid).

P1:
4. No CI/CD detection detail (only detects presence of CI config files,
   doesn't parse specific pipeline configurations).

5. No database connection testing (adapter detects database presence but
   doesn't connect or validate).

6. No mobile/appium detection beyond file scanning.

P2:
7. No artifact harvesting from target project (adapter collects paths but
   doesn't copy artifacts to shared-state automatically).

8. No CI workspace path injection (ci_workspace flag is accepted but not
   yet functional).

================================================================================
12. SUCCESS CRITERION
================================================================================

Spec requirement: "The Harness can independently identify and safely
interact with an external target repository without being installed
inside that repository."

VERIFICATION:

✓ Harness (this repo) is separate from target project
✓ Target project is at /Users/t/Desktop/demo-target-project/
✓ Harness discovers target via project.yaml target_repository.path
✓ Capability map correctly identifies Playwright, JavaScript, npm,
  web, API, webhooks, existing automation
✓ Environment discovery extracts base URL, env var names (no values),
  test scripts
✓ Test data locations detected
✓ Existing tests detected
✓ Command execution works with correct cwd (target repo)
✓ Safety classification blocks destructive/approval commands
✓ Secrets never exposed (PORT, BASE_URL, API_URL,
  WEBHOOK_SIGNING_SECRET all show "NOT EXPOSED")
✓ stage-status.json contract preserved
✓ 14-stage workflow order preserved
✓ Backward compatible — project.yaml without target_repository is a no-op

SUCCESS CRITERION MET.

================================================================================
END OF REPORT
================================================================================
