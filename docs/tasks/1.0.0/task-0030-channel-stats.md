# Task 0030: Channel Stats

## Prompt

I would like to add a new feature to the project: channel stats. We want to be able to get stats of the channel.

I want to be able to leverage statistics of the podcast channel. I would like to get stats of how many times and time-stamps of when the files are accessed via the api.  Also i would like to know, if possible, if we can track how much of the audio files are served via the api. 

Some questiones that i would like to answer:
- Are the episodes fully reproduced by the user utilizing his podcast app of choice ?
- how many times is an episode reproduced ?
- how many episodes has th user reporduced ?
- what are the episodes that have not been reproduce ?
- ... think about what other questions might be relevant

This implies adding infrastructure to track the stats.

Think hard about the best way to implement this feature. Are there any other aspects that we should consider before we draft a detailed implementation plan with successs criteria and small tasks to be implemented later.

Create the plan in a new file called task-0030-episode-stats-implementation-plan-v1.md

---

### Result

Based on my research of the codebase and podcast analytics best practices, I've analyzed the requirements for implementing channel/episode statistics tracking. Let me create a comprehensive implementation plan.

#### Key Findings from Research:

Current Infrastructure:
✅ Event system already exists (event.py)
✅ Media serving with HTTP range request support (media.py)
✅ RSS feed generation (feeds.py)
✅ Clean Architecture with service layers

Podcast Analytics Best Practices:
- Byte-Range Request Tracking: Essential for measuring actual playback vs downloads
- Deduplication: Multiple range requests from same client = single listen session
- Playback Progress: Track bytes served to estimate completion percentage
- IAB v2.1 Compliance: 60-second rule for valid "play" vs "download"
- User Agent Analysis: Identify podcast apps/platforms
- Geographic Data: IP-based location tracking (privacy-compliant)

Questions to Answer:
✅ Are episodes fully reproduced? (Track byte ranges served)
✅ How many times is an episode reproduced? (Track unique sessions)
✅ How many episodes has the user reproduced? (Aggregate by identifier)
✅ What episodes have not been reproduced? (Query episodes with zero plays)
✅ Listen completion rate (bytes served / file size)
✅ Average listen duration
✅ Drop-off points (where listeners stop)
✅ Popular episodes by channel
✅ Platform/app distribution
✅ Geographic distribution (optional)
✅ Time-based trends


---