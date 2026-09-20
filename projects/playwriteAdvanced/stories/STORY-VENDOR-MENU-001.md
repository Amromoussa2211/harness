# STORY-VENDOR-MENU-001

## User Story

As an admin vendor,
I want to manage the product catalog through the admin panel,
so that I can add categories, add items, and organize the product offerings.

## Acceptance Criteria

### AC1 — Add Category
Given an admin logged into the vendor panel
When the admin creates a new category with a name and description
Then the category is saved and appears in the categories list

### AC2 — Add Item
Given an admin logged into the vendor panel
When the admin adds a new item with name, price, category, and description
Then the item is created and associated with the selected category

### AC3 — Category-Item Association
Given categories and items exist in the system
When an item is assigned to a category
Then the item appears under the correct category in the catalog

### AC4 — Admin Dashboard Access
Given an admin logged in
When the admin accesses the vendor dashboard
Then the dashboard shows categories count, items count, and recent activity
