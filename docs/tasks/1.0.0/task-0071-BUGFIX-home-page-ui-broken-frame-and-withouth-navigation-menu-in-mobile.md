TASK 0071: BUGFIX: Home page UI broken frame and without navigation menu in mobile

- Session File: @task-0058-BUGFIX-UI-homepage-layout-broken-fulll-session.md
- IDE: Cursor 2.0 - Plan Mode
- Date: 2025-12-02
- Model: Cursor Auto Model

## Prompt (Plan Mode)

As you can see in the two images provided, the home page UI is broken. The frame is not horizontally displayed correctly in iPads and iPhones screens.

However, the rest of the pages (eg: /channel, /activity, /settings, /subscriptions/channels, and /subscriptions/videos) are displayed correctly. The problem is that the pace content goes outside the screen width. We have the container extend beyong the screen width, and with the padding that makes it look good in the rest of the pages.

Plan how to make the changes to the home page UI to fix the issue in horizontal display in iPads and iPhones screens.

---

Also, in mobile, with the sidepanel change we lost navigation and need to restore a hamburger navigation menu at the top of the screen to navigate to the other pages.

---

## Prompt (Agent Mode)

build the app with docker compose locally (with production configuration) with "docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d" and check for errors

---

## Prompt (Agent Mode)

the app launches correctly all containers but we have some errors on the browser console:

Uncaught ReferenceError: useRouter is not defined

---

## Prompt (Agent Mode)

The home page continues to look odd on a web browser on a pc/mac You can see in the image that the browser is using vertical and horizontal scrollbars. This indicates that we are doing something wrong. Not like the rest of the pages, in which this effect does not happen.

The problem in the home page is clearly seen by inspecting the left margin of the stats row, we see some padding with the sidepanel on the left side. However, on the right side, the stats go outside the visible screen in the browser, thus the need of the horizontal scroll bar.

In in the image 2 you can see that when i scroll to the right, we see the end of the row, then the padding right, but on the contrary, the lef side is overlaped with the sidepanel.

Analyze why and replicate the same layout in the home page.
