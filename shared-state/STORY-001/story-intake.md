# Story Intake — STORY-001

**Source:** /Users/t/Desktop/qa-agent-harness/projects/demo/stories/STORY-001.md
**Project:** demo
**Story ID:** STORY-001
**Intake timestamp:** 2026-09-20T09:08:20Z

---

## Story Title

User Login

## User Story

As a registered user,
I want to log in using my email and password,
so that I can access my account.

## Acceptance Criteria

### AC1 — Successful Login

Given a registered user exists

When the user enters a valid email and valid password

And clicks Login

Then the user should be redirected to the Dashboard.

### AC2 — Invalid Password

Given a registered user exists

When the user enters a valid email and invalid password

Then the login request should be rejected.

And an appropriate error message should be displayed.

### AC3 — Empty Email

When the user submits the login form without an email

Then the email field should show a validation error.

### AC4 — Empty Password

When the user submits the login form without a password

Then the password field should show a validation error.

## Business Rules

- Email is required.
- Password is required.
- Invalid credentials must not create a session.
- Successful authentication creates an authenticated session.

## Notes

This is a demo story used to validate the QA Agent Harness workflow.

No real application should be accessed.
No real credentials should be used.

## Project Configuration Summary

- **Project name:** demo
- **Description:** N/A
- **Application — web:** True
- **Application — api:** True
- **Application — mobile:** False
- **Automation framework:** playwright
- **Automation language:** javascript
- **API — REST:** True
- **API — GraphQL:** False
- **API — webhooks:** False
- **Database enabled:** False
- **Database type:** none
- **Environment — dev:** False
- **Environment — staging:** False
- **Environment — production:** False
- **Safety — production execution:** False
- **Safety — real payments:** False
- **Safety — destructive database operations:** False

## Known Constraints

- Production execution is disabled by project safety configuration.
- Real payment transactions are disabled by project safety configuration.
- Destructive database operations are disabled by project safety configuration.
- No environments are enabled in the project adapter.

## Unknown or Missing Information

- No application URL or base URL specified.
- No valid test credentials available.
