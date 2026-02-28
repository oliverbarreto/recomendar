# Task 0065: BUGFIX - Automated taks are listed as executed by "user" instead of "system" in the activity page

- Session File: task-0065-BUGFIX-automated-tasks-events-are-listed-as-executedby-user-full-session.md
- IDE: Cursor
- Date: 2025-12-02
- Model: Composer 1

---

## Prompt (Plan Mode)

Great !!! We have a working implementation of the automated tasks to discover new videos for all followed channels.

Now, as you can see in the image, we actually triggered the tasks and even video was correctly found in a channel during the search process. 5 tasks were launched for all 5 channels currently in the database and all 5 were completed correctly. I can see the events correctly stored in the database (table "notifications").

However, we have a proble we must fix. I see that the column "executed_by" all have "system" as value, however in the activity page (see the image) all events are listed as "user".

explore the codebase frontend and backed api to understand the logic and the workflow involved. Review this aspect and fix the problem. We must make sure that the events are listed as "system" in the activity page.
