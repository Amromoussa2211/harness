# STORY-001

## Title

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