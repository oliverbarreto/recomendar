# TASK: CHORE - Divide app concerns in two apps: recommendarr and podcastarr

## Overview

We want to divide the app concerns in two apps: recommendarr and podcastarr.

- LabcastARR will be an app that will manage and publish podcasts channels. It allows the user to add episodes of podcasts channels, publish the channel and manage the episodes of the channel.
- RecommendARR will be an app that will allow the user to follow channels, track activity in channels to identify new videos and recommend videos and podcasts to the user.

Currently we have both concerns in our current same app. We want to divide them into two apps.

Except for the concerns of the two apps, we want to maintain basically everything in common between the two apps:

- UI
- architecture
- database schema
- data model
- services
- repositories
- components
- pages
- styles
- utils
- tests
- documentation
- configuration
- deployment
- monitoring
- logging
- error handling

## Tasks

The goal is to explore the current codebase to understand the current architecture and data model, and then create a detailed implementation plan to divide the app concerns into two apps. We will need to create two separate projects with the codebase for each app. It should be possible to do this in a way that is relatively easy to maintain and update in the future. It would mainly be removing parts of the codebase that are not needed for each concert.

I think we can copy the project before the separatation for each app and then work separately on diferent projects and remove the parts that are not needed for each app.

Analyze the best approach to do this.
