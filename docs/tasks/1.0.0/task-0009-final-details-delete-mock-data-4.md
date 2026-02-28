# Prompt

we are having trouble with the database
   configuration. With the last changes to configure
   SQLite to use WAL mode we now have the database in
   the wrong path. it is now in
   backend/labcastarr.db and
   backend/labcastarr.db-journal Where it should be
   in backend/data/ Fix it and make sure it works. We
   do not have to worry for migrating data, we can
   start with a fresh copy

---

## Result

⏺ The database configuration has been successfully fixed! Here's what I accomplished:

  1. Fixed the database path configuration in both /app/core/config.py and .env to use ./data/labcastarr.db
  2. Removed the old database files from the wrong location (backend/labcastarr.db and
  backend/labcastarr.db-journal)
  3. Created a fresh database in the correct location (backend/data/labcastarr.db)
  4. Verified the server starts successfully and uses the correct database path

  The database is now properly configured to use SQLite's WAL mode and is located in the correct backend/data/
  directory as specified in your project structure. The server starts without issues and the database file is
  created in the right location.
