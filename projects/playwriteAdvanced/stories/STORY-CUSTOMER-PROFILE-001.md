# STORY-CUSTOMER-PROFILE-001

## User Story

As a registered customer,
I want to view and manage my customer profile,
so that I can update my personal information and view my order history.

## Acceptance Criteria

### AC1 — View Profile Page
Given a logged-in customer
When the customer navigates to the profile page
Then the profile page displays the customer's name, email, and phone number

### AC2 — Update Profile Information
Given a logged-in customer on the profile page
When the customer updates their phone number and saves
Then the updated information is persisted
And the customer sees a success confirmation

### AC3 — View Order History
Given a logged-in customer on the profile page
When the customer views their order history
Then a list of previous orders is displayed with order dates and statuses

### AC4 — Profile Validation
Given a logged-in customer
When the customer attempts to save an empty name field
Then the profile save is rejected
And a validation error is displayed
