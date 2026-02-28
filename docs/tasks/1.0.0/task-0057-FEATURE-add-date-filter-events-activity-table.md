# Task 0057: FEATURE: Add date filter events activity table

- Session File: @task-0057-FEATURE-add-date-filter-events-activity-table-full-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-30
- Model: Cursor Auto Model

## Prompt (Agent Mode)

@frontend/src/app/activity/page.tsx @frontend/src/components/features/activity/activity-table.tsx

implement the "date range" filter in the /activity page which is currently disable. Use ShadcnUI calendar component to get the starting and finish date to filter the table

---

## Prompt (Agent Mode)

put a bit more effort styling the comopnent. It looks odd, and stuffed together. Aslo, change first date of week to monday. Give more room for the component

---

## Prompt (Agent Mode)

The style is now much better. I want now to tackle the problem with the way the results are shown. When i filter the table by date range, the results are not shown correctly.

After we apply the filter the app filters the page and shows no record with a message "No activity found - Notifications will appear here when events occur". However, we know there are events in the date range. The page shows in the pagination options to move acrros various pages. When we move these pages, the page shows the correct events by date. The problem is that the first page is always empty, with no events shown.

---

## Prompt (Agent Mode)
