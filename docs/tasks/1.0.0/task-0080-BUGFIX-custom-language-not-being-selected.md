# Task 0080: BUGFIX - Custom Language Audio: Not being selected

- Session File: @task-0080-BUGFIX-custom-language-not-being-selected-full-session-1.md
- IDE: Claude Code
- Date: 2026-02-09
- Model: Claude Opus 4.5

---

## Prompt (Plan Mode)

I need you to take the job seriously and fix an issue that we have been back and forth consuming my money for the last few days. As a senior software engineer, you should be able to identify the root cause of the issue and build a robust system.

We have implemented a new feature that allows the user to download the audio file of a youtube video in a different language than the original/default audio track of a Youtube video. The feature allows the user to select the language and a preffered quality for the audio file to download for a video. The feature is working partially, we are having trouble selecting the correct audio track in the specified language/quazlity to then download the audio file.

The creation of the episode is erroring out and not even falling back to download the default audio track as expected.

We will use the following video during the test:

- Video URL: https://www.youtube.com/watch?v=0t_DD5568RA
- Language: Spanish
- Quality: low

## The expected behavior

The feature shoudl work when the user creates a new episode with the "quick add" modal, or the "add episode from youtube video" multi-step form, or the uses "create episode" option from video cards of followed channels".

Let's describe the expected behavior step by step, for the quick add modal. The workflow is easy:

1. The user opens the "quick add" modal.
2. The user provides a youtube video url
3. The user can select a checkbox "Custom audio options" that makes visible two options:

- an option to select the language (right now only english and spanish)
- and an option to select the preffered quality of the audio file to download for the video (low: up to 70kbps, medium: 70kbps to 150kbps, high: more than 150kbps).

4. The user selects "Add Episode" button.
5. The system fetches the metadata of the video from youtube using the yt-dlp library.
6. The system identifies ALL available audio tracks for the video using the yt-dlp library.
7. The system identifies the audio track to download according to:
   1. first by the specified language if available. If the language is not available on any quality, then it should fall back to download the audio file in the original language and quality.
   2. then by language and preffered quality if available. If the language is available on the preffered quality, then it should download the audio file in the specified language and quality. If the language is not available on the preffered quality, then it should download the audio file in the best quality available for the language.
8. With the result of the selection, the system then downloads the audio file in the selected language/quality of the previous stepusing the yt-dlp library.
9. If needed, the system uses ffmpeg for post-processing the audio file to the format of the episode.

I identify the following processes:

- fetch_video_metadata: responsible for fetching the metadata of the video from youtube using the yt-dlp library.
- identify_available_audio_tracks: responsible for identifying the available audio tracks in the specified language/quality using the yt-dlp library.
- select_audio_track: responsible for selecting the audio track in the specified language/quality using the yt-dlp library.
- download_audio_file: responsible for downloading the audio file in the specified language/quality.
- post_process_audio_file: responsible for post-processing the audio file to the format of the episode if needed.
- create_episode: responsible for creating the episode with the audio file downloaded.
- save_episode: responsible for saving the episode to the database.
- events_handler: responsible for generating events of the process.
- notify_user: responsible for notifying the user of the event of the download process.

## Important considerations

It is important that we:

1. get all the audio tracks available for the video using the yt-dlp library.
2. process the output of the operation to get all tracks available. VERY IMPORTANT TO CORRECTLY IDENTIFY/PARSE THE ID OF THE AUDIO TRACK RIGHT FROM THE RESPONSE OF THE YT-DLP LIBRARY (COMMAND: yt-dlp --list-formats "URL").
3. identify the ID of the audio track that we need to send to the yt-dlp library to download according to the specified language/quality
4. download the audio file in the selected language/quality using the yt-dlp library (COMMAND: `yt-dlp -f SELECTED_TRACK_ID --extract-audio --audio-format m4a "VIDEO_URL"`).
5. Handle errors and exceptions that may occur during the process.
6. Fall back to download the audio file in the original language/quality if the specified language/quality is not available.
7. Post-process the audio file to the format of the episode if needed.
8. the UI in the frontend should show the progress of the download process, and the status of the download process.
9. the ui will show a tag with the language code of the downloaded audio file (eg: "es" for spanish, "en" for english, etc.) in the episode card and in the episode details page. In the episode details page, we will also show thae quality of the downloadedaudio file (low, medium, high).

Also important is to make sure that we use the latest version of the yt-dlp library in the docker container of the backend.

Let's separate responsabilities by processes above and log the results of each process, to clearly see what we passed as input and what we got as output, to identify the root cause of the issue.

## Possible root causes (but i want you to explore and analyze all possible causes):

I think that the problem can be (not limited to):

### Problem realted to the call we are making in code to the yt-dlp library to get all the audio tracks available for the video

Either because:

1. the call we are making in code to the yt-dlp library to get all the audio tracks available for the video is not responding with the same output as when we use the yt-dlp library directly from the macos terminal.
2. or we are parsing the output of the operation to get all tracks available, and we are generating incorrect data, specially not correctlyidentifying the ID of the audio track that we need to send to the yt-dlp library to download according to the specified language/quality.

### Problem related to language only available for video tracks, not for audio tracks

In this case, which is the case of the example video, we have tracks available in spanish with arious qualities. In this case we should download one of these options and extract the audio track from the video file. The problem is that they are not audio tracks, they are video tracks. In this case spanish audio exists ONLY inside muxed HLS video formats. Threfore we need to download the video track and extract the audio track from it.

We can do this by:

1. Option 1 (THE WAY TO GO!!!). Since we are already using yt-dlp, this is often the cleanest and better way to download the audio file, which avoids extra steps entirely: download the Spanish audio-only format directly using yt-dlp options. We simply need the ID of the audio track that we want to download id=91-0 lowest quality 141kbps.

With this option we could simply use `yt-dlp -f SELECTED_TRACK_ID --extract-audio --audio-format m4a "VIDEO_URL"`. In our example:

```bash
yt-dlp -f 91-0 --extract-audio --audio-format m4a "https://www.youtube.com/watch?v=0t_DD5568RA"
```

This will download the audio file in the specified language/quality using the yt-dlp library.

1. Option 2 (ony as reference): If we download an MP4 video that already contains Spanish audio, we can use ffmpeg to extract the audio cleanly (no re-encoding if you want). We can extract audio without re-encoding (fast, lossless). If the audio inside the MP4 is eg: "AAC" (which it usually is on YouTube):
   `ffmpeg -i input.mp4 -vn -acodec copy output.m4a`

### Logs of yt-dlp library from the macos terminal

If I use the yt-dlp library directly from the macos terminal, i can see the available audio tracks for the video. As you can see, there are audio tracks available in the specified language/quality to download the audio file for the example video.

```bash
 yt-dlp --list-formats "https://www.youtube.com/watch?v=0t_DD5568RA"

[youtube] Extracting URL: https://www.youtube.com/watch?v=0t_DD5568RA
[youtube] 0t_DD5568RA: Downloading webpage
[youtube] 0t_DD5568RA: Downloading android vr player API JSON
[youtube] 0t_DD5568RA: Downloading web safari player API JSON
[youtube] 0t_DD5568RA: Downloading player 4e51e895-tv
[youtube] [jsc:deno] Solving JS challenges using deno
[youtube] 0t_DD5568RA: Downloading m3u8 information
[info] Available formats for 0t_DD5568RA:
ID    EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb3   mhtml 48x27        0    │                  mhtml │ images                                  storyboard
sb2   mhtml 80x45        0    │                  mhtml │ images                                  storyboard
sb1   mhtml 160x90       0    │                  mhtml │ images                                  storyboard
sb0   mhtml 320x180      0    │                  mhtml │ images                                  storyboard
139   m4a   audio only      2 │   43.70MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, m4a_dash
249   webm  audio only      2 │   44.76MiB   50k https │ audio only          opus        50k 48k [en] English original (default), low, webm_dash
140   m4a   audio only      2 │  115.97MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, m4a_dash
251   webm  audio only      2 │  100.23MiB  112k https │ audio only          opus       112k 48k [en] English original (default), medium, webm_dash
91-0  mp4   256x144     25    │ ~126.29MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [es]
91-1  mp4   256x144     25    │ ~126.30MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [ar]
91-2  mp4   256x144     25    │ ~126.33MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [fr]
91-3  mp4   256x144     25    │ ~126.33MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [en]
91-4  mp4   256x144     25    │ ~126.34MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [ro]
91-5  mp4   256x144     25    │ ~126.37MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [ja]
91-6  mp4   256x144     25    │ ~126.37MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [id]
91-7  mp4   256x144     25    │ ~126.37MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [zh-Hans]
91-8  mp4   256x144     25    │ ~126.38MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [ko]
91-9  mp4   256x144     25    │ ~126.38MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [pl]
91-10 mp4   256x144     25    │ ~126.40MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [pt]
91-11 mp4   256x144     25    │ ~126.41MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [de]
91-12 mp4   256x144     25    │ ~126.41MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [hi]
91-13 mp4   256x144     25    │ ~126.42MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [it]
91-14 mp4   256x144     25    │ ~126.33MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [en] (original)
160   mp4   256x144     25    │   24.56MiB   27k https │ avc1.4d400c     27k video only          144p, mp4_dash
278   webm  256x144     25    │   70.71MiB   79k https │ vp9             79k video only          144p, webm_dash
394   mp4   256x144     25    │   35.72MiB   40k https │ av01.0.00M.08   40k video only          144p, mp4_dash
92-0  mp4   426x240     25    │ ~183.47MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [es]
92-1  mp4   426x240     25    │ ~183.48MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [ar]
92-2  mp4   426x240     25    │ ~183.51MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [fr]
92-3  mp4   426x240     25    │ ~183.51MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [en]
92-4  mp4   426x240     25    │ ~183.52MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [ro]
92-5  mp4   426x240     25    │ ~183.54MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [ja]
92-6  mp4   426x240     25    │ ~183.55MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [id]
92-7  mp4   426x240     25    │ ~183.55MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [zh-Hans]
92-8  mp4   426x240     25    │ ~183.56MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [ko]
92-9  mp4   426x240     25    │ ~183.56MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [pl]
92-10 mp4   426x240     25    │ ~183.58MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [pt]
92-11 mp4   426x240     25    │ ~183.59MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [de]
92-12 mp4   426x240     25    │ ~183.59MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [hi]
92-13 mp4   426x240     25    │ ~183.60MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [it]
92-14 mp4   426x240     25    │ ~183.51MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [en] (original)
133   mp4   426x240     25    │   45.99MiB   51k https │ avc1.4d4015     51k video only          240p, mp4_dash
242   webm  426x240     25    │   80.92MiB   90k https │ vp9             90k video only          240p, webm_dash
395   mp4   426x240     25    │   54.60MiB   61k https │ av01.0.00M.08   61k video only          240p, mp4_dash
93-0  mp4   640x360     25    │ ~361.21MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [ar]
93-1  mp4   640x360     25    │ ~361.23MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [fr]
93-2  mp4   640x360     25    │ ~361.23MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [pl]
93-3  mp4   640x360     25    │ ~361.25MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [hi]
93-4  mp4   640x360     25    │ ~361.28MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [en]
93-5  mp4   640x360     25    │ ~361.29MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
93-6  mp4   640x360     25    │ ~361.30MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [pt]
93-7  mp4   640x360     25    │ ~361.32MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [id]
93-8  mp4   640x360     25    │ ~361.33MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [it]
93-9  mp4   640x360     25    │ ~361.35MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [zh-Hans]
93-10 mp4   640x360     25    │ ~361.37MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [ro]
93-11 mp4   640x360     25    │ ~361.38MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [ja]
93-12 mp4   640x360     25    │ ~361.38MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [de]
93-13 mp4   640x360     25    │ ~361.43MiB  404k m3u8  │ avc1.4D401E         mp4a.40.2           [ko]
93-14 mp4   640x360     25    │ ~361.28MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [en] (original)
134   mp4   640x360     25    │   84.53MiB   94k https │ avc1.4d401e     94k video only          360p, mp4_dash
18    mp4   640x360     25  2 │  323.36MiB  361k https │ avc1.42001E         mp4a.40.2       44k [en] 360p
243   webm  640x360     25    │  137.82MiB  154k https │ vp9            154k video only          360p, webm_dash
396   mp4   640x360     25    │  100.25MiB  112k https │ av01.0.01M.08  112k video only          360p, mp4_dash
94-0  mp4   854x480     25    │ ~650.50MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [ar]
94-1  mp4   854x480     25    │ ~650.53MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [fr]
94-2  mp4   854x480     25    │ ~650.53MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [pl]
94-3  mp4   854x480     25    │ ~650.55MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [hi]
94-4  mp4   854x480     25    │ ~650.57MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [en]
94-5  mp4   854x480     25    │ ~650.59MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
94-6  mp4   854x480     25    │ ~650.60MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [pt]
94-7  mp4   854x480     25    │ ~650.62MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [id]
94-8  mp4   854x480     25    │ ~650.63MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [it]
94-9  mp4   854x480     25    │ ~650.64MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [zh-Hans]
94-10 mp4   854x480     25    │ ~650.67MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [ro]
94-11 mp4   854x480     25    │ ~650.68MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [ja]
94-12 mp4   854x480     25    │ ~650.68MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [de]
94-13 mp4   854x480     25    │ ~650.73MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [ko]
94-14 mp4   854x480     25    │ ~650.57MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [en] (original)
135   mp4   854x480     25    │  130.62MiB  146k https │ avc1.4d401e    146k video only          480p, mp4_dash
244   webm  854x480     25    │  211.33MiB  236k https │ vp9            236k video only          480p, webm_dash
397   mp4   854x480     25    │  144.19MiB  161k https │ av01.0.04M.08  161k video only          480p, mp4_dash
95-0  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [ar]
95-1  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [fr]
95-2  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [pl]
95-3  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [hi]
95-4  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [en]
95-5  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [es]
95-6  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [pt]
95-7  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [id]
95-8  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [it]
95-9  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [zh-Hans]
95-10 mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [ro]
95-11 mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [ja]
95-12 mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [de]
95-13 mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [ko]
95-14 mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [en] (original)
136   mp4   1280x720    25    │  196.60MiB  219k https │ avc1.4d401f    219k video only          720p, mp4_dash
247   webm  1280x720    25    │  386.44MiB  431k https │ vp9            431k video only          720p, webm_dash
398   mp4   1280x720    25    │  252.76MiB  282k https │ av01.0.05M.08  282k video only          720p, mp4_dash
96-0  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [ar]
96-1  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [fr]
96-2  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [pl]
96-3  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [hi]
96-4  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [en]
96-5  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [es]
96-6  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [pt]
96-7  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [id]
96-8  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [it]
96-9  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [zh-Hans]
96-10 mp4   1920x1080   25    │ ~  2.08GiB 2375k m3u8  │ avc1.640028         mp4a.40.2           [ro]
96-11 mp4   1920x1080   25    │ ~  2.08GiB 2375k m3u8  │ avc1.640028         mp4a.40.2           [ja]
96-12 mp4   1920x1080   25    │ ~  2.08GiB 2375k m3u8  │ avc1.640028         mp4a.40.2           [de]
96-13 mp4   1920x1080   25    │ ~  2.08GiB 2375k m3u8  │ avc1.640028         mp4a.40.2           [ko]
96-14 mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [en] (original)
137   mp4   1920x1080   25    │  790.58MiB  883k https │ avc1.640028    883k video only          1080p, mp4_dash
248   webm  1920x1080   25    │  713.26MiB  796k https │ vp9            796k video only          1080p, webm_dash
399   mp4   1920x1080   25    │  390.48MiB  436k https │ av01.0.08M.08  436k video only          1080p, mp4_dash
271   webm  2560x1440   25    │    2.12GiB 2425k https │ vp9           2425k video only          1440p, webm_dash
400   mp4   2560x1440   25    │  972.22MiB 1085k https │ av01.0.12M.08 1085k video only          1440p, mp4_dash
313   webm  3840x2160   25    │    6.64GiB 7589k https │ vp9           7589k video only          2160p, webm_dash
401   mp4   3840x2160   25    │    1.95GiB 2225k https │ av01.0.12M.08 2225k video only          2160p, mp4_dash
```

With this information, we can see that we have at least the following audio tracks available in spanish. We only have now to pick the quality according the the users preffered quality. As ID, we have to use the first column of the output, the "ID" of the audio track.

```
ID    EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
91-0  mp4   256x144     25    │ ~126.29MiB  141k m3u8  │ avc1.4D400C         mp4a.40.5           [es]
92-0  mp4   426x240     25    │ ~183.47MiB  205k m3u8  │ avc1.4D4015         mp4a.40.5           [es]
93-5  mp4   640x360     25    │ ~361.29MiB  403k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
94-5  mp4   854x480     25    │ ~650.59MiB  726k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
95-5  mp4   1280x720    25    │ ~  1.08GiB 1235k m3u8  │ avc1.4D401F         mp4a.40.2           [es]
96-5  mp4   1920x1080   25    │ ~  2.08GiB 2374k m3u8  │ avc1.640028         mp4a.40.2           [es]
```

In our example, we would have to use the ID "91-0" to download the audio file in the specified language/quality.

We would have to use the following command to download the audio file in the specified language/quality:

```bash
yt-dlp -f "91-0" "https://www.youtube.com/watch?v=0t_DD5568RA"
```

## Celery Worker logs

Below are the full logs of the Celery worker that is responsible for downloading the audio file. As you can see in the logs below, these are the logs of system with all the audio tracks that our current logic has identified after parsing the output of the yt-dlp library to get all tracks available. We can see that it is not selecting the correct audio track in the specified language/quality to then download the audio file.

```bash
[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 11: id=133, ext=mp4, vcodec=avc1.4d4015, acodec=none, abr=0, vbr=51.341, resolution=426x240, fps=25, note=240p, lang=None, protocol=https, filesize=48220402

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 12: id=242, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=90.345, resolution=426x240, fps=25, note=240p, lang=None, protocol=https, filesize=84852508

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 13: id=395, ext=mp4, vcodec=av01.0.00M.08, acodec=none, abr=0, vbr=60.958, resolution=426x240, fps=25, note=240p, lang=None, protocol=https, filesize=57251960

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 14: id=134, ext=mp4, vcodec=avc1.4d401e, acodec=none, abr=0, vbr=94.379, resolution=640x360, fps=25, note=360p, lang=None, protocol=https, filesize=88640792

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 15: id=18, ext=mp4, vcodec=avc1.42001E, acodec=mp4a.40.2, abr=None, vbr=None, resolution=640x360, fps=25, note=360p, lang=en, protocol=https, filesize=339068842

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 16: id=243, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=153.87, resolution=640x360, fps=25, note=360p, lang=None, protocol=https, filesize=144515069

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 17: id=396, ext=mp4, vcodec=av01.0.01M.08, acodec=none, abr=0, vbr=111.927, resolution=640x360, fps=25, note=360p, lang=None, protocol=https, filesize=105122324

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 18: id=135, ext=mp4, vcodec=avc1.4d401e, acodec=none, abr=0, vbr=145.833, resolution=854x480, fps=25, note=480p, lang=None, protocol=https, filesize=136966899

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 19: id=244, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=235.945, resolution=854x480, fps=25, note=480p, lang=None, protocol=https, filesize=221600216

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 20: id=397, ext=mp4, vcodec=av01.0.04M.08, acodec=none, abr=0, vbr=160.986, resolution=854x480, fps=25, note=480p, lang=None, protocol=https, filesize=151198787

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 21: id=136, ext=mp4, vcodec=avc1.4d401f, acodec=none, abr=0, vbr=219.494, resolution=1280x720, fps=25, note=720p, lang=None, protocol=https, filesize=206149376

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 22: id=247, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=431.438, resolution=1280x720, fps=25, note=720p, lang=None, protocol=https, filesize=405206701

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 23: id=398, ext=mp4, vcodec=av01.0.05M.08, acodec=none, abr=0, vbr=282.199, resolution=1280x720, fps=25, note=720p, lang=None, protocol=https, filesize=265041490

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 24: id=137, ext=mp4, vcodec=avc1.640028, acodec=none, abr=0, vbr=882.652, resolution=1920x1080, fps=25, note=1080p, lang=None, protocol=https, filesize=828987459

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 25: id=248, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=796.324, resolution=1920x1080, fps=25, note=1080p, lang=None, protocol=https, filesize=747907842

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 26: id=399, ext=mp4, vcodec=av01.0.08M.08, acodec=none, abr=0, vbr=435.955, resolution=1920x1080, fps=25, note=1080p, lang=None, protocol=https, filesize=409449567

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 27: id=271, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=2425.39, resolution=2560x1440, fps=25, note=1440p, lang=None, protocol=https, filesize=2277926976

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 28: id=400, ext=mp4, vcodec=av01.0.12M.08, acodec=none, abr=0, vbr=1085.439, resolution=2560x1440, fps=25, note=1440p, lang=None, protocol=https, filesize=1019444533

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 29: id=313, ext=webm, vcodec=vp9, acodec=none, abr=0, vbr=7589.291, resolution=3840x2160, fps=25, note=2160p, lang=None, protocol=https, filesize=7127862440

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 30: id=401, ext=mp4, vcodec=av01.0.12M.08, acodec=none, abr=0, vbr=2225.494, resolution=3840x2160, fps=25, note=2160p, lang=None, protocol=https, filesize=2090184078

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] ================================================================================

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Found 5 audio/language formats out of 31 total

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Language 'es' not available, falling back to default

[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format selection: format=249, quality=64kbps, fallback=True

[2026-02-09 17:32:01,436: WARNING/ForkPoolWorker-4] ERROR: [youtube] 0t_DD5568RA: Requested format is not available. Use --list-formats for a list of available formats

[2026-02-09 17:32:01,436: ERROR/ForkPoolWorker-4] Failed to download audio from https://www.youtube.com/watch?v=0t_DD5568RA: ERROR: [youtube] 0t_DD5568RA: Requested format is not available. Use --list-formats for a list of available formats

[2026-02-09 17:32:01,436: ERROR/ForkPoolWorker-4] Download failed for episode 6: Download failed: ERROR: [youtube] 0t_DD5568RA: Requested format is not available. Use --list-formats for a list of available formats

[2026-02-09 17:32:01,440: ERROR/ForkPoolWorker-4] Failed to update episode status after download failure: Can only increment retry count for failed or pending episodes

[2026-02-09 17:32:01,440: INFO/ForkPoolWorker-4] Celery download task completed for episode 6: error

[2026-02-09 17:32:01,441: INFO/ForkPoolWorker-4] Task app.infrastructure.tasks.download_episode_task.download_episode[14aceafd-b773-4e92-8d97-0c8b7bccd625] succeeded in 4.507375251996564s: {'status': 'error', 'episode_id': 6, 'message': 'Download failed: ERROR: [youtube] 0t_DD5568RA: Requested format is not available. Use --list-formats for a list of available formats'}
```

For example, from the logs above, we see that we have data for every audio track available with the following structure, in which the ID is in this example id=133. None of the ids are "91-0" or "94-5", nor the rest of the ids that we have identified as available in the video when we use the yt-dlp library directly from the macos terminal.

```
[2026-02-09 17:31:59,368: INFO/ForkPoolWorker-4] Format 11: id=133, ext=mp4, vcodec=avc1.4d4015, acodec=none, abr=0, vbr=51.341, resolution=426x240, fps=25, note=240p, lang=None, protocol=https, filesize=48220402
```

## Deployment options

Remember that we must rebuild the docker containers to apply the changes in the code using `docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d`.
