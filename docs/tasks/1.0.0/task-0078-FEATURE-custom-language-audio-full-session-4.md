# Prompt: Fix audio language selection and add quality preferences

I have just tested the latest changes by running the app locally with docker (with production configuration) with a video which i know it has various spanish tracks with different audio quality. It did not downloaded spanish version as requested, andd it shows fall back in the thumbnail.

If we use the yt-dlp tool directly on the macos terminal, we also get the follwoing errors, resulting in only being able to download the audio file in the original language (english).

## Test to download the audio file in the specified language

### Test 1: Errors

In the following terminal session i tried to download the audio file in the Spanish language. First i requested the list of all the different qualities available, and then, i tried to download the audio file for spanish in the options available. We always got "ERROR: unable to download video data: HTTP Error 403: Forbidden"

```bash
yt-dlp --list-formats "https://www.youtube.com/watch?v=I_w81rptxkc"
oliver@minio labcastarr % yt-dlp --list-formats "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading tv client config
[youtube] I_w81rptxkc: Downloading player 4e51e895-main
[youtube] I_w81rptxkc: Downloading tv player API JSON
[youtube] I_w81rptxkc: Downloading android sdkless player API JSON
WARNING: [youtube] I_w81rptxkc: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
[info] Available formats for I_w81rptxkc:
ID      EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb3     mhtml 48x27        0    │                  mhtml │ images                                  storyboard
sb2     mhtml 80x45        0    │                  mhtml │ images                                  storyboard
sb1     mhtml 160x90       0    │                  mhtml │ images                                  storyboard
sb0     mhtml 320x180      0    │                  mhtml │ images                                  storyboard
139-drc m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, DRC, m4a_dash
249-drc webm  audio only      2 │   44.02MiB   51k https │ audio only          opus        51k 48k [en] English original (default), low, DRC, webm_dash
139-0   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [ar] Arabic, low, m4a_dash
139-1   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [de] German, low, m4a_dash
139-2   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [es] Spanish, low, m4a_dash
139-3   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [fr] French, low, m4a_dash
139-4   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [hi] Hindi, low, m4a_dash
139-5   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [id] Indonesian, low, m4a_dash
139-6   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [it] Italian, low, m4a_dash
139-7   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [ja] Japanese, low, m4a_dash
139-8   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [nl] Dutch, low, m4a_dash
139-9   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [pl] Polish, low, m4a_dash
139-10  m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [ro] Romanian, low, m4a_dash
139-11  m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [zh-Hans] Chinese (Simplified), low, m4a_dash
139-12  m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [pt] Portuguese, low, m4a_dash
139-13  m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, m4a_dash
249-0   webm  audio only      2 │   41.64MiB   48k https │ audio only          opus        48k 48k [ja] Japanese, low, webm_dash
249-1   webm  audio only      2 │   41.94MiB   49k https │ audio only          opus        49k 48k [zh-Hans] Chinese (Simplified), low, webm_dash
249-2   webm  audio only      2 │   42.23MiB   49k https │ audio only          opus        49k 48k [fr] French, low, webm_dash
249-3   webm  audio only      2 │   42.36MiB   49k https │ audio only          opus        49k 48k [de] German, low, webm_dash
249-4   webm  audio only      2 │   42.41MiB   49k https │ audio only          opus        49k 48k [hi] Hindi, low, webm_dash
249-5   webm  audio only      2 │   42.41MiB   49k https │ audio only          opus        49k 48k [es] Spanish, low, webm_dash
249-6   webm  audio only      2 │   42.48MiB   49k https │ audio only          opus        49k 48k [pt] Portuguese, low, webm_dash
249-7   webm  audio only      2 │   42.57MiB   49k https │ audio only          opus        49k 48k [it] Italian, low, webm_dash
249-8   webm  audio only      2 │   42.64MiB   49k https │ audio only          opus        49k 48k [pl] Polish, low, webm_dash
249-9   webm  audio only      2 │   42.66MiB   49k https │ audio only          opus        49k 48k [ro] Romanian, low, webm_dash
249-10  webm  audio only      2 │   42.67MiB   49k https │ audio only          opus        49k 48k [ar] Arabic, low, webm_dash
249-11  webm  audio only      2 │   42.75MiB   50k https │ audio only          opus        50k 48k [nl] Dutch, low, webm_dash
249-12  webm  audio only      2 │   42.90MiB   50k https │ audio only          opus        50k 48k [id] Indonesian, low, webm_dash
249-13  webm  audio only      2 │   43.93MiB   51k https │ audio only          opus        51k 48k [en] English original (default), low, webm_dash
140-drc m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, DRC, m4a_dash
251-drc webm  audio only      2 │   92.42MiB  107k https │ audio only          opus       107k 48k [en] English original (default), medium, DRC, webm_dash
140-0   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [ar] Arabic, medium, m4a_dash
140-1   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [de] German, medium, m4a_dash
140-2   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [es] Spanish, medium, m4a_dash
140-3   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [fr] French, medium, m4a_dash
140-4   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [hi] Hindi, medium, m4a_dash
140-5   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [id] Indonesian, medium, m4a_dash
140-6   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [it] Italian, medium, m4a_dash
140-7   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [ja] Japanese, medium, m4a_dash
140-8   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [nl] Dutch, medium, m4a_dash
140-9   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [pl] Polish, medium, m4a_dash
140-10  m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [pt] Portuguese, medium, m4a_dash
140-11  m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [ro] Romanian, medium, m4a_dash
140-12  m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [zh-Hans] Chinese (Simplified), medium, m4a_dash
140-13  m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, m4a_dash
251-0   webm  audio only      2 │  106.38MiB  123k https │ audio only          opus       123k 48k [ja] Japanese, medium, webm_dash
251-1   webm  audio only      2 │  114.73MiB  133k https │ audio only          opus       133k 48k [fr] French, medium, webm_dash
251-2   webm  audio only      2 │  115.56MiB  134k https │ audio only          opus       134k 48k [de] German, medium, webm_dash
251-3   webm  audio only      2 │  115.63MiB  134k https │ audio only          opus       134k 48k [es] Spanish, medium, webm_dash
251-4   webm  audio only      2 │  115.64MiB  134k https │ audio only          opus       134k 48k [pt] Portuguese, medium, webm_dash
251-5   webm  audio only      2 │  115.64MiB  134k https │ audio only          opus       134k 48k [zh-Hans] Chinese (Simplified), medium, webm_dash
251-6   webm  audio only      2 │  116.29MiB  135k https │ audio only          opus       135k 48k [ar] Arabic, medium, webm_dash
251-7   webm  audio only      2 │  117.26MiB  136k https │ audio only          opus       136k 48k [pl] Polish, medium, webm_dash
251-8   webm  audio only      2 │  118.21MiB  137k https │ audio only          opus       137k 48k [nl] Dutch, medium, webm_dash
251-9   webm  audio only      2 │  118.38MiB  137k https │ audio only          opus       137k 48k [ro] Romanian, medium, webm_dash
251-10  webm  audio only      2 │  118.50MiB  137k https │ audio only          opus       137k 48k [hi] Hindi, medium, webm_dash
251-11  webm  audio only      2 │  118.64MiB  137k https │ audio only          opus       137k 48k [it] Italian, medium, webm_dash
251-12  webm  audio only      2 │  121.12MiB  140k https │ audio only          opus       140k 48k [id] Indonesian, medium, webm_dash
251-13  webm  audio only      2 │   92.32MiB  107k https │ audio only          opus       107k 48k [en] English original (default), medium, webm_dash
160     mp4   256x144     25    │   29.43MiB   34k https │ avc1.4d400c     34k video only          144p, mp4_dash
278     webm  256x144     25    │   80.38MiB   93k https │ vp9             93k video only          144p, webm_dash
394     mp4   256x144     25    │   39.69MiB   46k https │ av01.0.00M.08   46k video only          144p, mp4_dash
133     mp4   426x240     25    │   55.85MiB   65k https │ avc1.4d4015     65k video only          240p, mp4_dash
242     webm  426x240     25    │   90.20MiB  105k https │ vp9            105k video only          240p, webm_dash
395     mp4   426x240     25    │   60.70MiB   70k https │ av01.0.00M.08   70k video only          240p, mp4_dash
134     mp4   640x360     25    │  114.50MiB  133k https │ avc1.4d401e    133k video only          360p, mp4_dash
18      mp4   640x360     25  2 │  317.79MiB  368k https │ avc1.42001E         mp4a.40.2       44k [en] 360p
243     webm  640x360     25    │  155.53MiB  180k https │ vp9            180k video only          360p, webm_dash
396     mp4   640x360     25    │  112.76MiB  131k https │ av01.0.01M.08  131k video only          360p, mp4_dash
135     mp4   854x480     25    │  197.85MiB  229k https │ avc1.4d401e    229k video only          480p, mp4_dash
244     webm  854x480     25    │  239.58MiB  278k https │ vp9            278k video only          480p, webm_dash
397     mp4   854x480     25    │  163.59MiB  190k https │ av01.0.04M.08  190k video only          480p, mp4_dash
136     mp4   1280x720    25    │  299.97MiB  348k https │ avc1.4d401f    348k video only          720p, mp4_dash
247     webm  1280x720    25    │  437.38MiB  507k https │ vp9            507k video only          720p, webm_dash
398     mp4   1280x720    25    │  293.30MiB  340k https │ av01.0.05M.08  340k video only          720p, mp4_dash
137     mp4   1920x1080   25    │  988.88MiB 1146k https │ avc1.640028   1146k video only          1080p, mp4_dash
248     webm  1920x1080   25    │  903.31MiB 1047k https │ vp9           1047k video only          1080p, webm_dash
399     mp4   1920x1080   25    │  456.36MiB  529k https │ av01.0.08M.08  529k video only          1080p, mp4_dash
271     webm  2560x1440   25    │    2.25GiB 2667k https │ vp9           2667k video only          1440p, webm_dash
400     mp4   2560x1440   25    │    1.13GiB 1346k https │ av01.0.12M.08 1346k video only          1440p, mp4_dash
313     webm  3840x2160   25    │    6.72GiB 7968k https │ vp9           7968k video only          2160p, webm_dash
401     mp4   3840x2160   25    │    2.09GiB 2482k https │ av01.0.12M.08 2482k video only          2160p, mp4_dash
oliver@minio labcastarr % yt-dlp -f 139-2 "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading tv client config
[youtube] I_w81rptxkc: Downloading player 4e51e895-main
[youtube] I_w81rptxkc: Downloading tv player API JSON
[youtube] I_w81rptxkc: Downloading android sdkless player API JSON
WARNING: [youtube] I_w81rptxkc: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
[info] I_w81rptxkc: Downloading 1 format(s): 139-2
[download] Sleeping 6.00 seconds as required by the site...
ERROR: unable to download video data: HTTP Error 403: Forbidden
oliver@minio labcastarr % yt-dlp -f 140-2 "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading tv client config
[youtube] I_w81rptxkc: Downloading player 4e51e895-main
[youtube] I_w81rptxkc: Downloading tv player API JSON
[youtube] I_w81rptxkc: Downloading android sdkless player API JSON
WARNING: [youtube] I_w81rptxkc: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
[info] I_w81rptxkc: Downloading 1 format(s): 140-2
[download] Sleeping 6.00 seconds as required by the site...
ERROR: unable to download video data: HTTP Error 403: Forbidden
oliver@minio labcastarr % yt-dlp -f 251-3 "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading tv client config
[youtube] I_w81rptxkc: Downloading player 4e51e895-main
[youtube] I_w81rptxkc: Downloading tv player API JSON
[youtube] I_w81rptxkc: Downloading android sdkless player API JSON
WARNING: [youtube] I_w81rptxkc: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
[info] I_w81rptxkc: Downloading 1 format(s): 251-3
[download] Sleeping 6.00 seconds as required by the site...
ERROR: unable to download video data: HTTP Error 403: Forbidden
oliver@minio labcastarr % yt-dlp -f 249-5 "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading tv client config
[youtube] I_w81rptxkc: Downloading player 4e51e895-main
[youtube] I_w81rptxkc: Downloading tv player API JSON
[youtube] I_w81rptxkc: Downloading android sdkless player API JSON
WARNING: [youtube] I_w81rptxkc: Some web client https formats have been skipped as they are missing a url. YouTube is forcing SABR streaming for this client. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details
[info] I_w81rptxkc: Downloading 1 format(s): 249-5
[download] Sleeping 5.00 seconds as required by the site...
ERROR: unable to download video data: HTTP Error 403: Forbidden
```

### Test 2: Success

After failing to download the audio file in the specified language, in test 1, i updated `yt-dlp` tool to the latest version with (brew upgrade yt-dlp) and tried to download again the audio file in spanish. First i requested the list of all the different qualities available, which you can see in the following output, follows a different output (different audio id) with the list of all the different qualities available. then i tried to download the audio file for spanish in the options available. We got the following successful output downloading the spanish audio track "91-13":

```bash
oliver@minio labcastarr % yt-dlp -f 249-5 "https://www.youtube.com/watch?v=I_w81rptxkc"
[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading android vr player API JSON
[youtube] I_w81rptxkc: Downloading web safari player API JSON
[youtube] I_w81rptxkc: Downloading player 4e51e895-tv
[youtube] [jsc:deno] Solving JS challenges using deno
[youtube] I_w81rptxkc: Downloading m3u8 information
ERROR: [youtube] I_w81rptxkc: Requested format is not available. Use --list-formats for a list of available formats
oliver@minio labcastarr % yt-dlp --list-formats "https://www.youtube.com/watch?v=I_w81rptxkc"

[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading android vr player API JSON
[youtube] I_w81rptxkc: Downloading web safari player API JSON
[youtube] I_w81rptxkc: Downloading player 4e51e895-tv
[youtube] [jsc:deno] Solving JS challenges using deno
[youtube] I_w81rptxkc: Downloading m3u8 information
[info] Available formats for I_w81rptxkc:
ID    EXT   RESOLUTION FPS CH │   FILESIZE   TBR PROTO │ VCODEC          VBR ACODEC      ABR ASR MORE INFO
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
sb3   mhtml 48x27        0    │                  mhtml │ images                                  storyboard
sb2   mhtml 80x45        0    │                  mhtml │ images                                  storyboard
sb1   mhtml 160x90       0    │                  mhtml │ images                                  storyboard
sb0   mhtml 320x180      0    │                  mhtml │ images                                  storyboard
139   m4a   audio only      2 │   42.10MiB   49k https │ audio only          mp4a.40.5   49k 22k [en] English original (default), low, m4a_dash
249   webm  audio only      2 │   43.93MiB   51k https │ audio only          opus        51k 48k [en] English original (default), low, webm_dash
140   m4a   audio only      2 │  111.74MiB  129k https │ audio only          mp4a.40.2  129k 44k [en] English original (default), medium, m4a_dash
251   webm  audio only      2 │   92.32MiB  107k https │ audio only          opus       107k 48k [en] English original (default), medium, webm_dash
91-0  mp4   256x144     25    │ ~151.73MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [ro]
91-1  mp4   256x144     25    │ ~151.76MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [it]
91-2  mp4   256x144     25    │ ~151.78MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [zh-Hans]
91-3  mp4   256x144     25    │ ~151.81MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [de]
91-4  mp4   256x144     25    │ ~151.81MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [ar]
91-5  mp4   256x144     25    │ ~151.82MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [pl]
91-6  mp4   256x144     25    │ ~151.83MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [hi]
91-7  mp4   256x144     25    │ ~151.83MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [pt]
91-8  mp4   256x144     25    │ ~151.84MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [ja]
91-9  mp4   256x144     25    │ ~151.84MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [id]
91-10 mp4   256x144     25    │ ~151.88MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [nl]
91-11 mp4   256x144     25    │ ~151.91MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [en]
91-12 mp4   256x144     25    │ ~151.92MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [fr]
91-13 mp4   256x144     25    │ ~151.97MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [es]
91-14 mp4   256x144     25    │ ~151.91MiB  176k m3u8  │ avc1.4D400C         mp4a.40.5           [en] (original)
160   mp4   256x144     25    │   29.43MiB   34k https │ avc1.4d400c     34k video only          144p, mp4_dash
278   webm  256x144     25    │   80.38MiB   93k https │ vp9             93k video only          144p, webm_dash
394   mp4   256x144     25    │   39.69MiB   46k https │ av01.0.00M.08   46k video only          144p, mp4_dash
92-0  mp4   426x240     25    │ ~273.18MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [ro]
92-1  mp4   426x240     25    │ ~273.21MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [it]
92-2  mp4   426x240     25    │ ~273.23MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [zh-Hans]
92-3  mp4   426x240     25    │ ~273.26MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [de]
92-4  mp4   426x240     25    │ ~273.27MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [ar]
92-5  mp4   426x240     25    │ ~273.27MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [pl]
92-6  mp4   426x240     25    │ ~273.28MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [hi]
92-7  mp4   426x240     25    │ ~273.28MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [pt]
92-8  mp4   426x240     25    │ ~273.29MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [ja]
92-9  mp4   426x240     25    │ ~273.29MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [id]
92-10 mp4   426x240     25    │ ~273.33MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [nl]
92-11 mp4   426x240     25    │ ~273.36MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [en]
92-12 mp4   426x240     25    │ ~273.37MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [fr]
92-13 mp4   426x240     25    │ ~273.42MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [es]
92-14 mp4   426x240     25    │ ~273.36MiB  317k m3u8  │ avc1.4D4015         mp4a.40.5           [en] (original)
133   mp4   426x240     25    │   55.85MiB   65k https │ avc1.4d4015     65k video only          240p, mp4_dash
242   webm  426x240     25    │   90.20MiB  105k https │ vp9            105k video only          240p, webm_dash
395   mp4   426x240     25    │   60.70MiB   70k https │ av01.0.00M.08   70k video only          240p, mp4_dash
93-0  mp4   640x360     25    │ ~636.63MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [ro]
93-1  mp4   640x360     25    │ ~636.64MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [zh-Hans]
93-2  mp4   640x360     25    │ ~636.65MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [it]
93-3  mp4   640x360     25    │ ~636.67MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [de]
93-4  mp4   640x360     25    │ ~636.70MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [nl]
93-5  mp4   640x360     25    │ ~636.71MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [pt]
93-6  mp4   640x360     25    │ ~636.72MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [ja]
93-7  mp4   640x360     25    │ ~636.76MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [fr]
93-8  mp4   640x360     25    │ ~636.78MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [hi]
93-9  mp4   640x360     25    │ ~636.84MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [pl]
93-10 mp4   640x360     25    │ ~636.85MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [ar]
93-11 mp4   640x360     25    │ ~636.89MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [en]
93-12 mp4   640x360     25    │ ~636.89MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
93-13 mp4   640x360     25    │ ~636.90MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [id]
93-14 mp4   640x360     25    │ ~636.89MiB  738k m3u8  │ avc1.4D401E         mp4a.40.2           [en] (original)
134   mp4   640x360     25    │  114.50MiB  133k https │ avc1.4d401e    133k video only          360p, mp4_dash
18    mp4   640x360     25  2 │  317.79MiB  368k https │ avc1.42001E         mp4a.40.2       44k [en] 360p
243   webm  640x360     25    │  155.53MiB  180k https │ vp9            180k video only          360p, webm_dash
396   mp4   640x360     25    │  112.76MiB  131k https │ av01.0.01M.08  131k video only          360p, mp4_dash
94-0  mp4   854x480     25    │ ~888.91MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [ro]
94-1  mp4   854x480     25    │ ~888.92MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [zh-Hans]
94-2  mp4   854x480     25    │ ~888.93MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [it]
94-3  mp4   854x480     25    │ ~888.95MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [de]
94-4  mp4   854x480     25    │ ~888.98MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [nl]
94-5  mp4   854x480     25    │ ~889.00MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [pt]
94-6  mp4   854x480     25    │ ~889.01MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [ja]
94-7  mp4   854x480     25    │ ~889.05MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [fr]
94-8  mp4   854x480     25    │ ~889.06MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [hi]
94-9  mp4   854x480     25    │ ~889.13MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [pl]
94-10 mp4   854x480     25    │ ~889.14MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [ar]
94-11 mp4   854x480     25    │ ~889.17MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [en]
94-12 mp4   854x480     25    │ ~889.18MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [es]
94-13 mp4   854x480     25    │ ~889.18MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [id]
94-14 mp4   854x480     25    │ ~889.17MiB 1030k m3u8  │ avc1.4D401E         mp4a.40.2           [en] (original)
135   mp4   854x480     25    │  197.85MiB  229k https │ avc1.4d401e    229k video only          480p, mp4_dash
244   webm  854x480     25    │  239.58MiB  278k https │ vp9            278k video only          480p, webm_dash
397   mp4   854x480     25    │  163.59MiB  190k https │ av01.0.04M.08  190k video only          480p, mp4_dash
95-0  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [ro]
95-1  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [zh-Hans]
95-2  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [it]
95-3  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [de]
95-4  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [nl]
95-5  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [pt]
95-6  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [ja]
95-7  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [fr]
95-8  mp4   1280x720    25    │ ~  1.18GiB 1404k m3u8  │ avc1.4D401F         mp4a.40.2           [hi]
95-9  mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [pl]
95-10 mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [ar]
95-11 mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [en]
95-12 mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [es]
95-13 mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [id]
95-14 mp4   1280x720    25    │ ~  1.18GiB 1405k m3u8  │ avc1.4D401F         mp4a.40.2           [en] (original)
136   mp4   1280x720    25    │  299.97MiB  348k https │ avc1.4d401f    348k video only          720p, mp4_dash
247   webm  1280x720    25    │  437.38MiB  507k https │ vp9            507k video only          720p, webm_dash
398   mp4   1280x720    25    │  293.30MiB  340k https │ av01.0.05M.08  340k video only          720p, mp4_dash
96-0  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [ro]
96-1  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [zh-Hans]
96-2  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [it]
96-3  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [de]
96-4  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [nl]
96-5  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [pt]
96-6  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [ja]
96-7  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [fr]
96-8  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [hi]
96-9  mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [pl]
96-10 mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [ar]
96-11 mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [en]
96-12 mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [es]
96-13 mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [id]
96-14 mp4   1920x1080   25    │ ~  3.82GiB 4530k m3u8  │ avc1.640028         mp4a.40.2           [en] (original)
137   mp4   1920x1080   25    │  988.88MiB 1146k https │ avc1.640028   1146k video only          1080p, mp4_dash
248   webm  1920x1080   25    │  903.31MiB 1047k https │ vp9           1047k video only          1080p, webm_dash
399   mp4   1920x1080   25    │  456.36MiB  529k https │ av01.0.08M.08  529k video only          1080p, mp4_dash
271   webm  2560x1440   25    │    2.25GiB 2667k https │ vp9           2667k video only          1440p, webm_dash
400   mp4   2560x1440   25    │    1.13GiB 1346k https │ av01.0.12M.08 1346k video only          1440p, mp4_dash
313   webm  3840x2160   25    │    6.72GiB 7968k https │ vp9           7968k video only          2160p, webm_dash
401   mp4   3840x2160   25    │    2.09GiB 2482k https │ av01.0.12M.08 2482k video only          2160p, mp4_dash


oliver@minio labcastarr % yt-dlp -f 91-13 "https://www.youtube.com/watch?v=I_w81rptxkc"

[youtube] Extracting URL: https://www.youtube.com/watch?v=I_w81rptxkc
[youtube] I_w81rptxkc: Downloading webpage
[youtube] I_w81rptxkc: Downloading android vr player API JSON
[youtube] I_w81rptxkc: Downloading web safari player API JSON
[youtube] I_w81rptxkc: Downloading player 4e51e895-tv
[youtube] [jsc:deno] Solving JS challenges using deno
[youtube] I_w81rptxkc: Downloading m3u8 information
[info] I_w81rptxkc: Downloading 1 format(s): 91-13
[download] Sleeping 4.00 seconds as required by the site...
^[[hlsnative] Downloading m3u8 manifest
[hlsnative] Total fragments: 1393
[download] Destination: Tony Robbins： No One Is Ready For What's Coming (The truth about AI). [I_w81rptxkc].mp4
[download]  13.5% of ~ 111.91MiB at  459.81KiB/s ETA 03:33 (frag 190/1393)[download] Got error: HTTPSConnectionPool(host='rr4---sn-h5q7knez.googlevideo.com', port=443): Read timed out. (read timeout=20.0). Retrying (1/10)...
[download]  57.8% of ~ 111.93MiB at  397.30KiB/s ETA 01:58 (frag 806/1393)[download] Got error: HTTPSConnectionPool(host='rr4---sn-h5q7knez.googlevideo.com', port=443): Read timed out. (read timeout=20.0). Retrying (1/10)...
[download]  74.9% of ~ 112.43MiB at  464.54KiB/s ETA 01:02 (frag 1045/1393)[download] Got error: HTTPSConnectionPool(host='rr4---sn-h5q7knez.googlevideo.com', port=443): Read timed out. (read timeout=20.0). Retrying (1/10)...
[download]  92.8% of ~ 111.44MiB at  465.26KiB/s ETA 00:18 (frag 1293/1393)[download] Got error: HTTPSConnectionPool(host='rr4---sn-h5q7knez.googlevideo.com', port=443): Read timed out. (read timeout=20.0). Retrying (1/10)...
[download] 100% of  110.86MiB in 00:05:33 at 340.35KiB/s
[FixupM3u8] Fixing MPEG-TS in MP4 container of "Tony Robbins： No One Is Ready For What's Coming (The truth about AI). [I_w81rptxkc].mp4"
```

## EXAMPLE DOCUMENTATION: How to test to download the audio file in the specified language

This is a test of the yt-dlp library to download the audio file in the specified language.

### Step 1: List all available audio (and video) formats

To list all available audio (and video) formats - including audio tracks - for that YouTube video using yt-dlp in a macOS Terminal, run this command:

```bash
yt-dlp -F "https://www.youtube.com/watch?v=I_w81rptxkc"
```

or the longer equivalent command:

```bash
yt-dlp --list-formats "https://www.youtube.com/watch?v=I_w81rptxkc"
```

That will print a table showing all available streams (video and audio), with format IDs you can use to pick specific audio tracks for download.

> Tip: Audio-only formats will show up in that list with columns indicating the audio codec, bitrate, etc., and you can then download a specific audio track like this (example format ID 140):

```bash
yt-dlp -f140 https://www.youtube.com/watch?v=I_w81rptxkc
```

### Step 2: Download the audio file in the specified language

To download exactly that Spanish audio track (139-2, m4a, low quality) run:

```bash
yt-dlp -f 139-2"https://www.youtube.com/watch?v=I_w81rptxkc"
```

If you want to control the output filename (optional but handy):

```bash
yt-dlp -f 139-2 -o "%(title)s [es].m4a" "https://www.youtube.com/watch?v=I_w81rptxkc"
```

That will download only the Spanish audio stream, no video attached.

## TASK

After the tests, I thhink that one potential issue might be that we need to update the version we use of `yt-dlp` in the backend or background jobs. There can be other problems that we have to investigate and fix.

---
