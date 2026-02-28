# TASK 0047 v7: CHANGE FEATURE NOTIFICATIONS APPROACH TO USE ACTIVITY PAGE instead of the notifications section (bell icon) with popup

- Session File: @task-0047-new-feature-follow-channel-discover-videos-v7-full-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-28
- Model: Cursor Sonnet 4.5

## Prompt (Plan Mode) - 🔥 CHANGE FEATURE NOTIFICATIONS APPROACH TO USE ACTIVITY PAGE instead of the notifications section (bell icon) with popup

- Model: Cursor Sonnet 4.5

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
Ask as many questions as needed to fully understand the requirements and the approach needed to implement the requirements and create the plan

---

QUESTIONS:

1. For the new Activity page (/activity), should it display ALL notification types (including VIDEO_DISCOVERED, EPISODE_CREATED) or ONLY the channel search-related events (CHANNEL_SEARCH_STARTED, CHANNEL_SEARCH_COMPLETED, CHANNEL_SEARCH_ERROR)?

- [X] A. ll notification types - show complete activity history
- [ ] B. Only channel search events - focused on search activity

2. When the notification bell is clicked, should it navigate directly to /activity or should it still show a small popup with a quick summary and a 'View All Activity' button that links to /activity?

- [x] A. Direct navigation - clicking the bell goes straight to /activity page
- [ ] B. Show a small popup with a quick summary and a 'View All Activity' button that links to /activity

3. In the Activity table, the 'Channel Name' column should link to '/notifications/videos'. Did you mean
   'subscriptions/videos' (which is the existing page) or is '/notifications/videos' a new page you want to create?

- [x] A. Link to /subscriptions/videos (existing page)
- [ ] B. Create a new /notifications/videos page

4. Should the Activity page allow filtering notifications by type, date range, or channel? Or should it just be a simple chronological list with pagination?

- [ ] A. Simple chronological list with pagination only
- [x] B. Include filters for type, date range and/or channel

5. Should notifications be deletable from the Activity page, or should they only be markable as read/unread? Or both?

- [ ] A. Only mark as read/unread - no deletion
- [ ] B. Only delete - no read/unread toggle
- [ ] C. Both mark as read/unread AND delete
      SKIP THIS QUESTION.

For the case of the question 5, I want to provide more context: the "activity" page should:

- it should always have the latest notifications at the top of the list and have applied when the page shows the filter to show only not read notifications. In case the user wants to see all notifications, he should apply the filter to "Show all" in the top of the page.
- it should allow removing a single notification (mark it as read) in a context menu button on the right side of the notification item with an horizontal ellipsis icon (lucide "ellipsis") and an action "Mark as read".
- it should have a button to mark ALL notifications as button "Mark all as read" in the top of the page. It should display a confirmation dialog before clearing all notifications.
- it should have a button to DELETE all notifications (delete from the database) in the top of the page. It should display a confirmation dialog before clearing all notifications.

---

## Prompt (Plan Mode)

- Model: Cursor Auto

run the app locally with docker compose (docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d) and fix all the errors we try to build the app (in the nextjs frontend)

```bash
 => ERROR [frontend builder 4/4] RUN npm run build                                                                                    5.2s
 => [celery-worker stage-0 7/7] RUN chmod +x /app/startup.sh                                                                          0.1s
 => CANCELED [celery-beat] exporting to image                                                                                         1.5s
 => => exporting layers                                                                                                               1.5s
 => CANCELED [backend] exporting to image                                                                                             1.5s
 => => exporting layers                                                                                                               1.5s
 => CANCELED [celery-worker] exporting to image                                                                                       1.5s
 => => exporting layers                                                                                                               1.5s
------
 > [frontend builder 4/4] RUN npm run build:
0.295
0.295 > frontend@0.1.0 build
0.295 > next build
0.295
0.829 Attention: Next.js now collects completely anonymous telemetry regarding usage.
0.829 This information is used to shape Next.js' roadmap and prioritize features.
0.829 You can learn more, including how to opt-out if you'd not like to participate in this anonymous program, by visiting the following URL:
0.829 https://nextjs.org/telemetry
0.829
0.862    ▲ Next.js 15.5.2
0.862
0.906    Creating an optimized production build ...
5.137 Failed to compile.
5.137
5.138 ./src/app/activity/page.tsx
5.138 Module not found: Can't resolve '@/components/ui/pagination'
5.138
5.138 https://nextjs.org/docs/messages/module-not-found
5.138
5.138 ./src/components/features/activity/activity-actions.tsx
5.138 Module not found: Can't resolve '@/components/ui/alert-dialog'
5.138
5.138 https://nextjs.org/docs/messages/module-not-found
5.138
5.138 Import trace for requested module:
5.138 ./src/app/activity/page.tsx
5.138
5.138 ./src/components/features/activity/activity-table.tsx
5.138 Module not found: Can't resolve '@/components/ui/table'
5.138
5.138 https://nextjs.org/docs/messages/module-not-found
5.138
5.138 Import trace for requested module:
5.138 ./src/app/activity/page.tsx
5.138
5.141
5.141 > Build failed because of webpack errors
5.151 npm notice
5.151 npm notice New major version of npm available! 10.8.2 -> 11.6.4
5.151 npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.6.4
5.151 npm notice To update run: npm install -g npm@11.6.4
5.151 npm notice
------
Dockerfile:30

--------------------

  28 |

  29 |     # Build the application with env vars available

  30 | >>> RUN npm run build

  31 |

  32 |     # Production image, copy all the files and run next

--------------------

target frontend: failed to solve: process "/bin/sh -c npm run build" did not complete successfully: exit code: 1



View build details: docker-desktop://dashboard/build/default/default/3hrxaif82y4zkfssdi6nzg3g2
```

---

## Prompt (Plan Mode)

- Model: Cursor Auto

As you can see in the image, we get an error in the browser console "Uncaught RangeError: Invalid time value" Analyze it and fix it

---

## Prompt (Plan Mode)

- Model: Cursor Auto

it now works but the date and time columns show no data. What is wrong ? is the data not available in the event ? is it a conversion problem ? fix it

---
