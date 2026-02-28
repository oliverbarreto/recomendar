# Task 0051: Divide Subscriptions Page Tabs into Two Pages

- Session File: @task-0051-divide-subscriptions-page-tabs-v1.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-16
- Model: Claude Sonnet 4.5

## Prompt (Ask Mode)

@frontend/src/components/layout/sidepanel.tsx

We want to separate the two tabs currently under the page /subscriptions: "Followed Channels" and "Videos" into two pages:

- /subscriptions/channels - Followed Channels Tab
- /subscriptions/videos - Videos Tab

### Requirements:

- I want you to kepp in both pages the top header with the button "Follow Channel"
- Add both pages in the sidebar navigation:
  - /subscriptions/channels - Use current `rss` icon for this page
  - /subscriptions/videos - Use `list-video` icon for this page
- Do not change the current functionality of the page /subscriptions, we want to keep it as it is.
- The links off both tabs should navigate to each other
- Change the path of the notification button to point to '/subscriptions/channels'

### Analysys

I want you to analyze the current implementation of the `/subscriptions/videos` page to consider if it will be best to use search params in the url to filter the videos by state (pending, reviewed, episode created) and youtube channel.

## Prompt (Agent Mode)

Almost got it perfect at first try. You left the same tabs in both pages.

The page `/subscriptions/channels` Should only show the tab "Followed Channels" and the top header with the button "Follow Channel".
Similarly, the page `/subscriptions/videos` Should only show the tab "Videos" and the top header with the button "Follow Channel"

## Prompt (Agent Mode)

Now modify the plan at `docs/tasks/task-0047-new-feature-follow-channel-discover-videos-v2-SUMMARY.md` to reflect we just made to separate the tabs into two pages.
