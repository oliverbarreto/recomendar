# Task 0035 - bugfix pubdate itunes fix with episode creation date

## Prompt

---

## Result

I'll analyze how the <pubDate> is being generated for episodes in the RSS feed. Let me search for the relevant code.
Grep "pubDate"
⎿
13 lines of output
Grep "feed_generation_service"
⎿
35 lines of output
Read feed_generation_service_impl.py
Now let me check the Episode entity to see what publication_date and created_at fields are available:
Read episode.py, episode.py
Now let me check where the publication_date is being set during episode creation:
Grep "publication_date.*youtube|upload_date|published" (in /Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/backend/app)
⎿
30 lines of output
Read youtube_service.py
Now let me check the episode service to see where publication_date is being set when creating episodes:
Read episode_service.py
Read metadata_processing_service.py
Perfect! Now I have all the information I need. Let me analyze the issue and create a plan.
Analysis Summary
You are absolutely correct! The RSS feed is currently using the YouTube video's publication date instead of the episode creation date in your channel. Here's what I found:
Current Flow:
YouTube metadata extraction (youtube_service.py:304):
Extracts 'publication_date': info.get('upload_date') from YouTube
Metadata processing (metadata_processing_service.py:68-80):
Sets publication_date=pub_date (the YouTube upload date)
Sets created_at=datetime.utcnow() (when episode was added to YOUR channel)
RSS feed generation (feed_generation_service_impl.py:293-296):
# Ensure publication date has timezone info
pub_date = episode.publication_date or episode.created_at
if pub_date.tzinfo is None:
    pub_date = pytz.utc.localize(pub_date)
Problem: Uses episode.publication_date (YouTube date) as the primary source, and only falls back to created_at if publication_date is None.
Why This Matters:
The <pubDate> in podcast RSS feeds represents when the episode was published to YOUR podcast, not when the YouTube video was originally uploaded. This affects:
Episode order in podcast apps
"New episode" notifications to subscribers
Chronological display in podcast clients
The Fix:
Change line 294 in feed_generation_service_impl.py to:
pub_date = episode.created_at or episode.publication_date
This will use the date when the user added the episode to their channel (the correct behavior for a podcast feed).


### Fix RSS Feed `<pubDate>` to Use Episode Creation Date

**Problem**: RSS feed currently uses YouTube video's upload date instead of when the episode was added to the channel.

**Solution**: Update the RSS feed generation logic to prioritize `created_at` (when episode was added to channel) over `publication_date` (YouTube upload date).

**Change Required**:
- **File**: `backend/app/infrastructure/services/feed_generation_service_impl.py`
- **Line**: 294
- **Current**: `pub_date = episode.publication_date or episode.created_at`
- **New**: `pub_date = episode.created_at or episode.publication_date`

**Impact**:
- Episodes will appear in podcast apps ordered by when they were added to your channel, not when they were uploaded to YouTube
- "New episode" notifications will trigger when you add episodes, not based on YouTube dates
- More intuitive chronological ordering for podcast subscribers

**Testing**:
1. Regenerate RSS feed for a channel
2. Verify `<pubDate>` in feed.xml matches episode `created_at` timestamps
3. Test in podcast validator if available

...

Plan Mode
⎿
User approved the plan


Update Todos

Update RSS feed generation to use episode created_at instead of publication_date

Test RSS feed generation with updated logic
Edit feed_generation_service_impl.py
⎿
Added 1 line
123
1234
Update Todos

Update RSS feed generation to use episode created_at instead of publication_date

Test RSS feed generation with updated logic
Perfect! I've updated the RSS feed generation logic. Now let me verify the change is correct by reading the updated section:
Read feed_generation_service_impl.py (lines 286-310)
Update Todos

Update RSS feed generation to use episode created_at instead of publication_date

Test RSS feed generation with updated logic

✅ Fix Complete
I've successfully updated the RSS feed generation logic in feed_generation_service_impl.py:295.

**What Changed:**

- **Before:**
`pub_date = episode.publication_date or episode.created_at`

- **After:**
`pub_date = episode.created_at or episode.publication_date`

**Impact:**
Now the RSS feed <pubDate> will correctly use:
1. Primary: created_at - When you added the episode to your channel
2. Fallback: publication_date - YouTube's original upload date (only if created_at is somehow missing)

This means episodes will appear in podcast apps in the order you added them to your channel, not when they were originally uploaded to YouTube. This is the correct behavior for a curated podcast feed.

**To See the Changes:**

The RSS feed will automatically use the new logic the next time it's generated. You can verify by:
1. Accessing your feed at https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml
2.Checking that <pubDate> values now match when episodes were added to your channel (their created_at timestamps)
