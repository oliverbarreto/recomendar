# Task 0047 v1: New Feature: Search Engine for YouTube Videos

- Session File: @task-0047-new-feature-follow-channel-discover-videos-v1.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-03
- Model: Cursor Composer 1

## Prompt (Plan Mode)

NEW FEATURE: We want to create a fully new and important feature to allow the user to be able to follow a channel for new episodes.

Files Attached:

- @video-search-engine/ (full project folder used as reference)
- @video-search-engine/labcastarr-bot/CLAUDE.md (CLAUDE.md file from the video-search-engine project)
- @docs/backend-libs-ytdlp-docs.md (yt-dlp documentation)

The user can tell the system from the contextual menu of the episode cards (in the home page and the /channel page) and also from the contextual menu in the details page of an episode, that we wants to follow that channel meaning that he wants the system to monitor updates from that channel checking for new videos daily. The videos will be listed on a new page: “subscriptions” which will show a list of all videos that have been found from all channels that we are monitoring. The contextual menus will have therefore a new option called “follow channel” and will display a confirmation modal form to tell the user he is about to start following that specific channel, and that new videos will be checked periodically and will be displayed in the the page “/subscriptions” from where he can select which ones he wants to create an episode from.

I have created a FastAPI project that searches for youtube Channels and fetches episodes and also download transcripts of videos. The idea is to utilize this project as the basis for creating a new feature of the project. Here is the description in the [CLAUDE.md](http://CLAUDE.md) file with the details and architecture of the project. WE want to pay attention to the part of searching for new videos and retrieving metadata using YT-DLP library. The project is also capable of downloading transcripts, but for now, we only want to be aware that is there, it can be useful in the future if we do something with the transcript. But for now, is only about:

- following channels,
- periodically identifying new videos from those channels: we should have an option in settings to select: daily, twice a week, weekly,
- downloading and storing metadata from those videos: do not download the audio to create an episode until the user selects a new video to create a new episode for the channel, only download the video metadata using YT-DLP
- presenting new videos to the user: so he can chose which ones he wants to create an episode with. The user can also discard videos he does not want to use to create a new episode for the channel. The discarded videos should not be removed from the database, only marked as “reviewed”. This leads to create a state to model this, we have new videos that are pending review, and reviewed.
- creating the episodes and downloading the audio file: we should model another state to handle downloading: create a new episode with this video, downloading audio, episode created with this video (audio downloaded).

Initial Requirements:

- The user can then also access a page in the app that shows all available videos from different youtube channels he adds for the app to monitor new videos from.
- The user can then select the videos he want to create episodes in the channel.
- Then the app will download the audio and create the episode in the podcast channel.
- The user can mark in the list videos as reviewed, he might keep them in the list, not taking a decision where to discard or add to the podcast channel.

- The UI should have a “notification bell” icon to tell the user there are new videos identified pending to be reviewed The notification bell will have a link to the /subscrition page (we do not want to send a notification at this point, maybe in the future will be a new feature, and we can design other methods in the future like email/push/other).

- The page should have search functionality (similar to the one used in the /channels page) to be able to filter “new videos”, “reviewed videos” and “in the channel” (the ones selected to be part of the podcast channel)
- The user should also have an easy way to list, edit and remove followed channels.
- The episodes created from a channel as a podcast episode should not be removed when marking a Youtube channel as not followed any more. However, all metadata and episodes pending decision, will be deleted.
- Also to take into account, when adding a new youtube channel to follow, we should lookup for new videos for at least the last 20 videos (if that much) of the current year. The list of followed channels in the /subscriptions page will have options to download more videos by years and by all previous years. This check will be executed in the background as an independent check of the periodic checks for new videos in the channel. We should try to find using YT-DLP, if possible, the date the channel was created to allow showing the years prior to the current year..
- Also the user should be able to mark a followed channel as "auto-approved downloading all episodes". Meaning that all episodes that the periodic check in the future will be used to

If you have any other considerations please feel free to work with me asking questions to provide more detail. The idea is to create a very detailed prd and specificacion for this new feature. providing insights of all kind of technical and functional requirements.

### Results

Questions
Subscription check frequency: Is the "daily, twice a week, weekly" setting:
a) Global (one setting applies to all followed channels)
b) Per-channel (each channel can have its own frequency)
Scheduling mechanism: For periodic checks, should we use:
a) APScheduler (in-process scheduler)
b) External cron job (system cron)
c) Background task queue (Celery/Redis)
d) FastAPI startup background task (simple loop)
Video state management: When a user selects a video to create an episode, should it:
a) Immediately start downloading audio (transition: pending → downloading → episode created)
b) Queue the download as a background task (transition: pending → queued → downloading → episode created)
Auto-approved channels: When a channel is marked "auto-approved", should new videos:
a) Automatically create episodes in all user channels (or a default channel)
b) Prompt the user to select which podcast channel to use for auto-created episodes
c) Be configurable per followed channel (store which podcast channel to use)
Initial backfill: When following a channel, fetching the last 20 videos from the current year should:
a) Run synchronously (user waits)
b) Run as a background task (immediate response, process in background)
Video metadata storage: Should we store metadata from yt-dlp:
a) In a new youtube_videos table separate from episodes
b) Reuse/extend the existing episodes table with a new status field
Please answer these to finalize the plan.

## Prompt (Plan Mode)

Here are the answers to the questions:

Questions

1. Subscription check frequency: Is the "daily, twice a week, weekly" setting:
   The options should be Global (one setting applies to all followed channels)

2. Scheduling mechanism: For periodic checks, should we use:
   a) APScheduler (in-process scheduler)
   b) External cron job (system cron)
   c) Background task queue (Celery/Redis)
   d) FastAPI startup background task (simple loop)

In this case i have a doubt. I would like to use the Background task queue (Celery/Redis) to schedule the periodic checks for new videos in the channels. However, i do not want to over complicate the project with a new dependency like Celery/Redis. I want you to give me your opinion on this and suggest the best solution for this case. I want you to be 100% confident that the Background task queue (Celery/Redis) is the best solution and that you can help me to implement it. Also, you have to to take into account that Celery is not part of the project yet. So we should include a phase in the project to add Celery as a dependency and make it work with docker-compose.

3. Video state management: When a user selects a video to create an episode, should it:
   Queue the download as a background task (transition: pending → queued → downloading → episode created)

4. Auto-approved channels: When a channel is marked "auto-approved", should new videos:
   This auto-approve option is per-channel. Each channel can have its own auto-approve setting.

5. Initial backfill: When following a channel, fetching the last 20 videos from the current year should:
   Run as a background task (immediate response, process in background)

6. Video metadata storage: Should we store metadata from yt-dlp:
   We should use a fully new "youtube_videos" table separate from episodes

## Prompt (Agent Mode)
