# STORY-LOGIN-VAL

## User Story
As a registered user,
I want to log in with my email and password,
so that I can access my account.

## Acceptance Criteria
### AC1 — Successful Login
Given a registered user with valid email and valid password
When the user performs the login action
Then the user is redirected to the Dashboard

### AC2 — Invalid Password
Given a registered user with valid email
When the user provides an invalid password
Then the action is rejected

### AC3 — Empty Email Field
Given the login form is displayed
When the user submits without entering an email
Then the email field shows a validation error
