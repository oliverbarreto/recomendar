# Task 0080: New section in home page with latest videos discovered

- Session File: @task-0080-new-section-in-home-page-with-latest-videos-discovered-full-session.md
- IDE: Cursor 2.0
- Date: 2025-12-07
- Model: Cursor Composer 1

## Prompt (Plan Mode)

I want to create a new section in the home page with the latest videos discovered from the followed channels. Every time the user follows a new channel, the system will periodically fetch for updates and potentially discover the latest videos from that channel. We want now to extend the home page with this new section and display new information.

Currently in the home page we have a section "Latest Episodes" that displays the 10 latest episodes created in the podcast channel.
We want create a new section called "Latest Videos Discovered" that displays the 10 latest videos discovered from the followed channels.

In the "/subscriptions/videos" page, we have a list of videos discovered from the followed channels. We want to display the latest videos discovered from the followed channels in the home page still in "pending_review" state.

## Requirements:

- Create a new horizontal section in the home page with the latest youtube videos discoveries
- The section should be called "Followed Channels - New Videos Discovered"
- The section should display the latest videos discovered from the followed channels
- Use the same card component as the ones we use in the "/subscriptions/videos" page
