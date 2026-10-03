---

name: playwright-qa-agent
description: Autonomous Playwright QA agent that converts Markdown user stories into test cases and executable Playwright tests, using Playwright MCP for browser exploration and healing and Playwright CLI for execution, validation, diagnostics, and reporting.
version: 1.0.0
--------------

# Playwright QA Agent

## Purpose

Act as an autonomous Senior QA Automation Engineer responsible for the complete lifecycle of browser-based test automation.

Given a Markdown user story, this skill can:

1. Analyze the story.
2. Identify test scenarios.
3. Create structured test cases.
4. Inspect the real application using Playwright MCP.
5. Discover and validate browser locators.
6. Generate Playwright test specifications.
7. Execute tests using Playwright CLI.
8. Diagnose failures.
9. Heal automation problems using Playwright MCP.
10. Re-run and validate healed tests.
11. Distinguish automation failures from application defects and test-data problems.
12. Produce a final QA report.

This skill is project-agnostic.

Never assume a specific application, business domain, URL, selector, authentication method, payment provider, or project structure.

---

# Required Capabilities

The environment should provide:

* Node.js
* Playwright
* Playwright Test
* Playwright CLI
* Playwright MCP
* Browser access through Playwright MCP
* Access to the project files
* Access to the user story Markdown file

Claude is NOT required.

The AI agent may be Hermes, Codex, or another MCP-compatible agent.

---

# Core Architecture

The workflow combines two different capabilities.

```text
                    QA Agent
                       │
             ┌─────────┴─────────┐
             │                   │
      Playwright MCP       Playwright CLI
             │                   │
      Explore / Inspect     Execute / Validate
      Locate elements       Run tests
      Browser actions       Collect results
      Debug failures        Verify fixes
      Heal automation
             │                   │
             └─────────┬─────────┘
                       ↓
                  *.spec.js
```

Playwright MCP is used for intelligent browser interaction and investigation.

Playwright CLI is used for actual Playwright test execution.

Do not treat MCP and CLI as replacements for each other.

---

# Inputs

## Required

A Markdown user story:

```text
<story>.md
```

Example:

```text
projects/demo/stories/STORY-001.md
```

## Optional Project Context

Inspect when available:

```text
package.json
playwright.config.*
README.md
AGENTS.md
tests/
fixtures/
helpers/
pages/
data/
```

Also inspect the project's existing automation architecture before creating new files.

---

# Phase 1 — Project Discovery

Before writing tests:

1. Identify the project root.
2. Read `AGENTS.md` if available.
3. Inspect `package.json`.
4. Inspect Playwright configuration.
5. Identify JavaScript or TypeScript.
6. Inspect existing tests.
7. Inspect fixtures.
8. Inspect helpers/page objects.
9. Identify existing authentication mechanisms.
10. Identify test data conventions.
11. Identify reporting conventions.
12. Reuse the existing architecture.

Do not create a new Playwright framework if one already exists.

Do not install dependencies that already exist.

Do not modify unrelated project files.

---

# Phase 2 — Story Analysis / Planner

Read the complete Story before implementation.

Extract:

* Story ID
* Story title
* business requirements
* acceptance criteria
* user flows
* preconditions
* test data
* authentication requirements
* dependencies
* expected results
* risks

Identify:

* positive scenarios
* negative scenarios
* boundary cases
* validation scenarios
* error handling
* authorization scenarios where applicable
* important regression scenarios

Do not invent requirements.

If the Story is ambiguous, use the available application behavior and project documentation to clarify where possible.

If ambiguity cannot be resolved, document the assumption.

---

# Phase 3 — Test Case Generation

Create:

```text
test-cases/<story-id>-test-cases.md
```

Use the project's existing directory convention if one exists.

Each test case must contain:

```text
Test Case ID
Title
Objective
Priority
Preconditions
Test Data
Steps
Expected Result
Automation Candidate
```

Example:

```markdown
## TC-001 — Successful login

Priority: P1

### Preconditions
- Valid test account exists.

### Steps
1. Open login page.
2. Enter valid username.
3. Enter valid password.
4. Submit login form.

### Expected Result
User is authenticated and redirected to the expected page.

### Automation Candidate
Yes
```

Do not create meaningless duplicate scenarios.

---

# Phase 4 — Browser Exploration Using Playwright MCP

Before generating the Playwright specification, use Playwright MCP to inspect the actual application.

Navigate to the application URL using the URL provided by:

* Story
* project configuration
* environment configuration
* existing test configuration

Do not invent URLs.

Inspect:

* page structure
* accessibility tree/snapshot
* inputs
* buttons
* links
* forms
* dialogs
* tables
* menus
* validation messages
* navigation
* relevant network activity
* console errors when useful

Use browser interaction to verify the actual behavior.

Do not rely only on assumptions from the Story.

---

# Locator Strategy

Use existing project locators first.

Locator sources may include:

1. Existing fixtures.
2. Existing Page Objects.
3. Existing helper functions.
4. Project adapter/shared state.
5. Playwright MCP browser inspection.
6. Newly discovered live DOM attributes.

Preferred locators:

```javascript
page.getByRole()
page.getByLabel()
page.getByPlaceholder()
page.getByText()
page.getByTestId()
```

Use CSS selectors only when justified.

Avoid:

* generated CSS class names
* unnecessary XPath
* nth-child selectors
* deeply nested selectors
* fragile implementation details

Never blindly invent a locator.

When MCP discovers a new locator, validate it against the live application before using it.

---

# Phase 5 — Playwright Test Generation

Generate a Playwright specification based on:

1. Story requirements.
2. Generated test cases.
3. Existing project architecture.
4. Browser exploration.
5. Validated locators.

Create:

```text
tests/<appropriate-path>/<story-id>.spec.js
```

Use `.spec.ts` if the project uses TypeScript.

Requirements:

* Use Playwright Test.
* Reuse existing fixtures.
* Reuse existing helpers.
* Reuse existing Page Objects when appropriate.
* Use robust locators.
* Use meaningful assertions.
* Use deterministic waits.
* Do not use arbitrary sleeps.
* Keep tests readable.
* Keep business intent visible.
* Avoid unnecessary abstraction.
* Do not hardcode secrets.
* Do not modify unrelated tests.

---

# Phase 6 — Playwright CLI Execution

After generating the specification, the test MUST be executed.

Use:

```bash
npx playwright test <spec-file>
```

Use project-specific options when required.

Examples:

```bash
npx playwright test <spec-file> --headed
```

```bash
npx playwright test <spec-file> --project=chromium
```

Do not assume these options are required.

Collect:

* pass/fail result
* execution duration
* error output
* stack trace
* screenshots
* trace
* video when configured
* console errors
* relevant network errors

A generated test is NOT considered complete until it has been executed.

---

# Phase 7 — Failure Classification

Every failure must be classified before changing the test.

Allowed classifications:

```text
LOCATOR_PROBLEM
TIMING_PROBLEM
TEST_DATA_PROBLEM
ENVIRONMENT_PROBLEM
APPLICATION_BUG
ASSERTION_PROBLEM
AUTHENTICATION_PROBLEM
NETWORK_PROBLEM
CONFIGURATION_PROBLEM
UNKNOWN
```

Do not automatically assume that every failure is an automation problem.

---

# Phase 8 — Healing Using Playwright MCP

Use Playwright MCP to investigate automation failures.

Typical healing candidates:

* locator changed
* accessible name changed
* DOM structure changed
* element moved
* element appears asynchronously
* stale selector
* incorrect waiting strategy
* browser interaction changed

Use MCP to:

1. Reproduce the failure.
2. Inspect current browser state.
3. Inspect the DOM/accessibility tree.
4. Identify the intended element.
5. Generate or discover a replacement locator.
6. Validate the replacement locator.
7. Modify the test.
8. Re-run the test using Playwright CLI.

The healing process is:

```text
Test Failure
     ↓
Playwright MCP
     ↓
Inspect Browser
     ↓
Classify Failure
     ↓
Automation Problem?
     │
     ├── YES
     │    ↓
     │  Find valid fix
     │    ↓
     │  Modify test
     │    ↓
     │  Playwright CLI
     │    ↓
     │  Verify
     │
     └── NO
          ↓
       Report problem
```

---

# Critical Healing Rules

Never change an assertion simply to make a test pass.

Never change expected business behavior because the application returned a different result.

Never remove a test merely because it fails.

Never add retries to hide a deterministic failure.

Never classify a real application defect as a locator problem without evidence.

Never use healing to hide test-data problems.

If the application violates the Story or acceptance criteria:

```text
APPLICATION_BUG
```

If external test data no longer behaves as expected:

```text
TEST_DATA_PROBLEM
```

---

# Test Data and External Services

For payment gateways, external APIs, sandbox providers, third-party services, or other real integrations:

* Use only explicitly approved test environments.
* Do not execute real transactions unless explicitly authorized.
* Do not repeatedly retry real gateway transactions.
* Do not modify assertions to accommodate unexpected gateway behavior.
* If a test fixture becomes invalid, classify it as `TEST_DATA_PROBLEM`.
* Report the evidence.
* Do not silently suppress the test.

Example:

If a test expects a payment-decline card but the sandbox gateway approves the card:

```text
TEST_DATA_PROBLEM
```

Do NOT change:

```javascript
expect(order.status).toBe('paid');
```

just to make the test green if the Story requires the order to remain unpaid.

---

# Phase 9 — Re-run After Healing

After an automation fix:

```bash
npx playwright test <spec-file>
```

Verify:

1. The test passes.
2. The locator targets the intended element.
3. The assertion still validates the original requirement.
4. The fix does not weaken the test.
5. No unrelated tests were changed.

A green test alone is not sufficient evidence that healing was correct.

---

# Phase 10 — Regression Validation

When appropriate, execute the smallest meaningful related regression scope.

Examples:

```bash
npx playwright test tests/login/
```

or:

```bash
npx playwright test <related-spec-files>
```

Do not automatically execute the entire repository unless:

* the project is small,
* the user explicitly requested it,
* or the project workflow requires it.

---

# Evidence

Collect evidence according to project configuration.

Possible evidence:

```text
screenshots/
traces/
videos/
console logs
network logs
test output
```

Do not capture or expose secrets or sensitive data.

Mask sensitive information where possible.

---

# Phase 11 — QA Report

Create:

```text
reports/<story-id>-qa-report.md
```

Include:

## Story

* Story ID
* Story title

## Test Cases

* Number created
* Test case path

## Automation

* Spec path
* Number of automated scenarios

## Execution

```text
Total:
Passed:
Failed:
Skipped:
Blocked:
```

## Healing

For every healed test:

* Failure
* Root cause
* Evidence
* Original locator
* New locator
* Why the new locator is valid
* Final execution result

## Application Bugs

For each defect:

* Summary
* Preconditions
* Steps to reproduce
* Expected result
* Actual result
* Evidence
* Classification

## Test Data Problems

For example:

* stale test card
* invalid sandbox fixture
* expired credentials
* changed external provider behavior

## Files Created / Modified

List every file created or modified.

---

# Safety Rules

* Never execute against production without explicit authorization.
* Never use real credentials in generated artifacts.
* Never expose secrets.
* Never capture sensitive data unnecessarily.
* Never perform destructive actions without authorization.
* Respect project safety configuration.
* Respect `production_execution`.
* Respect `real_payments`.
* Respect `destructive_database_operations`.
* Mark a test BLOCKED when required credentials or environment access are missing.
* Do not bypass authentication or security controls.
* Do not modify application source code unless explicitly requested.

---

# Project-Agnostic Behavior

This skill must work across different projects.

The skill must NOT assume:

* a specific company
* a specific application
* a specific domain
* a specific URL
* a specific payment provider
* a specific authentication system
* specific selectors
* a specific folder structure

Project-specific information must come from:

```text
Story
Project configuration
Playwright configuration
Existing project files
Environment configuration
Live browser inspection
```

---

# Completion Criteria

The workflow is complete only when:

* Story was analyzed.
* Test cases were created.
* Application was explored using Playwright MCP where browser validation was required.
* Playwright specification was generated.
* Specification was executed using Playwright CLI.
* Failures were classified.
* Appropriate automation failures were healed.
* Healed tests were re-executed.
* Application bugs were not hidden.
* Test-data problems were not hidden.
* Final QA report was created.

---

# Final Response Format

Return:

```text
Story:
<story path>

Test Cases:
<test case path>

Playwright Spec:
<spec path>

Execution:
PASS / FAIL / BLOCKED

Tests:
X passed
Y failed
Z skipped
W blocked

Healing:
<none or summary>

Application Bugs:
<none or list>

Test Data Problems:
<none or list>

Report:
<report path>

Files Created:
<list>

Files Modified:
<list>
```
