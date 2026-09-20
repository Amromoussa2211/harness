# Story Intake — STORY-003

**Source:** /Users/t/Desktop/qa-agent-harness/projects/demo/stories/STORY-003.md
**Project:** demo
**Story ID:** STORY-003
**Intake timestamp:** 2026-09-20T09:08:20Z

---

## Story Title

Password Reset

## User Story

As a registered user,
I want to reset my password using a verification code sent to my email,
so that I can regain access to my account if I forget my password.

## Acceptance Criteria

### AC1 — Request Reset

Given a registered user exists,
When the user requests a password reset with their email,
Then a verification code should be sent to that email.

### AC2 — Valid Code

Given a password reset request has been made,
When the user submits a valid verification code and a new password,
Then the password should be updated.

### AC3 — Expired Code

Given a password reset request has been made,
When the user submits an expired verification code,
Then the reset should be rejected.

## Business Rules

- Verification codes expire after 10 minutes.
- A verification code can only be used once.
- The new password must meet the password policy.

## Notes

This is a fresh story for runtime validation.
No real application should be accessed.

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
