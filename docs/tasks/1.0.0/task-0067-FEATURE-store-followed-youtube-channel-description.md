# Task 0065: FEATURE - STORE TITLE & DESCRIPTION OF A YOUTUBE CHANNEL IN THE DATABASE WHEN WE GET THE DATA WHEN FOLLOWING A CHANNEL

- Session File: task-0065-FEATURE-store-followed-youtube-channel-description-full-session.md
- IDE: Cursor
- Date: 2025-12-02
- Model: Composer 1

---

## Prompt (Plan Mode)

REFACTOR: Store Title & Description of a Youtube Channel in the database when we get the data.

### Current Context:

Right now, in our model of followed youtube channels, which we store in the table “followed_channels” we have the following data: `youtube_channel_id`, `youtube_channel_name`, `youtube_channel_url` and `thumbnail_url`.

We now want to extend the current model and modify the codebase to support the new data.

### Expected behavior

We now want to also store the channel description in a new column `youtube_channel_description`.

This information must be extracted when the user uses the “+ Follow Channel”. The problem will be existing channels don’t have this information, so we must deal with an empty text. I can later add the text for current channels manually into the database.

There is also one more thing that i want to take the opoirtunity and add at the same time. I want to add a new action to the context menu of followed channels: “Update channel info”. This new action will trigger the same api call that we use to get the data the first time we create a channel, and update the channel info since the channels might change their description or image along the way.

We do not update any other columns. Only `youtube_channel_id`, `youtube_channel_name`, `youtube_channel_url`, `thumbnail_url` and the new `youtube_channel_description` must be updated.

Then, the UI of the followed channel cards must be changed to add:

- the channel description text below the title
- a new menu option in the context menu of the followed channel card to "Update channel info"

### Tasks

Fully understand the requirements of the expected behavior of new feature and explore the codebase to understand how to fully understand the logic, the workflow, the architecture, use cases, and the database model and schema of the codebase involved.

Create a detailed implementation plan with phases and tasks to implement the new feature. Analyze how we can schedule launching the use case that we have already implemented using Celery tasks. We should use existing functionality as much as possible. And only extend the current functionality to add the new data.

We should be already following a (relaxed version of) Clean Architecture approach.

Do not include any code yet. Just focus on the plan and tasks.

Ask more questions if you need to clarify the objective and task in order to create a detailed implementation plan in Phases with tasks and sub-tasks.
