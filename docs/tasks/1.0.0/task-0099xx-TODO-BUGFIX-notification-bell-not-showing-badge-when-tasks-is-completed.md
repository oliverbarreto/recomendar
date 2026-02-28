# Task 0058: BUGFIX: Fix the notification bell icon in the sidebar not showing the latest operations completed

- Session File: @
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-11-29
- Model: Claude Sonnet 4.5

---

## Prompt (Agent Mode)

Simplify the process of the bell.

1. the bell icon should only show a badge with a number of completed operations completed.

- I launch a background task to search for new videos for a followed channel.
- The task does its job and is completed successfully, the bell icon should increase by one a badge with the number of completed operations.
- In te case of error, the should also increase by one a badge with the number of completed operations.

2. In the future we might also want to place other important events in the bell icon, like:

- A new video is discovered for a followed channel.
- A new episode is created for a followed channel.
- A new video has finnished uploading for a followed channel.
- A new video has finnished downloading for a followed channel.
