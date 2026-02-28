# Task 0060: BUGFIX: Allow select/unselect all videos when on selection mode in the /subscriptions/videos page

- Session File: @task-0060-FEATURE-bulk-operations-select-unselect-videos-full-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-12-01
- Model: Composer 1

---

## Prompt (Agent Mode)

In the “[/subscriptions/videos](https://labcastarr.oliverbarreto.com/subscriptions/videos)” page we now have an option to toggle select mode which allows the user to conduct bulk operation (mark as reviewed or discard videos). We need to add a way to improve the experience of the user by allowing the user use a button to select all episodes or to deselect all, instead of going one by one.

The user could also keep cherry-picking selected videos, but we now provide a much faster way to select multiple videos.

Simply as that, the rest remains the same.

We use this button to toggle selection mode<button data-slot="button" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([c…" title="Enter selection mode"></button>
Place the new button to select and to deselect in this row<ForwardRef dir="ltr" data-orientation="horizontal" data-slot="tabs" className="flex flex-col gap-2" children="[Object]" ref={null}>All Videos (50) Pending (50) Reviewed (0) Episodes (0)</ForwardRef>

<div dir="ltr" data-orientation="horizontal" data-slot="tabs" class="flex flex-col gap-2">All Videos (50) Pending (50) Reviewed (0) Episodes (0)</div>
