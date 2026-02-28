# Task 0047 v3: New Feature: Search Engine for YouTube Videos - Notification System - Plan

- Session File: @task-0047-new-feature-follow-channel-discover-videos-v3.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-16
- Model: Claude Sonnet 4.5

## Prompt (Plan Mode)

@task-0047-new-feature-follow-channel-discover-videos-v2-SUMMARY.md

I want you to analyze current status of the implementation of the new feature to follow Youtube channels and create podcasts episodes from them.

We are in a state in which we can add youtube channels to follow, we can search for latest videos, we can mark a video as reviewed and we can also create an episode from a video when the user selects "Create Episode" in the video card which triggers the process of actually creating the podcast episode and downloading the audio file. In this point, we decided to replicate the service that we were using in FastAPI to do the same in Celery task when we trigger the download, and it now works.

Read the detailed summary of implementation in the file @task-0047-new-feature-follow-channel-discover-videos-v2-SUMMARY.md to have a full picture of the overall architecture and feature. Also fully understand the section "## Future Enhancements" with the pending tasks to plan the rest of the implementation.

## Prompt (Plan Mode)

Let me clarify your questions:

1. Which features do you want to implement?

The tasks defined in the section "## Future Enhancements" are not numbered with priority. They are just listed in order.

Create the plan based on phases, one for each main task. One phase for each feature. Lets implement:

- Advanced Filtering for Videos page (filter by channel, date range/year, bulk operations)
- Task Progress UI with real-time feedback for check/backfill operations
- Notification System for discovered videos and created episodes

2. For the Advanced Filtering feature implement them in this order:

   - Start with filtering by YouTube channel dropdown (currently missing from UI)
   - Then with date range/year filtering
   - Finally with bulk operations (select multiple videos, perform actions)

3. For Task Progress UI feature implement it in this order:

   - Backend infrastructure first (task status tracking, polling endpoints)
   - Frontend UI first (status indicators on channel cards, progress displays)

4. For Notification System feature implement it in this order:

   - Notify users when new videos are discovered after a check/backfill operation
   - Notify when episodes are created, both from the interaction of the user via the FastAPI (Quick Add Episode, Create Episode from locall uploaded video, Create Episode from Youtube Video) routes or from the Celery tasks (Create Episode from Video)
   - DO NOT IMPLEMENT NOW Email/push notifications. This is pending to decide if we want to implement this in the future.
