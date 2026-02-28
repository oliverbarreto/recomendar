# Task 0055: Refactor new architecture to search for new videos using youtube channel rss feed

- Session File: @task-0056-refactor-new-architecture-to-search-for-new-videos-using-youtube-channel-rss-feed-full-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-28
- Model: Claude Opus 4.5

## Prompt (Plan Mode)

Now that we have a good understanding of the codebase and the architecture after analysing the architecture in the plan document @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md, we want to start the refactoring of the new architecture to search for new videos of a Youtube Followed Channel using the youtube channel rss feed.

Right now we have an option in the context menu of a Followed Youtube Channel card to "search for new videos". When this happens, the system launches a a celery task that uses the `yt-dlp` API to find new videos for the channel.

We want to create a new feature to create a new way of actuallygetting the new videos from a youtube channel. This option consists on using the youtube channel rss feed to search for new videos, instead of using the `yt-dlp` library.

### Problem

In this project, we are using `yt-dlp` library to identify new videos from YouTube channels and also to download metadata of followed YouTube channels.

The problem is that it is too slow checking for new videos in a Youtube Channel is too slow. We need to find a better way to check new videos manually and periodically, and then use `yt-dlp` to conduct an api call to get the full metadata (no media download) for the new videos found.

For this task, we have the following options:

### Solution

API calls to `yt-dlp` library are slow. That's a common issue with screen-scraping tools like `yt-dlp` when checking for new content, as they often have to parse entire channel pages. The most **efficient and recommended** alternatives for quickly identifying new videos are the **YouTube Data API** and **YouTube RSS Feeds**.

We can use these faster methods to get the video IDs of new uploads, and then use `yt-dlp` **only** on those specific new videos to fetch the detailed metadata we need. This hybrid approach drastically reduces the time and resources spent on the periodic check.

#### Options

##### Option 1: YouTube RSS Feeds

Every YouTube channel has an associated RSS feed that lists recent uploads.

**Pros**

- **No API Key/Quota:** It's a simple HTTP request, consuming no YouTube Data API quota.
- **Very Fast:** Retrieving and parsing a small XML/Atom feed is extremely fast.

**Implementation Strategy**

1.  **Generate Feed URL:** The RSS feed URL for a channel is constructed using the channel's ID:
    - `https://www.youtube.com/feeds/videos.xml?channel_id=**YOUR_CHANNEL_ID**`
2.  **Periodic Check (RSS):** Fetch and parse this XML feed. The feed typically contains the **10-15 most recent uploads**. You can extract and quickly compare the video IDs in the feed against a list of the last few videos you've already processed to identify the very latest uploads.

3.  **Full Sweep (yt-dlp):** When new IDs appear → call `yt-dlp` only for those newly identified video IDs for the full metadata retrieval, not the whole channel. This reduces hours of scraping into milliseconds of polling.

**Drawback**

- **Limited History:** The biggest downside is that the RSS feed **only shows the most recent 10-15 videos**. If a channel uploads 20 videos between your checks, you will miss some. This makes the API a more robust option.
- This can be solved by using the `yt-dlp` library to get the metadata for each of the new video IDs found. Even though this option is slower, we should not remove the option to use the `yt-dlp` library to get the metadata for each of the new video IDs found

##### Option 2: Optimize Current `yt-dlp` Usage

If you must stick to `yt-dlp` for the initial check, we can still dramatically speed up the listing process by using specific command-line options.

The slowness comes from `yt-dlp` trying to extract _all_ the video information and, by default, attempting to resolve download formats. You can skip most of this unnecessary work for the check:

| Option                     | Purpose                                                                                                                    |
| :------------------------- | :------------------------------------------------------------------------------------------------------------------------- | ---- |
| **`--flat-playlist`**      | Retrieve only the video titles and IDs from the index (the playlist/channel page). **Crucial for speed.**                  |
| **`--skip-download`**      | Ensures no download streams are initiated or resolved.                                                                     |
| **`--print id`**           | Tells `yt-dlp` to only print the video ID, speeding up the output processing.                                              |
| **`--dateafter YYYYMMDD`** | Only search for videos published after a specific date (in your full sweep command). This can help limit the channel scan. |
| **`<CHANNEL_URL>`**        | The target YouTube channel                                                                                                 | URL. |

**Example optimized command for new video IDs:**

```bash
yt-dlp --flat-playlist --skip-download --dateafter YYYYMMDD --print id <CHANNEL_URL>
```

### Technical considerations

#### RSS/Atom XML feed parsing

Which library should we use to parse the RSS/Atom XML feed? We have various options to choose from: feedparser, lxml, etc.

Since we have lxml already installed, we can use ElementTree-style parsing directly.

You can see a real example of an XML RSS feed for a channel next.

##### Example of a RSS/Atom XML feed

```xml
<RSS EXAMPLE>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
<link rel="self" href="http://www.youtube.com/feeds/videos.xml?channel_id=UCnxubBCPlg0hHdZw_UehrTw"/>
<id>yt:channel:nxubBCPlg0hHdZw_UehrTw</id>
<yt:channelId>nxubBCPlg0hHdZw_UehrTw</yt:channelId>
<title>Rincón de Varo - Hardware & PC Gaming</title>
<link rel="alternate" href="https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw"/>
<author>
<name>Rincón de Varo - Hardware & PC Gaming</name>
<uri>https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw</uri>
</author>
<published>2015-03-22T13:13:17+00:00</published>
<entry>
<id>yt:video:fXx5phQVjr0</id>
<yt:videoId>fXx5phQVjr0</yt:videoId>
<yt:channelId>UCnxubBCPlg0hHdZw_UehrTw</yt:channelId>
<title>TODO lo que TIENDAS y MARCAS de PC Gaming NO quieren que SEPAS</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=fXx5phQVjr0"/>
<author>
<name>Rincón de Varo - Hardware & PC Gaming</name>
<uri>https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw</uri>
</author>
<published>2025-11-27T18:15:07+00:00</published>
<updated>2025-11-28T10:09:50+00:00</updated>
<media:group>
<media:title>TODO lo que TIENDAS y MARCAS de PC Gaming NO quieren que SEPAS</media:title>
<media:content url="https://www.youtube.com/v/fXx5phQVjr0?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i3.ytimg.com/vi/fXx5phQVjr0/hqdefault.jpg" width="480" height="360"/>
<media:description>Whokeys Black Friday Consigue un 25% de descuento con este cupón: RDV ➡️Windows 10 LTSC 2021 IoT Edition (17€): https://es.whokeys.com/wk/Rin10L ➡️Clave OEM de Windows 11 Pro (21€): https://es.whokeys.com/wk/rin5 ➡️Clave OEM de Windows 11 Home (20€) https://es.whokeys.com/wk/rin1h ➡️Windows LTSC 2021 (13€): https://es.whokeys.com/wk/RDVL ➡️Clave OEM de Windows 10 Pro (18€): https://es.whokeys.com/wk/rin1 ➡️Clave OEM de Windows 10 Home (15 €): https://es.whokeys.com/wk/rin2 ➡️Clave de Office 2019 Pro Plus (48€): https://es.whokeys.com/wk/rin3 ➡️Clave de Office 2016 Pro Plus (26€): https://es.whokeys.com/wk/rin7 ➡️Windows 10 Pro +Office 2019 Pro (55€): https://es.whokeys.com/wk/rin4 ➡️Windows 10 Pro +Office 2016 Pro (39€): https://es.whokeys.com/wk/rin6 Compre la CLAVE GLOBAL OEM de MS Win 11 Pro en: https://www.whokeys.com/ Marcas de Tiempo 00:00 Probé todo y hoy te contaré como te manipulan 01:04 La "estafa" del GAMING 03:42 La verdad del PC Preensamblado Vs Pc por piezas 07:28 Comprar por ESTATUS, no por CALIDAD - PRECIO 09:24 El FOMO con las Tarjetas Gráficas 11:44 El 3DVCaché NO ES lo MEJOR (para todos) #pcgamer #pcgaming #noticiaspc</media:description>
<media:community>
<media:starRating count="3797" average="5.00" min="1" max="5"/>
<media:statistics views="39459"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:URrh3PzDO_o</id>
<yt:videoId>URrh3PzDO_o</yt:videoId>
<yt:channelId>UCnxubBCPlg0hHdZw_UehrTw</yt:channelId>
<title>Esta NUEVA CPU GAMING es una ... | Ryzen 5 7500X3D Review</title>
<link rel="alternate" href="https://www.youtube.com/shorts/URrh3PzDO_o"/>
<author>
<name>Rincón de Varo - Hardware & PC Gaming</name>
<uri>https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw</uri>
</author>
<published>2025-11-26T19:45:43+00:00</published>
<updated>2025-11-27T13:57:20+00:00</updated>
<media:group>
<media:title>Esta NUEVA CPU GAMING es una ... | Ryzen 5 7500X3D Review</media:title>
<media:content url="https://www.youtube.com/v/URrh3PzDO_o?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/URrh3PzDO_o/hqdefault.jpg" width="480" height="360"/>
<media:description>¿Vale la pena el Ryzen 5 7500X3D? 🔥 Te cuento por qué este procesador de 6 núcleos y 12 hilos con 96 MB de 3D V-Cache puede ser ideal para gaming — y en qué casos conviene más el Ryzen 7 7800X3D. Comparativa directa: rendimiento, caché, núcleos y relación calidad-precio. ¡No compres sin ver esto! #pcgamer #pcgaming #nvidia</media:description>
<media:community>
<media:starRating count="1272" average="5.00" min="1" max="5"/>
<media:statistics views="23337"/>
</media:community>
</media:group>
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
<entry>
...
</entry>
</feed>
```

#### Celery task implementation

Create a NEW separate Celery task for RSS (keep tasks completely independent). Handle errors appropriately and update the status of the celery task in the database accordingly.

#### New channel workflow

When using the rss feed to search for new videos, we get the last 10/15 videos published only. When we find the first video_id that matches one of the video_ids stored in our database, we exit the search. This might result in various new videos.

However, in the case of a new youtube channel, the first time we use the search using rss feed, it will return all the videos published in the channel, since we have not stored any video_ids for that channel yet. Then the user can use other options to get the rest of the videos published in the channel.

### Goals

The idea is to create a new workflow that uses celery tasks in the background to search for new videos found in a Youtube Channel, based in the current workflow and logic we have implemented, but using the YouTube RSS Feeds to search for new videos, instead of using the `yt-dlp` library.

Evaluate if we might need to refactor and create abstract classes to handle the logic for the new workflow, and pros/cons of each approach. We should reuse as much as possible of the current logic and codebase, and only create the new logic and codebase for the new workflow, but in an isolated way, using clean code practices and a (relaxed version of) Clean Architecture approach.

For this task, you have access to the codebase and the architecture in the plan document @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md and the codebase in the `backend` and `frontend` directories.

I want you to create a phased plan with tasks and sub-tasks to refactor the current implementation and model utilized to implement the "search for new videos" feature to introduce this new workflow.

### Tasks

The tasks that we want to accomplish are the following:

- Rename the current menu option "search for new videos" to "search for recent videos (Slow API)". This button will use the current method and logic to search for new videos using `yt-dlp` library.
- Create a new context menu option in the Followed Youtube Channel card to "search for latest videos (RSS Feed)".
- Create the new functionality, the same structure as the current logic, but now using the YouTube RSS Feeds to search for new videos, instead of using the `yt-dlp` library. This will have to take into account the following:
  - We need to create new code responsible for fetching the Youtube Channel RSS feed, parsing it and returning the list of new video IDs found (see the logic in option 1).
  - Then we still need to use the `yt-dlp` library to get the metadata for each of the new video IDs found, but only for the new video IDs found, not for the whole channel.
  - Then we still need to implement the rest of the work of the current workflow.
  - IMPORTANT: We are only EXTRACTING the way to get the new video IDs from the RSS feed, we are not changing the way to get the metadata for each of the new video IDs found.
  - This might introduce a huge change in the codebase, since `yt-dlp` is used to get all the metadata for each of the new video IDs found, so we need to be careful and not break the current functionality.
  - Create a parallel workflow that will be called from another button, and make this workflow to have separated pieces of responsabilities:
    1. identify the new videos ids: this could use rss feed parsing, or even yt-dlp library (option 2 for fast checking),
    2. get the metadata for each of the new video ids found: this could use yt-dlp library to get the metadata for each of the new video ids found, or in the future, a new service to get the metadata for each of the new video ids found.
    3. update the database with the new video ids and metadata found.
    4. ... rest of the workflow.

Do not implement any code jet, just analyze the codebase and logic and model to implement the new service.

Ask more questions if you need to clarify the objective and task in order to create a detailed implementation plan in Phases with tasks and sub-tasks.

---

🔥 DO NOT INCUDE IN THE PROMPT

```markdown
##### Option 1: YouTube Data API v3

This is the most powerful and reliable method for interacting with YouTube data.

**Pros**

- **Speed and Efficiency:** You can specifically request only the channel's latest videos (e.g., using the `search.list` method with parameters like `channelId`, `type=video`, and sorting by `date`).
- **Filtering:** You can use the `publishedAfter` parameter to only check for videos published _since your last check_, making the API call extremely fast.
- **Rich Metadata:** The API can return various metadata fields directly, potentially reducing the need to use `yt-dlp` for some channels or simple use cases.

**Implementation Strategy**

1.  **Periodic Check (API):** Use the `search.list` method with `publishedAfter` set to the timestamp of your last successful run. This returns a clean, small list of new video IDs.
2.  **Full Sweep (yt-dlp):** Pass the newly identified video IDs to `yt-dlp` to get the full, detailed metadata dump (`--dump-json`) or to perform the eventual download/processing.

> **Note:** The YouTube Data API has a **Quota** system. Checking for new videos is generally a low-cost operation, but be mindful of your usage if you are monitoring thousands of channels or running checks very frequently.

---

### QUESTIONS:

1. Which library should we use to parse the RSS/Atom XML feed?

- [ ] A. feedparser - Popular library for parsing RSS/Atom feeds (new dependency)
- [ ] B. lxml - Already installed, use ElementTree-style parsing directly

2. How should we implement the RSS Celery task?

- [ ] A. Create a NEW separate Celery task for RSS (keep tasks completely independent)
- [ ] B. Modify existing task to accept a 'method' parameter ('rss' or 'ytdlp')

3. Should the periodic automatic checks (Celery Beat) use the new RSS method?

- [ ] A. Yes - Periodic checks should use RSS (fast), manual deep scan uses yt-dlp
- [ ] B. No - Keep periodic checks using yt-dlp, RSS is only for manual quick checks
- [ ] C. Make it configurable in user settings

Notes:

- We could tell the user that the first time they should always use the "search for recent videos (Slow API)" button to search for new videos, and then they can use the "search for latest videos (RSS Feed)" button to search for new videos.

- Download an example of the RSS feed for a Youtube Channel and parse it to get the list of new video IDs. Create documentation with the example to help the ai developer to understand how to implement the new service.
  - https://www.youtube.com/channel/UC5eAFEk3psF0mIDtKVsdl4Q
  - https://www.youtube.com/feeds/videos.xml?channel_id=UC5eAFEk3psF0mIDtKVsdl4Q
```

---

## Prompt (Agent Mode)

ok. I have run the app locally with docker compose and production configuration and used the new button "Search for latest videos (RSS Feed)" and nothing happenned. I get the toast message "RSS check task queued successfully", but no other indication that the task is running or that it has finished. We do not have the icon spinning or the status changing as in the case of the "Search for recent videos (Slow API)" button. After a couple of minutes i checked the events in the "/activity" page and i see no events related to the action trigered with this new button in the list of events.

I then used the old button "Search for recent videos (Slow API)" and it got spinning right away. Surprinsingly the icon for the other button started spinning as well. It change the status in the card of the channel to "queued" and it stayed like that for a while (5 minutes aprox). Then after that time, it changed to "updated" and the date and time of the last update as expected. I can now see the events correctly created and listed in the "/activity" page related to this last action trigered with the old button in the list of events. It did not find any new videos, but it seemed to be working as expected.

Some things to take into account:

- The old button search seems to be working as expected. However, when triggered, it should not make the icon for the other button start spinning.
- The new button does not seem to be working as expected. It did not updated the card of the channel to show the status "queued/searching/updated" and it did not create any events that can be listed later in the "/activity" page.

Revise the workflow and what is expected to be done when the new button is triggered.

---

## Prompt (Agent Mode)

Now, we have a worse problem. The new button (find updates of new videosusing RSS feed) search takes for ever to finish and got stuck in a loop checking for new videos, when it should be faster.

After ten minutes the card of the channel i was searching new videos with the RSS method, showed "queued" as status and did not change. I stoped the docker containers and restarted them.

I restarted the docker containers and the problem persisted. The card of the channel still showed "queued" as status and did not change. And the "/activity" page did not show any events related to this last action. Moreover, the buttons icons keep spinning and the status of the card does not change from "queued" after rebuilding the containers a couple of times.

The fact that tasks can get stuck in the background and we have no way to manage them or know their status is a big problem. We need to find a way to manage them and know their status. We need at least to add a way in the "advanced" tab of the "/settings" page a button to cancel all current tasks if needed.

### Tasks

- Check the data of the responses from the backend API that i include below. You can see that the channel with id: 1 is stuck in the background and the task is not finishing. Check the task status in the database to find the problem and fix it.
- Explore the implementation of the new workflow and codebase to find the problem and fix it.
- Add a way in the "advanced" tab of the "/settings" page a button to cancel all current celery tasks in the background if needed.

Here are some of the values that the page continues to receive after the task is stuck in the background, and after the container restarted:

<DATA from the browser console with request and the object with the response from the backend API>
https://labcastarr-api.oliverbarreto.com/v1/youtube-videos/stats/channel/1
{
"pending_review": 4,
"reviewed": 48,
"queued": 0,
"downloading": 0,
"episode_created": 1,
"discarded": 1,
"total": 54
}

https://labcastarr-api.oliverbarreto.com/v1/youtube-videos/stats/channel/2
{
"pending_review": 48,
"reviewed": 2,
"queued": 0,
"downloading": 0,
"episode_created": 1,
"discarded": 0,
"total": 51
}

https://labcastarr-api.oliverbarreto.com/v1/followed-channels/1/task-status
{
"id": 9,
"task_id": "dea09f05-bba5-4e93-b90b-a5f450fc4162",
"task_name": "check_followed_channel_for_new_videos_rss",
"status": "PENDING",
"progress": 0,
"current_step": null,
"result_json": null,
"error_message": null,
"followed_channel_id": 1,
"youtube_video_id": null,
"created_at": "2025-11-29T15:21:43.369650",
"updated_at": "2025-11-29T15:21:43.369651",
"started_at": null,
"completed_at": null
}

https://labcastarr-api.oliverbarreto.com/v1/followed-channels/2/task-status
{
"id": 5,
"task_id": "a269c7d7-4ce9-4d74-a110-9f90618d53ab",
"task_name": "check_followed_channel_for_new_videos",
"status": "SUCCESS",
"progress": 100,
"current_step": null,
"result_json": "{\"new_videos_count\": 0, \"total_pending_count\": 48}",
"error_message": null,
"followed_channel_id": 2,
"youtube_video_id": null,
"created_at": "2025-11-28T15:09:59.022740",
"updated_at": "2025-11-28T15:11:39.851713",
"started_at": "2025-11-28T15:09:59.081960",
"completed_at": "2025-11-28T15:11:39.851249"
}

https://labcastarr-api.oliverbarreto.com/v1/notifications/unread-count
{"unreadCount":13}

---

# Prompt (Agent Mode)

I followed your instructions to restart the celery worker and the beat scheduler. I also restarted the containers and the problem persisted.

However, i did not use the very same command that you provided. I used the following command since i was using the production configuration:

```bash
#Step 1: Restart Celery Worker (CRITICAL)
#docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev

#But i used the following command since i was using the production configuration:
docker compose -f docker-compose.production.yml restart celery-worker celery-beat
```

After restarting the celery worker and the beat scheduler, the problem persisted. The card of the channel still showed "queued" as status and did not change. And the "/activity" page did not show any events related to this last action. Moreover, the buttons icons keep spinning and the status of the card does not change from "queued" after rebuilding the containers a couple of times.

Then I followed your instructions to use the new Advanced tab to clear any old PENDING/FAILED tasks and monitor task health. The Advanced tab now gives you visibility into background task status. After using the CLEAR tasks, i went back to the follwoed channels page again, and now the problem was gone. The card showed the last updated message with the date of the last completed task as expected.

Then i used the RSS button to search for new videos and it worked as expected. I was way faster than using the old button. I am checking channel with id:1 which has no new videos published as of today, and we are updated in the database with the channel, and the search found no new videos to fetch medatata. After it finnished, the card showed the last updated message with the date of the last completed task as expected.

The only problem that we need to fix is that when i use the button for the quick "RSS feed" search, the icons of both buttons start spinning and after the task finnishes, both stop at the same time. The icon of a button should only spin when it is triggered. Clicking on a button should not make the other button icon spin.

---

## Prompt (Agent Mode)

I now want to solve the problem that we have with the status of the celery task in the Followed Youtube Channel card component. When the user clicks the button to search for videos (using either options "Search for recent videos (Slow API)" or "Search for latest videos (RSS Feed)") we set the status as "queued". It stays in that status until the task is finnished processing the videos. It does not show the "searching" (downloading state in the state machine). We should be showing "searching" when the task is being processed, actually using the RSS feed or the slow API to search for new videos, and downloading metadata and storing it in the database.

The functionality works, but the status of the card is not showing the correct status.

Explore the codebase and the architecture to find the problem and fix it.

---
