# Task 0063: FEATURE: Automate followed channels discovery with Celery Beat - v2

- Session File: task-0063-FEATURE-automate-followed-channels-discovery-with-celery-beat-full-session-v2.md
- IDE: Claude Code
- Date: 2025-12-01
- Model: Claude Sonnet 4.5

---

## Prompt (Agent Mode)

We are stuck in making work the feature to allow automatic videos discovery using Celery tasks in the background with Celery Beats. The problem is that after implementing the plan, we are stuck in making the required settins work. In the advanced tab in /settings page we have two important settings: the frequency (can be an enum of two values: daily or weekly) and the hour (using two fields in the ui one for the hour, and the other for the minutes).

When we navigate to this tab in settings, we get a toast message "Failed to load settings" and when we try to save clicking the "save changes" button we get another toast message with the following error "Failed to save settings: auerv.args: Field required; query.kwargs: Field required".

Explore the codebase, analyze the logic involved in the frontend and backend to retrieve the data from the database (careful with enums, and conversion from the ui to what the backend api expects, and viceversa).

This is a trivial task. Analyze how it is working, how it should work, and Plan how it fix it
