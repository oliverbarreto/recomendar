# Task 0055: Refactor new architecture to search for new videos using youtube channel rss feed

- Session File:
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-29
- Model: Claude Opus 4.5

---

## Prompt (Plan Mode)

Explore the codebase of the project that implements the functionality to "search for new videos from a FollowedYoutube Channel" feature both, in the frontend and the backend (FastAPI Backend and Celery tasks). Analyze the workflow and the architecture of the codebase involved. We should be already following a (relaxed version of) Clean Architecture approach.

Fully understand the logic, the workflow, the architecture, use cases, and the database model and schema of the codebase involved. We should have code impleementing various functionalities, services, repositories, components, etc. to implement the feature.

Create mermaid diagrams to help the developer to understand the codebase and the architecture. This is important to document the current state of the codebase and the architecture, and to add new features and refactorings in the near future.

## Some of the Features involved:

- Follow/Unfollow a Youtube Channel (it should be implemented in the backend accesssing the database, not via celery tasks)
- Search for new videos of a Youtube Followed Channel ("Check for new videos" option in the context menu of a Followed Youtube Channel card) using the `yt-dlp` library using Celery tasks in the background.
- Search for past videos of a Youtube Followed Channel ("Backfill videos" option in the context menu of a Followed Youtube Channel card) using the `yt-dlp` library using Celery tasks in the background.
- Configure settings for videos discovery ("auto-approve all episodes" to automatically create episodes from all new videos in this channel)
- Notifications of events happening in the feature for new videos discovered (notifications section in the frontend)

### Results

Plan Document is stored in @docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md
