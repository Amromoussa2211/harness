Purpose

Use this skill when the user provides a Markdown user story and asks to:

analyze the story
create test cases
explore the application
generate Playwright tests
execute Playwright tests
investigate failures
heal automation failures
report application defects

This skill is reusable across projects and must not contain project-specific business logic.

Required capabilities

The agent should have access to:

Playwright
Playwright Test
Playwright CLI
Playwright MCP
Browser access through MCP
Existing project files and configuration

Do not require Claude.

Inputs

Primary input:

<story>.md

Optional project context:

package.json
playwright.config.*
tests/
fixtures/
helpers/
data/
README.md
Workflow

Execute the following workflow:

Story
  ↓
Analyze requirements
  ↓
Create test cases
  ↓
Playwright MCP browser exploration
  ↓
Generate Playwright spec
  ↓
Playwright CLI execution
  ↓
Failure classification
  ↓
MCP investigation/healing when appropriate
  ↓
CLI re-run
  ↓
QA report
Phase 1 — Story analysis

Read the complete Story.

Identify:

requirements
acceptance criteria
positive scenarios
negative scenarios
boundary cases
validation rules
test data
authentication requirements
dependencies
risks

Do not invent requirements.

Phase 2 — Test cases

Create:

test-cases/<story-id>-test-cases.md

Each test case must include:

ID
title
objective
preconditions
test data
steps
expected result
priority
automation candidate
Phase 3 — Browser exploration

Use Playwright MCP.

Explore the real application before generating locators.

Inspect:

pages
DOM/accessibility snapshots
inputs
buttons
links
dialogs
validation messages
navigation
relevant network behavior

Prefer:

getByRole
getByLabel
getByPlaceholder
getByText
data-testid

Avoid brittle selectors and hard waits.

Phase 4 — Generate test

Create:

tests/<appropriate-path>/<story-id>.spec.js

Use the project's existing language and architecture.

Reuse:

fixtures
helpers
page objects
configuration

Do not create a new framework when one already exists.

Phase 5 — Execute

Use Playwright CLI:

npx playwright test <spec-file>

Collect:

pass/fail
errors
screenshots
traces
console errors
network failures

A generated test is not considered complete until it has been executed.

Phase 6 — Failure classification

Classify failures as:

LOCATOR_PROBLEM
TIMING_PROBLEM
TEST_DATA_PROBLEM
ENVIRONMENT_PROBLEM
APPLICATION_BUG
ASSERTION_PROBLEM
AUTHENTICATION_PROBLEM
NETWORK_PROBLEM
UNKNOWN
Phase 7 — Healing

Use Playwright MCP when the failure is an automation problem.

Investigate the current browser state.

Examples:

changed locator
changed accessible name
changed DOM structure
timing issue
stale selector

Validate the replacement locator before modifying the test.

Then run:

npx playwright test <spec-file>

again.

Critical healing rule

Never change an assertion simply to make the test pass.

Never change expected business behavior to match an unexpected application result.

If the application violates the Story or acceptance criteria:

APPLICATION_BUG

Do not heal it.

Test data rule

If a test uses external gateway/payment/sandbox data and the external provider behavior has changed:

TEST_DATA_PROBLEM

Do not change the assertion to hide the problem.

Do not repeatedly retry real-gateway transactions.

Phase 8 — Final report

Create:

reports/<story-id>-qa-report.md

Include:

Story
Test cases
generated spec
execution results
healed tests
application bugs
test-data problems
files created/modified
Final response

Report:

Story:
...

Test Cases:
...

Playwright Spec:
...

Execution:
...

Healing:
...

Application Bugs:
...

Test Data Problems:
...

Report:
...
Completion criteria

The workflow is complete only when:

Story was analyzed.
Test cases were created.
Browser was explored using Playwright MCP.
Playwright spec was generated.
Spec was executed using Playwright CLI.
Failures were classified.
Appropriate automation failures were healed.
Healed tests were rerun.
Application defects were not hidden.
Final QA report was created.
