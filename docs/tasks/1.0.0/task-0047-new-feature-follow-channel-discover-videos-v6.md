# Task 0047 v6: New Feature: Search Engine for YouTube Videos

- Session File: @task-0047-new-feature-follow-channel-discover-videos-v6-full-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-28
- Model: Claude Opus 4.5

## Prompt (Plan Mode)

We are in the middle of implementing the new feature: "Follow Channel and Discover Videos". We haven't finnished yet, there are still some improvements to be made to the workflow and ui. Make sure you fully understand and execute the task given in the file @docs/tasks/task-0047-new-feature-follow-channel-discover-videos-v6.md

---

We are in the middle of implementing the new feature: "Follow Channel and Discover Videos". We haven't finnished yet, there are still some improvements to be made to the workflow and ui.

## Context overview of the feature

The "Follow Channel and Discover Videos" feature enables users to:

1. **Follow YouTube channels** - Subscribe to channels for automatic video discovery
2. **Discover new videos** - Automatically fetch metadata for new videos from followed channels
3. **Review videos** - Browse discovered videos and decide which ones to convert to episodes
4. **Create episodes** - Convert selected videos into podcast episodes with automatic audio download
5. **Notifications** - Receive notifications for new videos, tasks progress, and errors.

### Key Design Decisions

- **Celery + Redis**: Professional task queue for reliable background processing
- **Separate Video Storage**: Videos are stored separately from episodes until user decides to create an episode
- **State Machine**: Videos transition through states: `pending_review` → `reviewed` → `queued` → `downloading` → `episode_created`
- **Dual Download Paths**: FastAPI BackgroundTasks for Quick Add, Celery tasks for Follow Channel feature
- **Auto-approve**: Optional automatic episode creation for new videos
- **Separate Pages**: Followed Channels and Videos are now on separate pages (`/subscriptions/channels` and `/subscriptions/videos`) for better navigation and organization
- **URL Search Params**: Videos page supports URL search parameters for filtering (state, channel, search) enabling bookmarking and sharing filtered views

## OBJECTIVES:

### OBJECTIVE 1: Improve the background tasks and ui of the workflow to update metadata downloaded from "Followed Youtube Channel"

Our task is to implement the finnishing touches to the Feature to allow following youtube channels and creating podcast episodes from the videos, and the ui improvements to the workflow and notifications.

IMPORTANT: DO NOT CHANGE THE VIDEO CARDS shown in the page `/subscriptions/videos`, we are placing the focus on the cards shown on the page `/subscriptions/channels` and the workflow and notifications.

In `/subscriptions/channels`the user can use the context menu of a channel to "search for new videos". When this happens, the system will create a celery task that uses the `yt-dlp` API to find new videos for the channel:

#### When we launch the celery task, and it starts:

1. we should update the status icon to a processsing icon, and a label in the "Followed Youtube Video" card with the new status: "searching new videos"

2. we should show a message in the `notifications` section (bell icon) saying "searching new videos for channel NAME_CHANNEL" and provide a link to navigate to the channels page filtering by the channel, eg: "/subscriptions/videos?channel=1"

#### When the celery task is finnished:

1. we should show an green check icon with no label in the "Followed Youtube Video" card. Update the label with the date of the last update.

2. we should show a message in the `notifications` section (bell icon) saying "search for new videos finished for channel NAME_CHANNEL" It should also contain a number inside a badge with the number of new videos found (from the ones already in the db) and provide a link to navigate to the `/subscriptions/channels` page but filtering by channel and the pending review status, eg: "/subscriptions/videos?state=pending_review&channel=1"

#### When the celery tasks gives an error:

1. Show an error icon and a label to tell the user to retry searching in the context menu.

2. We should show a message in the `notifications` section (bell icon) saying "Error searching for new videos for channel NAME_CHANNEL. You can retry in the subscriptions page" and provide a link to navigate to `/subscriptions/channels`

### OBJECTIVE 2: Improve "Followed Youtube Channel" card component

We need to improve the "Followed Youtube Channel" card component that we use in the `/subscriptions/channel` page:

- It should have a link to navigate to `/subscriptions/videos` filtering by the Youtube channel, eg: "/subscriptions/videos?channel=1"
- The card should also show stats with the actual number of videos in the database for the channel by state, eg: "all: 50 | Pending Review: 5 | Reviewed: 40 | Downloading: 0 | Episode Created: 5"
- It should contain an indication of status, just like we do when downloading an episode from an url. We show an icon representing the status of the tasks being managed by celery "queued/searching/finnished/error" and a label with the corresponding status description:
  - queued: queued icon (monitor-pause), message "queued"
  - searching: processing icon (monitor-cog), "searching"
  - finnished: green check icon (circle-check), message with the date of the last update ("updated: dd/MM/YYYY")
  - error: error icon (cloud-alert), message to "retry"

### OBJECTIVE 3: Improve The notifications bell button and Notifications popup

The notifications popup triggered by the bell icon on the sidebar needs to be improved:

- notifications can have state: "unread | read"
- it should include a link to the `/subscriptions/channels` page.
- it should show messages from the last 10 days (if they not have been removed before)
- it should allow removing a single notification (mark it as read)
- it should have a button to clear all notifications (mark all as read) in the notifications list
- the sidebar icon should include a badge with the number of pending (unread) notifications

## Tasks:

The app can now run locally in my machine using Docker Compose (production configuration). I have tested the feature and it correctly follows channels and discovers new videos, but we need to make various improvements and fixes to the workflow and ui.

- Make sure you fully understand the 3 objectives detailed in the "OBJECTIVES" section and explore the codebase to understand the code involved for this feature in the backend and frontend.

- I want you to locally run the app locally using docker with production configuration to test the feature and monitor errors and logs to ensure the app works correctly.

Note: Use the following command to start the app:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

---

## Prompt (Plan Mode)

- Model: Claude Sonnet 4.5

We now have the correct information on the followed youtube channels cards with the stats of the videos with links to the videos page filtering all status (all, pending review, reviewed, downloading, episode created) and the date of the last task to check for new videos.

However, there are still some things missing:

- [ ] When we click the button on the card to trigger a new search for new videos, we see the toast message "Check task queued successfully" but the status of the task is not being updated in the card, nor in the notifications section (bell icon). This has the purpose to let the user know what is happening in the background. (See image 2)
- [ ] when the celery task is finnished, we should update the status of the task in the card and the notifications section (bell icon) to show the number of new videos found. It is not hapenning neither. (See image 3)
- [ ] the popup that is shown when the notifications section (bell icon) is clicked should show events of celery tasks from the last 10 days and the number of new videos found in the badge with the number of pending (unread) notifications. It should also implement the functionality to manage the notifications. All these things are not hapenning neither. (See image 1)
- [ ] when the celery task gives an error, we should update the status of the task i n the card and the notifications section (bell icon) to show the error message. I have no way to test this manually, so you need to implement it and test it.

---

## Prompt (Plan Mode)

- Model: Claude Sonnet 4.5

As you can see in the image provided, we are having errors on the browser console. The problem is the same we had with the health check endpoint.

We are using the following call to the endpoint: `https://labcastarr-api.oliverbarreto.com/v1/notifications?skip=0&limit=20&unreadonl`
But the endpoint DOES REQUIRED THE BACKSLASH AT THE END OF THE URL, so it should be `/v1/notifications/`. Fix this issue.

---

## Prompt (Plan Mode)

- Model: Claude Sonnet 4.5

Great we now fixed the problem with the notifications endpoint, but we now have a nother problem. As you can see in the image provided, we are having errors on the browser console. The problem is that we are getting a 404 error when we try to get the task status of a channel with the following call: `https://labcastarr-api.oliverbarreto.com/v1/followed-channels/2/task-status`.

Analyze the problem and fix it.

---

## Prompt (Plan Mode)

- Model: Claude Sonnet 4.5

Ok, now we have the page working correctly and got rid of the most of the errors on the browser console. The problem is that we are not updating the status of the celery task in the notifications section (bell icon).

I have analized the browser console and have identified that we are in fact receiving the status of the celery task from the backend, but we are not updating the status of the notifications section (bell icon), and we still don't show the list of events in the notifications popup.

- In image 1: we can see that we have 16 notifications, with the full payload to be used to update the notifications section (bell icon). Notification number 0 is the task with id 16, which I believe it is created when we click to start searching for new videos for the channel. It has type: "channel_search_started".

- In image 2: we can see that we now get an event with type: "channel_search_completed" after it finnised searching for new videos. This event has now notification id number 0 and task id 17 and has full payload to be used to update the notifications section (bell icon).

## Requirements:

I want to change the approach to notify the user.

### New Activity page: /activity

I want to create a new page `/activity` with a table list of all the events that have happened in the system. The page should be accessible from the sidebar menu and should be named "Activity" and have an clock icon (lucide "clock") with a list of events in a table. The page must be responsive and accessible, and enable pagination in case the list of events is too long.

The table should have the following columns:

- Event Type:
  - Name: "Type"
  - Value: channel_search_started, channel_search_completed, channel_search_error: with a descritive text instead of the enum value
- Channel Name:
  - Name: "Channel"
  - Value: with a link to navigate to the `/notifications/videos`page filtered by the channel id
- Event Date:
  - Name: "Date"
  - Value: (dd/mm/yyyy)
- Event Time:
  - Name: "Time"
  - Value: hh:mm:ss
- Event Description:
  - Name: "Description"
  - Value: with the text describing the event

### Notification bell component: `/components/features/notifications/notification-item.tsx`

The notification bell component should not show a popup anymore. Its purpuse is twofold:

Firstly, it should show a badge with the number of unread notifications. It should be updated every time we finnish a celery task.
Secondly, it should be a link to navigate to the `/activity` page.

## Tasks:

I want you to fully understand the requirements first. Then explore the codebase and understand the code involved for this feature in the backend and frontend. Then analyze the changes needed to implement the requirements and create a plan in different phases if needed.

Do not create any code yet. Just the plan.
Ask as many questions as needed to fully understand the requirements and the approach needed to implement the requirements and create the plan.
