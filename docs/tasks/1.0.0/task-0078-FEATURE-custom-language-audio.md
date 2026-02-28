# Task 0078: FEATURE - Custom Language Audio: Allow downloading media file in to create episodes in other languages

- Session File: @task-0078-FEATURE-custom-language-audio-full-session-1.md
- IDE: Claude Code
- Date: 2025-12-07
- Model: Claude Opus 4.5

---

## Prompt (Plan Mode)

We want to finalize building the feature of background followed channel videos discovery and the creation of podcast episodes from them.

But first I want you to explore the codebase and analyze the functionality that what we already have working when we download the media file of a youtube video to create a podcast episode for our channel. We need to have a clear understanding of the current pieces providing this feature. Remember that all the media download and metadata of Youtube videos is being handled utilizing “yt-dlp” library.

### CONTEXT:

Currently, we should have two parallel workflows capable of downloading media files from youtube videos and creating a podcast episode:

1. when the user utilizes the UI, I believe that the frontend directly calls FastAPI endpoint which utilizes FastAPI background tasks to conduct all the required steps. We have various ways to do so:

- the user can click the “quick add” modal (launched from the sidepanel button)
- the user can click the “add episode from youtube video” which is the multi-step form (launched from the sidepanel button). This allows the user to create an episode having control of what we actually save into the database after the system fetches the metadatya from youtube and before actually downloading the media file associated to the video
- the user can click the “upload audio episode” (launched from the sidepanel button). This last one should not be the target of the changes, since it does not download any media file utilizing “yt-dlp” library. It uploads the audio from the frontend to the backend and it is ok using FastAPI tasks as of now.

2.  when the user adds a Youtube Channel to be followed, the system will periodically conduct a scheduled search to discover new videos using Celery Beat and Celery tasks, according to the settings (frequency and time).

- In this case, we only download metadata of the videos. We do not download any media file yet, since the user must select the videos he wants to create an episode with.
- When the system founds new videos, the new videos are added to the database and listed as videos found on the “/subscriptions/videos” page associated to a given Youtube Channel.
- Then, there is an option that the user can use to create a podcast episodes out of these videos from followed channels. This option uses Celery tasks to download the media file and create the podcast episode.

### OBJECTIVE:

We want to fully finalize the feature of “Followed Channels” and the use of Celery tasks to work in the background. The purpose of this task is twofold: modify the creation of podcast episodes and the download of media files from the ui and from Celery tasks to be able to download audio files of a given language specified by the user in settings or in the ui in the quick add form.

**BACKGROUND PROCESS WITH CELERY TASKS**

1. we want to add a new option to the user settings (in the “subscriptions” tab of the /settings page) that allows storing a preferred language (using a dropdown with a list of languages codes, eg: default, en, es, fr, …) to allow the user specify the language he wants to create the all the podcast episodes.
2. The system will use this option to always try to download the media file from the youtube video using the language specified in settings for all videos we download for all followed channels of the user.
3. IMPORTANT: If the audio file for a youtube video is not available in the default selected language, we always download the video using the original track.
4. IMPORTANT: The default option should always be to download the audio file with the original language”.
5. **Technical Considerations:**
   1. We should analyze what needs to be modified in the logic, the data model, and the architecture involved in the process now used by Celery tasks to download the audio file of a video in a celery task in the background.
   2. Then we have to analyze how to use “yt-dlp” library to download the audio media file in the specified language.

**PROCESS TRIGGERED FROM THE UI**

We should also modify the “quick add” modal to allow the user to select a different language for the download.

1. The UI should include a checkbox that, when checked, it will show a dropdown with a list of languages for the user to select one (eg: en/us, es/es , …)
2. We should now add that episode using the specified language using the current process with FastAPI background tasks.
3. **Technical considerations:**
   1. The modal should always be pre-loaded with the value the user has defined in settings
   2. If the user specifies a language in the modal for quick adding an episode in another language, this setting will take over all the option that the user might have in settings. For example,
      1. the user has specified “original” in settings and in quick add he selects “es” for spanish, the system should try to download the audio file in spanish
      2. the user has specified “spanish” in settings and in quick add he does selects “en” for english, the system should try to download the audio file in english since he changed the preferred language from what he had in settings.

### Important notes for the UI of this feature both workflows:

1. we have to extend the model to add the information of the language of the downloaded media file for the episode and the original track in:
2. all videos that are downloaded in a different language than the original track, should have a clear mark in the UI:
   1. The card we use in the UI to show an episode of a podcast channel, should have a pill with the language code using an overlay of the thumbnail image of the card, similar to the pill that we already have to represent the current duration of the episode, but in the bottom left side of the thumbnail
   2. The episode details page “[/episodes/](https://labcastarr.oliverbarreto.com/episodes/82)EPISODE_ID” should also add this data. To do so, let’s add it to the page bellow the episode title, to the right of the creation time.

TASKS:

Explore the current codebase to analyze the current workflows we have in place that add an episode to the podcast channel, how we download the audio media file, and how we should download the media.

Analyze the current model for settings, followed channel videos and podcast episodes and also analyze the required new pieces of information that we should add to implement this new feature.

We also need to consider the list of languages codes to be used

If you need to add more questions to have a better understanding of the current codebase, do so.

Do not create any code yet, just plan the steps needed to implement this new feature.

---

## Prompt (Plan Mode) Fully new and clear session

We have just implemented a new feature: "allow the user to create podcast episodes in a different language than the youtube video original audio track". The plan covered allowing the user to create podcast episodes in a different language utillizing all methods available via the UI and via Celery tasks.

When testing the app, i started by testing the "quick add" method in the UI. Then i identified that we feature does not fully work since the podcast episodes are correctly created, but the audio file is not downloaded in the specified language in the modal form. All episodes are always downloaded in the original language.

Let's explore the codebase and analyze the problem and fix it. Do not create any code yet, just plan the steps needed to implement this new feature.

## Prompt (Agent Mode)

Here are the steps of the tests i have conducted:

0. I have not modified settings, so the it is using the default option of "Preferred Audio Language" is "original (no prefference)".
1. I tried to download an episode with the "quick add" method and selecting spanish in the modal form.
2. The episode was created correctly but the audio file was downloaded in the original language (english).

### OBSERVARIONS

These are some things i have found on the logs of the tests:

0. First and most important, I do not want to paste here the full session logs, since it will be way too long and consume the context, This is why i will explain the main important findings. If you need to see the full session logs, you can execute yourself the use case and check for the logs in the docker container.

1. Here we see that we initiate the creation of the episode and we identify the language selected in the modal form, and is clearly identifying the language selected as "es" (spanish): `"create_from_youtube_url", "line": 119, "message": "Using provided language preference: es"}`

```bash
...

2025-12-08 13:15:35.398 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 298, "message": "Creating episode from URL: https://www.youtube.com/watch?v=qxxnRMT9C-8"}

2025-12-08 13:15:35.398 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 299, "message": "Received preferred_audio_language: es"}

2025-12-08 13:15:35.401 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "app.application.services.url_validation_service", "function": "validate_youtube_url", "line": 89, "message": "Successfully validated YouTube URL: qxxnRMT9C-8"}

2025-12-08 13:15:35.402 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 110, "message": "Creating episode from YouTube URL: https://www.youtube.com/watch?v=qxxnRMT9C-8"}

2025-12-08 13:15:35.402 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 111, "message": "EpisodeService received preferred_audio_language: es"}

2025-12-08 13:15:35.402 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 119, "message": "Using provided language preference: es"}

2025-12-08 13:15:35.404 | {"timestamp": "2025-12-08T13:15:35", "level": "INFO", "logger": "labcastarr.downloader", "function": "_proxy_to_logger", "line": 223, "message": "{"url": "https://www.youtube.com/watch?v=qxxnRMT9C-8", "operation": "extract_metadata", "event": "Starting metadata extraction", "logger": "labcastarr.downloader", "level": "info", "timestamp": "2025-12-08T13:15:35.404006Z"}"}

...

```

2. Then we get confirmation of the metadata extraction before actually downloading the audio file:

```bash
...


2025-12-08 13:15:38.338 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "labcastarr.downloader", "function": "_proxy_to_logger", "line": 223, "message": "{"url": "https://www.youtube.com/watch?v=qxxnRMT9C-8", "video_id": "qxxnRMT9C-8", "video_title": "World No.1 Sleep Expert: Magnesium Isn\u2019t Helping You Sleep! This Habit Increases Heart Disease 57%!", "duration_ms": 2934.75, "operation": "extract_metadata", "event": "Metadata extraction completed successfully", "logger": "labcastarr.downloader", "level": "info", "timestamp": "2025-12-08T13:15:38.338731Z"}"}

2025-12-08 13:15:38.339 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "labcastarr.system", "function": "_proxy_to_logger", "line": 223, "message": "{"service": "youtube", "endpoint": "https://www.youtube.com/watch?v=qxxnRMT9C-8", "method": "GET", "success": true, "request_details": {"operation": "metadata_extraction", "video_id": "qxxnRMT9C-8"}, "duration_ms": 2934.748649597168, "event": "External API call to youtube completed", "logger": "labcastarr.system", "level": "info", "timestamp": "2025-12-08T13:15:38.339025Z"}"}

2025-12-08 13:15:38.339 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.application.services.metadata_processing_service", "function": "process_youtube_metadata", "line": 54, "message": "Processing metadata for video: qxxnRMT9C-8"}

2025-12-08 13:15:38.339 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.application.services.metadata_processing_service", "function": "process_youtube_metadata", "line": 105, "message": "Successfully processed metadata for episode: World No.1 Sleep Expert Magnesium Isn’t Helping You Sleep! This Habit Increases Heart Disease 57%!"}

2025-12-08 13:15:38.345 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 150, "message": "Successfully created episode 5: World No.1 Sleep Expert Magnesium Isn’t Helping You Sleep! This Habit Increases Heart Disease 57%! with language: es"}

2025-12-08 13:15:38.345 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 346, "message": "Transaction committed for episode 5"}

2025-12-08 13:15:38.345 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 356, "message": "API session closed for episode 5"}

2025-12-08 13:15:38.346 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 369, "message": "Successfully created episode 5: World No.1 Sleep Expert Magnesium Isn’t Helping You Sleep! This Habit Increases Heart Disease 57%!"}

2025-12-08 13:15:38.346 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "labcastarr.api", "function": "_log_request_completion", "line": 231, "message": "{"correlation_id": "181d7002-b3f2-4fd2-aaa7-a112722fb148", "method": "POST", "path": "/v1/episodes/", "status_code": 201, "processing_time_ms": 2953.73, "client_ip": "88.24.113.79", "user_id": null, "content_length": "4620", "event": "Request completed", "logger": "labcastarr.api", "level": "info", "timestamp": "2025-12-08T13:15:38.346489Z"}"}

2025-12-08 13:15:38.346 | {"timestamp": "2025-12-08T13:15:38", "level": "WARNING", "logger": "labcastarr.api", "function": "_log_request_completion", "line": 246, "message": "{"correlation_id": "181d7002-b3f2-4fd2-aaa7-a112722fb148", "method": "POST", "path": "/v1/episodes/", "processing_time_ms": 2953.73, "user_id": null, "event": "Slow request detected", "logger": "labcastarr.api", "level": "warning", "timestamp": "2025-12-08T13:15:38.346670Z"}"}

2025-12-08 13:15:38.347 | {"timestamp": "2025-12-08T13:15:38", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "_isolated_download_queue", "line": 59, "message": "Waiting for API session cleanup before starting download for episode 5"}

...
```

3. Here you can see that the logs say that we are trying to download the audio file in the preferred language: None: `"line": 183, "message": "Starting download for URL: https://www.youtube.com/watch?v=qxxnRMT9C-8 with preferred language: None"}"`

```bash
...

2025-12-08 13:15:41.353 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "_isolated_download_queue", "line": 68, "message": "Starting isolated download queue for episode 5"}

2025-12-08 13:15:41.365 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "app.infrastructure.services.download_service", "function": "queue_download", "line": 334, "message": "Queued download for episode 5 (priority: 0)"}

2025-12-08 13:15:41.366 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "_isolated_download_queue", "line": 71, "message": "Successfully queued download for episode 5"}

2025-12-08 13:15:41.367 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "app.infrastructure.services.download_service", "function": "_process_queue", "line": 379, "message": "Started download task for episode 5"}

2025-12-08 13:15:41.371 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "app.infrastructure.services.download_service", "function": "_download_episode_task", "line": 441, "message": "Starting download for episode 5: World No.1 Sleep Expert Magnesium Isn’t Helping You Sleep! This Habit Increases Heart Disease 57%!"}

2025-12-08 13:15:41.371 | {"timestamp": "2025-12-08T13:15:41", "level": "INFO", "logger": "labcastarr.downloader", "function": "download_audio", "line": 183, "message": "Starting download for URL: https://www.youtube.com/watch?v=qxxnRMT9C-8 with preferred language: None"}

...

```

4. Finally the audio is downloaded, but in the original audio track.

5. I also checked the database the episodes created with

```sql
select id, title, original_filename, preferred_audio_language, actual_audio_language  from episodes
```

and i found that `preferred_audio_language`and `actual_audio_language` columns were "NULL" for all existing episodes.

---

## Prompt (Agent Mode)

The videos were created correctly, but the audio file was still downloaded in the original language, english.

### Observations

Now we are doing three things that we were not doing before:

1. We are identifying the language selected in the modal form and we are passing it to the service in the backend.

```bash
2025-12-08 15:42:16.660 | {"timestamp": "2025-12-08T15:42:16", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 111, "message": "EpisodeService received preferred_audio_language: es"}

2025-12-08 15:42:16.661 | {"timestamp": "2025-12-08T15:42:16", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 119, "message": "Using provided language preference: es"}

...

2025-12-08 15:42:20.672 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "labcastarr.downloader", "function": "_proxy_to_logger", "line": 223, "message": "{"url": "https://www.youtube.com/watch?v=P7Y-fynYsgE", "video_id": "P7Y-fynYsgE", "video_title": "An AI Expert Warning: 6 People Are (Quietly) Deciding Humanity\u2019s Future! We Must Act Now!", "duration_ms": 4009.74, "operation": "extract_metadata", "event": "Metadata extraction completed successfully", "logger": "labcastarr.downloader", "level": "info", "timestamp": "2025-12-08T15:42:20.672536Z"}"}

2025-12-08 15:42:20.672 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "labcastarr.system", "function": "_proxy_to_logger", "line": 223, "message": "{"service": "youtube", "endpoint": "https://www.youtube.com/watch?v=P7Y-fynYsgE", "method": "GET", "success": true, "request_details": {"operation": "metadata_extraction", "video_id": "P7Y-fynYsgE"}, "duration_ms": 4009.7439289093018, "event": "External API call to youtube completed", "logger": "labcastarr.system", "level": "info", "timestamp": "2025-12-08T15:42:20.672807Z"}"}

2025-12-08 15:42:20.672 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "app.application.services.metadata_processing_service", "function": "process_youtube_metadata", "line": 54, "message": "Processing metadata for video: P7Y-fynYsgE"}

2025-12-08 15:42:20.673 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "app.application.services.metadata_processing_service", "function": "process_youtube_metadata", "line": 105, "message": "Successfully processed metadata for episode: An AI Expert Warning 6 People Are (Quietly) Deciding Humanity’s Future! We Must Act Now!"}

2025-12-08 15:42:20.680 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "labcastarr.processor", "function": "create_from_youtube_url", "line": 150, "message": "Successfully created episode 6: An AI Expert Warning 6 People Are (Quietly) Deciding Humanity’s Future! We Must Act Now! with language: es"}

2025-12-08 15:42:20.680 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 346, "message": "Transaction committed for episode 6"}

2025-12-08 15:42:20.680 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 356, "message": "API session closed for episode 6"}

2025-12-08 15:42:20.680 | {"timestamp": "2025-12-08T15:42:20", "level": "INFO", "logger": "app.presentation.api.v1.episodes", "function": "create_episode", "line": 369, "message": "Successfully created episode 6: An AI Expert Warning 6 People Are (Quietly) Deciding Humanity’s Future! We Must Act Now!"}
...


2025-12-08 15:42:23.705 | {"timestamp": "2025-12-08T15:42:23", "level": "INFO", "logger": "app.infrastructure.services.download_service", "function": "_download_episode_task", "line": 441, "message": "Starting download for episode 6: An AI Expert Warning 6 People Are (Quietly) Deciding Humanity’s Future! We Must Act Now!"}

2025-12-08 15:42:23.705 | {"timestamp": "2025-12-08T15:42:23", "level": "INFO", "logger": "labcastarr.downloader", "function": "download_audio", "line": 183, "message": "Starting download for URL: https://www.youtube.com/watch?v=P7Y-fynYsgE with preferred language: es"}

2025-12-08 15:42:23.705 | {"timestamp": "2025-12-08T15:42:23", "level": "INFO", "logger": "labcastarr.downloader", "function": "download_audio", "line": 191, "message": "Using language-aware format string for es"}

...
```

2. We are actually saving the language selected and the actual language downloaded into the database.

Running this query in the database:

```sql
select id, title, original_filename, preferred_audio_language, actual_audio_language  from episodes
```

We got this result for the two new videos that were created in the test:

```text
id: 6, `preferred_audio_language` = "es", `actual_audio_language` = "en"
id: 7, `preferred_audio_language` = "es", `actual_audio_language` = "en"
```

3. We are now showing the language pill in the episode card and the episode details page. It shows "EN" (english) for both videos. In the episode details page we even show more details: "Audio Language: EN" and "⚠️ Requested ES but not available".

4. All previous results demonstrate that we are almost there, but we need to fix the actual download of the audio file in the specified language in the sevice in the backend.

We can see that the service is trying to download the audio file in the specified language, but it is falling back to the original language in this part of the logs:

```bash
...
2025-12-08 15:42:25.219 | {"timestamp": "2025-12-08T15:42:25", "level": "INFO", "logger": "labcastarr.downloader", "function": "_log_available_formats", "line": 345, "message": "Using format string: bestaudio[language=es][ext=m4a]/bestaudio[language=es][ext=mp3]/bestaudio[language=es]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]"}

2025-12-08 15:42:25.219 | {"timestamp": "2025-12-08T15:42:25", "level": "INFO", "logger": "labcastarr.downloader", "function": "_log_available_formats", "line": 349, "message": "Found 1 audio format(s):"}
2025-12-08 15:42:25.219 | {"timestamp": "2025-12-08T15:42:25", "level": "INFO", "logger": "labcastarr.downloader", "function": "_select_format_by_language", "line": 399, "message": "No format found with language 'es', will use fallback"}

2025-12-08 15:42:25.220 | {"timestamp": "2025-12-08T15:42:25", "level": "INFO", "logger": "labcastarr.downloader", "function": "_download_audio_sync", "line": 255, "message": "Falling back to format string-based selection"}
...
```

In this case, i got the following results directly from a terminal for the last video that was created in the test (video id: qxxnRMT9C-8):

```bash
yt-dlp -F "https://www.youtube.com/watch?v=qxxnRMT9C-8"

[info] Available formats for qxxnRMT9C-8:
ID      EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
139-2   m4a   audio only      2 │   47.96MiB   49k https │ audio only          mp4a.40.5   49k 22k [es] Spanish, low, m4a_dash
249-7   webm  audio only      2 │   48.24MiB   49k https │ audio only          opus        49k 48k [es] Spanish, low, webm_dash
140-2   m4a   audio only      2 │  127.28MiB  129k https │ audio only          mp4a.40.2  129k 44k [es] Spanish, medium, m4a_dash
251-6   webm  audio only      2 │  137.73MiB  140k https │ audio only          opus       140k 48k [es] Spanish, medium, webm_dash
```

As you can see there are other audio tracks available in the video (mp4a and webm),
Even though there is a spanish audio track available, the service is falling back to the original language (english). However we must see that available audio tracks are not in "best quality", the are marked as "Spanish, low" and "Spanish, medium". In this case we should download the audio file in the selected language in the best quality available in mp4a format (this case it is the "Spanish, medium"), even if it is not the "best quality".

### Tasks

Explore the code of the service in the backend to find what we are doing to specify the best quaility available for an specific language which utilizes: "Using format string: bestaudio[language=es][ext=m4a]/bestaudio[language=es][ext=mp3]/bestaudio[language=es]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]". It not available we should manage the case to search for the next best "medium", then "low", and if no audio track is available for a language different than the original, then use the fallback and download the audio file in the original language.

---

### Prompt (Agent Mode)

We are in the middle of creating a new feature: allowing the user to download episodes in an specific language. The problem is that we are having trouble actually downloading the right audio track.

We are testing the workflow by adding episodes to the podcast channel with the "quick add" modal. The episodes are being created correctly, we are identifying the preferred language settings, also the option that a user selects in the modal that can override the default in settings (the original track of a video).

### Observations

Again, in the last test, the episode was downloaded with the original language (english) even when we identified that it should be downloaded in spanish in the modal and the call to the service is also with language "es"

```bash
...
2025-12-08 18:41:13.069 | {"timestamp": "2025-12-08T18:41:13", "level": "INFO", "logger": "app.infrastructure.services.download_service", "function": "_download_episode_task", "line": 441, "message": "Starting download for episode 2: No.1 Brain Scientist Your Brain Is Lying To You! Here's How I Discovered The Truth!"}

2025-12-08 18:41:13.069 | {"timestamp": "2025-12-08T18:41:13", "level": "INFO", "logger": "labcastarr.downloader", "function": "download_audio", "line": 183, "message": "Starting download for URL: https://www.youtube.com/watch?v=hQaN5w3YwtM with preferred language: es"}

2025-12-08 18:41:13.069 | {"timestamp": "2025-12-08T18:41:13", "level": "INFO", "logger": "labcastarr.downloader", "function": "download_audio", "line": 191, "message": "Using language-aware format string for es"}
...
```

In the logs of the last video that was created in the test (video id: hQaN5w3YwtM), we can see the following logs when we specify the format string that is responsible for selecting the audio to download:

```bash
...
2025-12-08 18:41:14.457 | {"timestamp": "2025-12-08T18:41:14", "level": "INFO", "logger": "labcastarr.downloader", "function": "_log_available_formats", "line": 345, "message": "Using format string: bestaudio[language=es][ext=m4a]/bestaudio[language=es][ext=mp3]/bestaudio[language=es]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]"}

2025-12-08 18:41:14.457 | {"timestamp": "2025-12-08T18:41:14", "level": "INFO", "logger": "labcastarr.downloader", "function": "_select_format_by_language", "line": 401, "message": "No format found with language 'es', will use fallback"}
....
```

Running this command in the terminal `yt-dlp -F "https://www.youtube.com/watch?v=hQaN5w3YwtM"`, we get the output that i include later, in which you can see the available audio tracks for the video. AS you can see there is spanish audio tracks available and we are falling back to the original language (english).

### Tasks

Explore the codebase to find the best way to implement the feature. We should create a new piece of the code that will be responsible for detecting available audio tracks and selecting the best audio track for a given language.

We should also investigate how the yt-dlp library works to fully understand how it works and how we can use it to our advantage. We should have a function that will be responsible for detecting available audio tracks and selecting the audio track for a given language. Lets take advantage of this new function and enable a way to specify the quality of the audio track to download: low, medium, high quality. For now lets use the lowest possible as default to allow faster downloads and use less disk storing files.

NOTE (Do not implement this now): This new function would play an important role when we tackle the option to create videos from the UI using the "download from youtube video" which is a multi-step modal form, in which we can plug a new step in the middle to: first search for available languages and allow the user to select from the available ones.

### Full Output of the command `yt-dlp -F "https://www.youtube.com/watch?v=hQaN5w3YwtM"`

```bash
yt-dlp -F "https://www.youtube.com/watch?v=hQaN5w3YwtM"
[youtube] Extracting URL: https://www.youtube.com/watch?v=hQaN5w3YwtM
[youtube] hQaN5w3YwtM: Downloading webpage
[youtube] hQaN5w3YwtM: Downloading tv client config
[youtube] hQaN5w3YwtM: Downloading player 217a23a9-main
[youtube] hQaN5w3YwtM: Downloading tv player API JSON
[youtube] hQaN5w3YwtM: Downloading android sdkless player API JSON
[youtube] [jsc:deno] Solving JS challenges using deno
[info] Available formats for hQaN5w3YwtM:
ID      EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb3     mhtml 48x27        0    │                  mhtml │ images                                  storyboard
sb2     mhtml 80x45        0    │                  mhtml │ images                                  storyboard
sb1     mhtml 160x90       0    │                  mhtml │ images                                  storyboard
sb0     mhtml 320x180      0    │                  mhtml │ images                                  storyboard
139-drc m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, DRC, m4a_dash
249-drc webm  audio only      2 │   34.28MiB   50k https │ audio only          opus        50k 48k [en] English original (default), low, DRC, webm_dash
250-drc webm  audio only      2 │   44.86MiB   65k https │ audio only          opus        65k 48k [en] English original (default), low, DRC, webm_dash
139-0   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [hi] Hindi, low, m4a_dash
139-1   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [nl] Dutch, low, m4a_dash
139-2   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [zh] Chinese, low, m4a_dash
139-3   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [de] German, low, m4a_dash
139-4   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [fr] French, low, m4a_dash
139-5   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [ja] Japanese, low, m4a_dash
139-6   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [it] Italian, low, m4a_dash
139-7   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [es] Spanish, low, m4a_dash
139-8   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [id] Indonesian, low, m4a_dash
139-9   m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [pt] Portuguese, low, m4a_dash
139-10  m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [ar] Arabic, low, m4a_dash
139-11  m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [pl] Polish, low, m4a_dash
139-12  m4a   audio only      2 │   33.47MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, m4a_dash
249-0   webm  audio only      2 │   31.82MiB   46k https │ audio only          opus        46k 48k [zh] Chinese, low, webm_dash
249-1   webm  audio only      2 │   32.20MiB   47k https │ audio only          opus        47k 48k [es] Spanish, low, webm_dash
249-2   webm  audio only      2 │   32.21MiB   47k https │ audio only          opus        47k 48k [fr] French, low, webm_dash
249-3   webm  audio only      2 │   32.23MiB   47k https │ audio only          opus        47k 48k [nl] Dutch, low, webm_dash
249-4   webm  audio only      2 │   32.26MiB   47k https │ audio only          opus        47k 48k [pl] Polish, low, webm_dash
249-5   webm  audio only      2 │   32.28MiB   47k https │ audio only          opus        47k 48k [hi] Hindi, low, webm_dash
249-6   webm  audio only      2 │   32.32MiB   47k https │ audio only          opus        47k 48k [it] Italian, low, webm_dash
249-7   webm  audio only      2 │   32.34MiB   47k https │ audio only          opus        47k 48k [pt] Portuguese, low, webm_dash
249-8   webm  audio only      2 │   32.39MiB   47k https │ audio only          opus        47k 48k [ar] Arabic, low, webm_dash
249-9   webm  audio only      2 │   32.43MiB   47k https │ audio only          opus        47k 48k [id] Indonesian, low, webm_dash
249-10  webm  audio only      2 │   32.47MiB   47k https │ audio only          opus        47k 48k [de] German, low, webm_dash
249-11  webm  audio only      2 │   32.56MiB   47k https │ audio only          opus        47k 48k [ja] Japanese, low, webm_dash
250-0   webm  audio only      2 │   45.29MiB   66k https │ audio only          opus        66k 48k [zh] Chinese, low, webm_dash
250-1   webm  audio only      2 │   46.93MiB   68k https │ audio only          opus        68k 48k [fr] French, low, webm_dash
250-2   webm  audio only      2 │   47.14MiB   69k https │ audio only          opus        69k 48k [nl] Dutch, low, webm_dash
250-3   webm  audio only      2 │   47.18MiB   69k https │ audio only          opus        69k 48k [es] Spanish, low, webm_dash
250-4   webm  audio only      2 │   47.19MiB   69k https │ audio only          opus        69k 48k [ar] Arabic, low, webm_dash
250-5   webm  audio only      2 │   47.25MiB   69k https │ audio only          opus        69k 48k [de] German, low, webm_dash
250-6   webm  audio only      2 │   47.49MiB   69k https │ audio only          opus        69k 48k [hi] Hindi, low, webm_dash
250-7   webm  audio only      2 │   47.54MiB   69k https │ audio only          opus        69k 48k [pt] Portuguese, low, webm_dash
250-8   webm  audio only      2 │   47.64MiB   69k https │ audio only          opus        69k 48k [pl] Polish, low, webm_dash
250-9   webm  audio only      2 │   47.86MiB   70k https │ audio only          opus        70k 48k [it] Italian, low, webm_dash
250-10  webm  audio only      2 │   48.02MiB   70k https │ audio only          opus        70k 48k [ja] Japanese, low, webm_dash
250-11  webm  audio only      2 │   49.04MiB   71k https │ audio only          opus        71k 48k [id] Indonesian, low, webm_dash
249-12  webm  audio only      2 │   34.21MiB   50k https │ audio only          opus        50k 48k [en] English original (default), low, webm_dash
250-12  webm  audio only      2 │   44.87MiB   65k https │ audio only          opus        65k 48k [en] English original (default), low, webm_dash
140-drc m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, DRC, m4a_dash
251-drc webm  audio only      2 │   77.93MiB  114k https │ audio only          opus       114k 48k [en] English original (default), medium, DRC, webm_dash
140-0   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [ar] Arabic, medium, m4a_dash
140-1   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [de] German, medium, m4a_dash
140-2   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [es] Spanish, medium, m4a_dash
140-3   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [fr] French, medium, m4a_dash
140-4   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [hi] Hindi, medium, m4a_dash
140-5   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [id] Indonesian, medium, m4a_dash
140-6   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [it] Italian, medium, m4a_dash
140-7   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [ja] Japanese, medium, m4a_dash
140-8   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [nl] Dutch, medium, m4a_dash
140-9   m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [pl] Polish, medium, m4a_dash
140-10  m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [pt] Portuguese, medium, m4a_dash
140-11  m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [zh] Chinese, medium, m4a_dash
140-12  m4a   audio only      2 │   88.83MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, m4a_dash
251-0   webm  audio only      2 │   86.74MiB  126k https │ audio only          opus       126k 48k [zh] Chinese, medium, webm_dash
251-1   webm  audio only      2 │   90.19MiB  131k https │ audio only          opus       131k 48k [fr] French, medium, webm_dash
251-2   webm  audio only      2 │   90.33MiB  132k https │ audio only          opus       132k 48k [nl] Dutch, medium, webm_dash
251-3   webm  audio only      2 │   90.54MiB  132k https │ audio only          opus       132k 48k [ar] Arabic, medium, webm_dash
251-4   webm  audio only      2 │   90.73MiB  132k https │ audio only          opus       132k 48k [es] Spanish, medium, webm_dash
251-5   webm  audio only      2 │   91.01MiB  133k https │ audio only          opus       133k 48k [de] German, medium, webm_dash
251-6   webm  audio only      2 │   91.41MiB  133k https │ audio only          opus       133k 48k [ja] Japanese, medium, webm_dash
251-7   webm  audio only      2 │   91.47MiB  133k https │ audio only          opus       133k 48k [pt] Portuguese, medium, webm_dash
251-8   webm  audio only      2 │   91.49MiB  133k https │ audio only          opus       133k 48k [hi] Hindi, medium, webm_dash
251-9   webm  audio only      2 │   92.04MiB  134k https │ audio only          opus       134k 48k [it] Italian, medium, webm_dash
251-10  webm  audio only      2 │   92.08MiB  134k https │ audio only          opus       134k 48k [pl] Polish, medium, webm_dash
251-11  webm  audio only      2 │   94.92MiB  138k https │ audio only          opus       138k 48k [id] Indonesian, medium, webm_dash
251-12  webm  audio only      2 │   77.86MiB  113k https │ audio only          opus       113k 48k [en] English original (default), medium, webm_dash
160     mp4   256x144     25    │   25.43MiB   37k https │ avc1.4d400c     37k video only          144p, mp4_dash
278     webm  256x144     25    │   46.29MiB   67k https │ vp9             67k video only          144p, webm_dash
394     mp4   256x144     25    │   35.32MiB   51k https │ av01.0.00M.08   51k video only          144p, mp4_dash
133     mp4   426x240     25    │   49.59MiB   72k https │ avc1.4d4015     72k video only          240p, mp4_dash
242     webm  426x240     25    │   60.77MiB   89k https │ vp9             89k video only          240p, webm_dash
395     mp4   426x240     25    │   51.54MiB   75k https │ av01.0.00M.08   75k video only          240p, mp4_dash
134     mp4   640x360     25    │   92.39MiB  135k https │ avc1.4d401e    135k video only          360p, mp4_dash
18      mp4   640x360     25  2 │  273.72MiB  399k https │ avc1.42001E         mp4a.40.2       44k [en] 360p
243     webm  640x360     25    │  130.80MiB  191k https │ vp9            191k video only          360p, webm_dash
396     mp4   640x360     25    │   92.28MiB  135k https │ av01.0.01M.08  135k video only          360p, mp4_dash
135     mp4   854x480     25    │  154.41MiB  225k https │ avc1.4d401e    225k video only          480p, mp4_dash
244     webm  854x480     25    │  204.19MiB  298k https │ vp9            298k video only          480p, webm_dash
397     mp4   854x480     25    │  156.37MiB  228k https │ av01.0.04M.08  228k video only          480p, mp4_dash
136     mp4   1280x720    25    │  251.22MiB  366k https │ avc1.4d401f    366k video only          720p, mp4_dash
247     webm  1280x720    25    │  388.59MiB  566k https │ vp9            566k video only          720p, webm_dash
398     mp4   1280x720    25    │  283.02MiB  413k https │ av01.0.05M.08  413k video only          720p, mp4_dash
137     mp4   1920x1080   25    │  878.26MiB 1280k https │ avc1.640028   1280k video only          1080p, mp4_dash
248     webm  1920x1080   25    │  691.84MiB 1008k https │ vp9           1008k video only          1080p, webm_dash
399     mp4   1920x1080   25    │  494.97MiB  721k https │ av01.0.08M.08  721k video only          1080p, mp4_dash
271     webm  2560x1440   25    │    1.74GiB 2590k https │ vp9           2590k video only          1440p, webm_dash
400     mp4   2560x1440   25    │    1.46GiB 2178k https │ av01.0.12M.08 2178k video only          1440p, mp4_dash
313     webm  3840x2160   25    │    4.81GiB 7186k https │ vp9           7186k video only          2160p, webm_dash
401     mp4   3840x2160   25    │    2.74GiB 4083k https │ av01.0.12M.08 4083k video only          2160p, mp4_dash
```

---

---

---

---

🔥 Maybe we can create a new api endpoint and service to make a quick request to "yt-dlp" api to check for available audio tracks in the specified video url, before actially downloading the audio file.

In the case of the "add episode from youtube video", it is easy to add a new step in the multi-step modal and the workflow in which we can make a quick request to "yt-dlp" api to check for available audio tracks in the specified video url, before actially downloading the audio file. The process can be like this:

- we enter the youtube video url
- we click the "Add episode" button
- we wait for the system to analyze the video and return the available audio tracks and the metadata of the video
- we present the metadata of the video and the available audio tracks to the user to review and select the audio track we want to download
- we click the "download" button
- we wait for the system to download the audio file in the specified language
- we click the "create episode" button
- we wait for the system to create the episode
- we click the "save" button

where we can make a quick request to "yt-dlp" api to check for available audio tracks in the specified video url, before actially downloading the audio file.

download the audio file in the specified language. This way we can avoid the problem of the audio file being downloaded in the original language.

✅ What we CAN do (best practice) to get the available audio tracks for a given video url

First: inspect the video to list available audio tracks using:

```bash
yt-dlp -F --print formats VIDEO_URL
```

This prints all audio formats and their languages. Example output snippet:

```bash
251          webm      audio only  en
251/es       webm      audio only  es
251/fr       webm      audio only  fr
```

If the selected language (e.g. Spanish) exists, we can download it. If not, we can download the audio file in the default language.

⸻

Summary of the workflow to download the audio file in the specified language. The backend logic should:

In quick add modal, the workflow should be:

1. Check the selected language of the user in the settings (by default it should be set to "original" unless the user has changed it), and use it to load the pre-loaded language in the modal form.
2. If the user does not select another language in the modal, this means we should try to download the audio file in the language selected in the settings (by default it should be set to "original" unless the user has changed it).
3. If the user selects a different language from the one selected in the settings in the modal, we should try to download the audio file in the selected language in the modal.
4. The backend logic should detect all available audio track languages for the given video url and download the audio file in the selected language accordingly.

   1. Detect all available audio track languages.
   2. If user’s selected language exists → download that audio.
   3. If not → either:
      • download another default language (e.g., English), or
      • return an error / fallback message.

      1.1 Download the audio file in the language selected in the settings.
      1.2 Return a mesage that can be displayed in a toast message in the frontent "The audio file is being downloaded in the LANGUAGE_SELECTED".
      2.1 Detect all available audio track languages for the given video url.
      2.2 If the selected language (e.g. Spanish) exists, download the audio file in that language.
      2.3 If the selected language does not exist, download the audio file in the "original" language.

yt-dlp -F --print formats https://www.youtube.com/watch?v=hQaN5w3YwtM
yt-dlp -F --print formats 'https://www.youtube.com/watch?v=hQaN5w3YwtM'

1. ✅ 1. Get only audio tracks with their languages (much shorter list)

Use the --print fields to extract only what you want:

yt-dlp -F --match-filter "acodec!^$" --print "%id %language" "https://www.youtube.com/watch?v=hQaN5w3YwtM"

2. ✅ 2. Get a list of unique languages available

yt-dlp -F --match-filter "acodec!^$" --print "%language" "URL" | sort -u

3. ✅ 3. Check if a specific language is available

Example: check for Spanish (es):

yt-dlp -F --match-filter "acodec!^$ & language=es" --print "%id %language %abr" "URL"

4. ✅ 4. Automatically download best audio track for a specific language

This is the cleanest way to do the actual download:

yt-dlp -f "ba[language=es]" -o "%(title)s.%(ext)s" "URL"

What it does:
• ba = best audio
• [language=es] = filter by language

If Spanish isn’t available, yt-dlp will fail unless you provide a fallback:

yt-dlp -f "ba[language=es]/ba" "URL"

➡️ This tries: 1. Best audio in Spanish 2. If not available → best audio in any language

⭐️ Best approach for your planned feature (“Preferred Language”):

1. On video import:

Get available languages:

yt-dlp -F --match-filter "acodec!^$" --print "%language" URL | sort -u

Store this list per video.

2. When downloading:

Use:

yt-dlp -f "ba[language=<user_pref>]/ba" URL

3. If preferred not available:

Detect from empty output or rely on fallback.

'https://www.youtube.com/watch?v=hQaN5w3YwtM'
yt-dlp -F --match-filter "acodec!^$" --print "%language" 'https://www.youtube.com/watch?v=hQaN5w3YwtM' | sort -u

yt-dlp -F --match-filter "acodec!^$ & language=es" --print "%id %language %abr" 'https://www.youtube.com/watch?v=hQaN5w3YwtM'

yt-dlp -O "%(formats[?language=='es'] | best_audio.format_id)s" 'https://www.youtube.com/watch?v=hQaN5w3YwtM'

yt-dlp -O "%(formats[?language=='es'].acodec)s" 'https://www.youtube.com/watch?v=hQaN5w3YwtM'

yt-dlp -j "https://www.youtube.com/watch?v=hQaN5w3YwtM" | jq -r '.formats[] | select(.acodec != "none" and (.language == "es")) | .format_id'

yt-dlp -F "https://www.youtube.com/watch?v=hQaN5w3YwtM"

yt-dlp -F "https://www.youtube.com/watch?v=qxxnRMT9C-8"
[info] Available formats for qxxnRMT9C-8:
ID EXT RESOLUTION FPS CH │ FILESIZE TBR PROTO │ VCODEC VBR ACODEC ABR ASR MORE INFO
139-2 m4a audio only 2 │ 47.96MiB 49k https │ audio only mp4a.40.5 49k 22k [es] Spanish, low, m4a_dash
249-7 webm audio only 2 │ 48.24MiB 49k https │ audio only opus 49k 48k [es] Spanish, low, webm_dash
140-2 m4a audio only 2 │ 127.28MiB 129k https │ audio only mp4a.40.2 129k 44k [es] Spanish, medium, m4a_dash
251-6 webm audio only 2 │ 137.73MiB 140k https │ audio only opus 140k 48k [es] Spanish, medium, webm_dash

yt-dlp -F "https://www.youtube.com/watch?v=hQaN5w3YwtM"

2025-12-08 15:42:25.219 | {"timestamp": "2025-12-08T15:42:25", "level": "INFO", "logger": "labcastarr.downloader", "function": "\_log_available_formats", "line": 345, "message": "Using format string: bestaudio[language=es][ext=m4a]/bestaudio[language=es][ext=mp3]/bestaudio[language=es]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]"}

"Using format string: bestaudio[language=es][ext=m4a]/bestaudio[language=es][ext=mp3]/bestaudio[language=es]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]"}
