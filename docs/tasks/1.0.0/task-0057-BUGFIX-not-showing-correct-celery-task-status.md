# Task 0057: BUGFIX: Update the status of the celery task in the Followed Youtube Channel card component

- Session File: @
- IDE: Claude Code - Plan Mode
- Date: 2025-11-30
- Model: Claude Sonnet 4.5

---

## Prompt (Agent Mode)

Now I want to tackle an issue we have updating the status of the celery task in the Followed Youtube Channel card component.

We have the problem that when we send the task to the background, we are updating the Followed Youtube Channel card component by having a icon spinning when we send the task to search for new videos to the background.

The problem that i have identified is that the card correctly shows the status "queued" right away, but it last for a very long time, then it directly jumpts to updated and the date.

According to the workflow of the specs of this feature, we should have the status "queued" when the user clicks the "search for new videos" button, and the celery task is queued, but not when the celery task actually starts its job of searching for new videos (when the task is being handled by a Celery worker). When we are actually searching for new videos, the status should be "searching" and not "queued". We need to show "searching" when the celery task is being processed which is what actually should take time.

According to the documentation in @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md the state machine for the celery task, we might have a problem since it has a state downloading, not searching.

Note from the documentation that the `celery_task_status` states are as follows: `PENDING`, `STARTED`, `PROGRESS`, `SUCCESS`, `FAILURE`, `RETRY`. We might have a problem that maybe we are using the wrong state, we might be using
`youtube_videos` state (**States:** `pending_review`, `reviewed`, `queued`, `downloading`, `episode_created`, `discarded`) instead of `celery_task_status` state.

### Testing Information

I tested the flow with a full test and i was able to reproduce the problem. I got the following results:

1. The user clicks the "search for new videos" button.
2. The system creates a celery task and updates the status of the celery task in the UI to "queued".
3. The celery task starts doing its jobbut the UI is still showing "queued".
4. The celery task is finnished successfully and the status of the celery task in the UI is still showing "queued".
5. The UI is updated to show "completed"
6. Then after i refresh the page, the status is changed to reflect "updated" and the date of the last update (eg: updated: 30/11/2025 10:40)

A few more notes that i investigated of a full test of the flow:

1. In image 1 we can see that right after we click on the button to search for new videos, a toast message is shown saying "RSS check task queued successfully" and the status is updated to "queued" and the icon starts spinning.
2. In image 2 we can see the case that after the celery task has found some new videos and marked them as "pending review", the satus still shows "queued" and the icon keeps spinning. In image 3 we see that when we checked the activity page we saw that the action of finding new videos has two events: first event type is "Search started" and the second and most recent event is "Search completed".
3. In image 4 we see that after a while, the status is changed to reflect "completed" and, then after i refreshed the page, we see in image 5 that the status was finally changed to reflect "updated" and the date of the last update (updated: 30/11/2025 10:40).

### Tasks

- Read and understand the technical analysis of the feature in @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md
- Understand the problem and the testing information
- Analyze how to go about fixing the problem

---

## Prompt (Agent Mode)

I have tested the changes and launched a couple of updates in various followed channels. Sometimes it works, but i found that sometimes it does not work.

I have investigated and found these problems:

OBSERVATION 1: IMAGE 1

- as you can see in the left side of image 1, when searching for channel "THE GRIM" (followed_channels id: 2), the status shows "queued" and the icon in the context menu (Search for lastest videos RSS Feed) keeps spinning.

- Then in the right side of the image 1, we see the activity events and we have that we opened and close the event at the very same time:

```
Most recent event: Search Started, THE GRIM, 30/11/2025	12:24:00, Searching for new videos, Searching for new videos from THE GRIM
Second most recent event: Search Completed, THE GRIM, 30/11/2025	12:24:00, Search completed for THE GRIM, No new videos found from THE GRIM
```

- We also have a pending celery task in the background. I checked it using the advanced tab in settings. After i cancel the task, using this tool the card is fixed and shows the "updated: 30/11/2025 12:24" and we can now start using the options in the context menu

OBSERVATION 1: IMAGE 2

- as you can see in the left side of image 2, when searching for channel "THE GRIM" (followed_channels id: 2), the status shows "searching" with a spinning icon.

- However, in the right side of image 2, we see the activity events and we have that we opened and close the event at the very same time, but the status icon keeps spinning with "searching" label. After a while, the status changed to "updated: 30/11/2025 12:38" removing the "searching" label and its icon spinning.

- How can we have a "searching" status when the celery task is being processed and not a "queued" status? Are we using the wrong state? Are we triggering the saving of events using wrong status changes?

---

## Prompt (Agent Mode)

Nop. I ran the search again and into both cases:

- in image 1 we have the case that the status shows "queued" and the icon keeps spinning in the left side of the image, while the activity page already has both events: "Search Started" and "Search Completed" for Channel: Theo - t3․gg and time: 30/11/2025 12:58:02.

- image 2 shows that i got searching status and the icon keeps spinning in the left side of the image, while the activity page already has both events: "Search Started" and "Search Completed" with the same time "30/11/2025 12:59:35" for channel: THE GRIM (first row).

Analyze the problem and explore the codebase to find the root cause of the problem.

---

## Prompt (Agent Mode)

After the lastest changes i tried launching the search again. I got both cases.. one got stuck with queued status and i had to cancel the task. The other one showed searching status but the activity page already had both events: "Search Started" and "Search Completed" with the same time "30/11/2025 12:59:35".

---

## Prompt (Agent Mode)

We are trying to fix the problem of not showing the correct status of the celery task in the Followed Youtube Channel card component.

Explore the codebase, read and understand the technical analysis of the feature in @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md to try to solve the following problem that we are facing.

### PROBLEM SUMMARY

I have observed two cases:

#### OBSERVATION 1:

I click on search for new videos button and the status shows "queued", while the activity page already has both events: "Search Started" and "Search Completed", both with the same time. After a couple of minutes, I refresh the page and the status shows "updated" and the date of the last update is shown, with the time of the events that were shown in the activity page some time before the refresh.

#### OBSERVATION 2:

I click on search for new videos button and the status shows "searching ", while the activity page already has both events: "Search Started" and "Search Completed", both with a separation of 2 seconds. After a while the status shows "updated" and the date of the last update is shown, with the time of the events that were shown in the activity page some time before the refresh.

### Tasks

- [ ] Explore the codebase, read and understand the technical analysis of the feature in @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md to try to solve the following problem that we are facing.

- [ ] Describe the process that is going on the frontend and the backend. We must make sure that we generate the events that get saved in the database and then shown in the activity page correctly. This means that Celery tasks must generate the events correctly and the frontend must show them correctly.

  - Is the frontend polling the backend to get the status of the celery task? In that case, we might be showing a status value that is not the actual status in the database due to polling refresh times. In that case, will it suffice to reduce the polling time? Will it need anything else?
  - Are we not generating the correct events according to the celery task status? In that case, we might be generating the events incorrectly and the frontend might be showing them incorrectly.

- [ ] Analyze the problem and explore the codebase to find the root cause of the problem.
- [ ] Define a plan to fix the problem.

---

## Prompt (Plan Mode)
