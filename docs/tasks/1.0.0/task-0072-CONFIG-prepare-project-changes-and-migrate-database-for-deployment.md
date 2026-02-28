# Task 0071: CONFIG - PREPARE PROJECT CHANGES AND MIGRATE DATABASE FOR DEPLOYMENT

- Session File: task-0065-FEATURE-store-followed-youtube-channel-description-full-session.md
- IDE: Cursor
- Date: 2025-12-03
- Model: Composer 1

---

## Prompt (Plan Mode)

We have been working on various big features that are now merged into the project. Now it is time to prepare the project for deployment on production. The thing is that we already have a working version of the project running in production with its own database schema and data. We cannot lose the data in production. We cannot reset the database, there is user config like tags, channel name, description and other user preferences, and most importantly, the episodes and audio files already downloaded that we do not want to lose.

I have made a backup (copied sql file) of the production database.

Now i need to prepare the project for deployment. I need to make sure that the project is ready for deployment.

Since we build the project using docker compose from the codebase, i have copied the new code, making sure not to delete the media files and the database files.

- Media Files: `backend/media/`
- Database Files: `backend/data/labcastarr.db` (there is no .db-wal and no .db-shm files)

I want you to assist me with the process of preparing the project for deployment. Should we use a copy of the database and run the migrations lcoally before deploying to production? Or should we run the migrations on the production database?

Analyze the pros and cons of both approaches and suggest the best approach.

Then, based on your analysis, suggest the best approach and the steps to follow.

The copy of the current production database is in the `backend/data/labcastarr_prod_copy.db`.

---

Let's migrate with the plan.

Remember that the copy of the current production database is in the `backend/data/labcastarr_prod_copy.db`. After we apply the migrations stop so i can manually rename the file to `labcastarr.db`.

Then we will run the app with docker compose using production configuration (`docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d`).
