# Task [Task Description]
- Session File: @file-name:
- IDE: Claude Code
- Date: 2026-01-29
- Model: Claude Opus 4.5


## Overview

This is a project with a number of features and workflows already implemented that i haven't touched for a couple of months and i need to resume working on it. It is very important to understand the project and the features we have implemented to update the documentation and the codebase organization.

There is a `CLAUDE.md`, `README.md` and other files (`docs/documentation/*.md`) on the docs folder but we need to thoroughly explore the actual state of the project codebase again and understand what we have implemented so far and the point in which we are right now to update documentation, and maybe rethink its organization. There is an important file in that folder that is `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md` that is a technical analysis of the feature to search for new videos in youtube channels and create episodes from them using celery tasks in the background that we got already working. This file is very important to understand the architecture and the implementation of the feature and the state of the project right now. We should use this file as a reference in our analysis.

There are also another two example projects that i created to test a new feature to search for new videos in youtube channels and create episodes from them. These test project are located in the directory `web/` and `video-search-engine/`. These two example projects should be ignored in terms of the documentation for our project. The purpose was to use it as example code and documentation related to a new feature requeset to incorporate in our main project. The first one was a flask app that was used as reference for the new architecture, and the second one was a new project to test the feature that will allow searching for new videos in youtube channels and create episodes from them using celery tasks in the background that we got already working.

Your goal is to thoroughly explore the project codebase again and understand what we have implemented and the point in which we are right now to update documentation, and maybe rethink and simplifyits organization.

I think we definetely need to update the documentation to reflect: 
- the tech stack, 
- the architecture, 
- the models and the database schema, 
- the features we have implemented, 
- the architecture of the codebase and the codebase organization, for both backend and frontend, separately and together, considering that we use a monorepo structure.
- relevant workflows, 
- and also important is the deployment workflow for both local and production considering that we use docker and docker compose for both. 

### Goals and Instructions:

The goal conduct an extense exploration of the project codebase and understand the actual state of the project. Then analyze actual documentation and update it to reflect the actual state of the project. 

The goal is not to simplify the documentation per se, but to make it more accurate and up to date with the actual state of the project. We will use the new documentation files to advance in the development of the project, therefore it is very important to make it as accurate and up to date as possible.

Do not change any existing documentation files, we will identify the files that need to be updated and create the new ones in `docs/documentation/new-documentation` folder.

