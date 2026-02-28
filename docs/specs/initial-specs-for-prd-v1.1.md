# LabCastARR

## Objective

I want to create an appliction to allow users tu download audio tracks from youtube videos and create a personal podcast channel taht can be used by most popular podcast applications like Spotify and Apple Podcast. 

This will be a first version of the app intended to target homelab and personal use.

The app is comprised by a frontend and a backend: 
- The frontend will be a next web application that will allow users to upload an url of a youtube video that will be passed to the backend. The backend is responsible for downloading the audio files from Youtube (using a library called yt-dlp). The web app will also allow the user to list all the audio files that have been downloaded. It will also allow otehr CRUD operations like delete audio files and the podcast feed. 
- The backend will be a FastAPI application that will handle the requests from the frontend and will be responsible for downloading the audio files from Youtube, processing them and returning the results to the frontend. The backend will also be responsible for creating the podcast feed (RSS) that can be used by most popular podcast applications.


## Implementation details

### Technology Stack
- The app must use Next.js v15+ as frontend and FastAPI as backend.
- The application should be structured in a way that allows easy deployment and scaling, utilizing best practices for both frontend and backend applications using clean architecture principles.
- The app must use ShadCN v4 UI, Radix and TailwindCSS for components and styling.
- The app will use Lucide icons for icons.
- The frontend MUST use TypeScript (IMPORTANT: NO JAVASCRIPT).
- The frontend should use Zod for form validation and use useActionState with react-hook-form for form validation.
- The frontend should use React Query to handle data fetching and caching.
- The backend MUST use Python 3.11+.
- The backend should use SQLAlchemy as ORM to interact with the SQLite database.
- The backend should use Pydantic to validate the request and response data.
- The backend should use Alembic to manage the database migrations.
- The backend should use BackgroundTasks from FastAPI to handle the long running tasks like downloading the audio files, storing the audio files, storing the metadata in the database and creating the podcast feed

### Application & Deployment
- The application must be deployed using Docker and Docker Compose.
- The application must be able to run locally for development and testing purposes.
- The application must be able to be deployed to a production environment.
- The application will be used for personal use, so it will not have a multi-user authentication system, however, it will have a simple authentication system (using an API KEY or jwt based) to prevent unauthorized access.
- The application must be able to provide a `https` endpoint using a reverse proxy like Traefik or Nginx, to allow Apple Podcast and Spotify to access the podcast feed.
- The app should use a `.env` file to manage environment variables like the domain name of the published RSS feed, the podcast channel name, description, author, the API KEY used by the frontend and backend, etc.
- The folder structure of the app should be:
```
/LabCastARR
  /backend
    /app
      /api
      /core
      /models
      /schemas
      /services
      /utils
      /static
        /media
      /tests
      main.py
    Dockerfile
    requirements.txt
  /frontend
    /src
      /components
      /pages
      /public
      /styles
      /tests
      /utils
    next.config.js
    package.json
    Dockerfile
  .env
  docker-compose.yml
  README.md
```

### Frontend
- The frontend will have a UI that will utilize a design with a top navigation bar that will have links to the main pages of the app: 
  - Home Page (/) which should redirect to the Channel Page,
  - Channel Page (/channel), which have a nice grid of cards (like Youtube website) with the episodes (audio files extracted from youtube videos) that have been downloaded. 
  - Add Episode ("+" icon), a simple form with a single input field to upload a youtube video url to download the audio file and a button to send it.
  - Settings (/settings) to view and manage user settings for the Podcast RSS Feed and the tags CRUD.
  - and it will also have a search text box to filter the episodes of the /channel page by title, description, author, tags, keywords, etc.
  - and a notification icon to show the progress of the audio files that might be downloading in a given moment. Showing a list of events for the latest events (like a navigation history log) of the last 24 hours (or week, or 30 days) like "Downloading audio file from Youtube", "Processing audio file", "Audio file downloaded successfully", "Error downloading audio file", etc.

### Backend
- The backend will be a FastAPI application that will handle the requests from the frontend and will use the `yt-dlp` library to download the audio files from Youtube and to access metadata about the videos.
- The backend will use a database to store the information about the audio files and the podcast feed, users settings, and about the podcast channel. The database will be a `SQLite` database for simplicity.
- The backend will also use a storage service to store the audio files. The storage service will be a local file system for simplicity. The files will be shared as FastAPI static files.
- The backend will also use a library called `PodGen` to create the podcast feed (RSS) which will be stored in the local file system and will be accesible by Podcast applications via a route served by FastAPI backend.
- **Optional** we will consider the following option: The backend will also use a library called `pydub` to process the audio files (e.g. convert them to mp3 format, normalize the audio, etc.).

## Features
### Frontend
- The frontend should allow users to:
  - Upload a youtube video url to download the audio file.
  - List all the audio files that have been downloaded.
  - Delete audio files.
  - Assign multiple tags to an episode.
  - Edit the metadata of an episode (title, description, author, date, duration, tags, keyworkds, etc.).
  - View the progress of the audio files that are being downloaded in real time using websockets.
  - View the latest events like a navigation history log of the last 24 hours
  - Search episodes by title, description, author, tags, keywords, etc.
  - View and manage user settings (podcast channel name, description, author, tags, etc.).
  - View and manage the podcast feed (RSS).

- The frontend should have the following pages:
  - Home page (/): should redirect to the channel page.
  - Channel page (/channel): to list all the audio files that have been downloaded. 
    - It should also have a link to the Add Episode page and the Settings page. 
    - The home page should also have a link to the podcast feed (RSS).
    - It should allow pagination if there are many audio files.
    - It will sort epidodes by date, with the most recent episode at the top.
    - It must allow deleting audio files.
    - It must allow editiing the metadata of an episode which is initially downloaded bye the backend.
    - It should allow filtering the episodes by tags.
  - Add Episode (/episodes/add): to upload a youtube video url using a simple post request with the url of the video that we want to download.
    - The page should have a form with a single input field for the youtube video url and a submit button.
    - After sending the request to the backend, it should first redirect to the homepage with the list of videos of the channel and show a loading indicator while the audio file is being downloaded. The process of downloading a videos has two main parts:
      - We should extract the metadata of the video (title, description, author, etc.)
      - We must download as a background task in the backend the best audio track available for the video.
      - The front end should add a place holder component for the video right after we reqeust the download.
      - After the backend acceeses the metadata of the video, it should update the place holder with a "video card" component: thumbnail, title, description, author, date, duration, tags, keyworkds, etc. It should also show a loading indicator to show that the audio file is being downloaded.
      - It should communicate with the backend using websockets to get real time updates about the progress of the download.
      - Once the audio file has been downloaded, it should update the "video card" component to show that the audio file is available for playback and download.
      - The "video card" should have a play button to play the audio file using an HTML5 audio player.
    - The frontend should handle the request to the backend to periodically query the status of the download until it is completed or failed. It should show a success message when the audio file has been downloaded successfully. It should show an error message when the audio file could not be downloaded.

  - Episode Page (/episodes/{id}): to show a full page withe the episode information  from the stored metatada. 
    - It should include buttons to edit/delete the episode info.
    - The episode page should also have an HTML5 audio player to play the audio file (sotored in the backend as static file).
    - It should also have a play in youtube button to link the episode with the original video in Youtube.
    - The information of the video is first extracted by the backend using the yt-dlp library and then stored in the database. The page should have allow the user to use a form to edit the metadata of the episode: title, description, author, date, duration, tags, keyworkds, etc.
    - It should allow the user to add/remove tags to the episode.

  - Settings page: to view and manage user settings for the Podcast RSS Feed organized as sections: 
    - Channel Info:
      - Podcast channel name (TEXT)
      - description (TEXT)
      - personal website (URL)  
      - channel image (URL)
      - category (TEXT)
      - language (TEXT)
      - The channel episodes might contain explicit content (BOOLEAN),
    - Authoring:
      - author name and email (TEXT)
      - owner name and email (TEXT)
    - Tags:
      - CRUD operations for tags that can be assigned to episodes.
    - ...

### Backend
- The backend should have the following functionalities:
  - The backend should handle the requests from the frontend and return the appropriate responses and utilize background tasks for long running tasks.
  - The backend should use the `yt-dlp` library to download the audio files from Youtube and get the metadata about the videos.
  - The backend should use the `PodGen` library to create the podcast feed (RSS) that will be accesible by Podcast applications.
  - The backend should store the metadata of the audio file in a `SQLite` database.
  - The backend should use the local file system to store the audio files. It should create a folder called `media` inside the `static` files folder in the backend to store and share the audio files (eg: "https://labcastarr.oliverbarreto.com/static/media/yLjAI19z1xU.m4a").
  - The backend should register all events requested by the user in the database to allow an endpoint to get the latest events like a navigation history.
  - The backend should allow the frontend to get real time updates about the progress of the download.
  - the backend should provide an endpoint to check the health of the backend.
  - the backend should provide an endpoint to get the metrics of the backend (for monitoring purposes).
  - the backend should model:
    - channel settings
    - episodes (created from Youtuve videos which result in metadata of the video and the audio file downloaded into the local file system)
    - tags associated to episodes (many to many relationship)
    - events (for navigation history): id, type, message, timestamp, status (requested, processing, downloading, completed, failed)
    - users (for authentication purposes, even if it is a single user app)
    - ...
  - **Optional** process the audio file using the pydub library (e.g. convert to mp3 format, normalize the audio, etc.).

- The backend should have the following endpoints:
  - POST /episodes: to upload a youtube video url and download the audio file.
  - GET /episodes: to list all the audio files that have been downloaded.
  - GET /episodes/{id}: to get a single audio file by id.
  - DELETE /episodes/{id}: to delete a single audio file by id.
  - PUT /episodes/{id}: to update the metadata of a single audio file by id.
  - GET /settings: to get the user settings for the podcast feed.
  - PUT /settings: to update the user settings for the podcast feed.
  - GET /feed: to get the podcast feed (RSS).
  - GET /tags: to list all the tags.
  - POST /tags: to create a new tag.
  - PUT /tags/{id}: to update a tag by id.
  - DELETE /tags/{id}: to delete a tag by id.
  - GET /ws/episodes/{id}/progress: to get real time updates about the progress of the download.
  - GET /events: to get the latest events like a navigation history.
  - GET /health: to check the health of the backend.
  - GET /metrics: to get the metrics of the backend (for monitoring purposes).
  - POST /regenerate-feed: to regenerate the podcast feed (RSS) manually.
  - 

### Authentication
  - Must have an authentication system to prevent unauthorized access. This should be an API KEY that is set in the `.env` file.
  - The API key must be shard by the frontend and the backend using the `.env` file.
  - The API key must be sent in the request headers using the `Authorization` header with the value `Bearer`.