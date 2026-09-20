# STORY-003

## Title

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
