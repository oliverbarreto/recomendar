# Prompt

We want to add a new feature to the application to allow the user to upload a local audio file to the application and create an episode from it. 

The user should be able to upload the audio file and the data about the episode from the frontend and the backend should be able to first validate the audio file and then process it and then create an episode from it.

We can want to use a multi-step form to allow the user to upload the audio file and the data about the episode from the frontend. It should have the following steps:
- Step 1: Upload the audio file.
- Step 2: Enter the data about the episode.
- Step 3: Review the episode data and create the episode.
- Step 4: Confirm the episode creation.

We should consider the following requirements:
- The audio file should be validated and processedto be a valid audio file.
- The audio file should be stored in the media folder with the same name structure as the other audio files.
- The episode should be created and added to the database.
- The episode should be added to the podcast feed.
- We should add a new column to the episode table to differentiate that the episode was created from a local audio file.

Analyze the codebase to understand the existing code and the code structure, and identify the pieces that we need to add or modify to implement the new feature (logic, services, repositories, models, etc.).

DO NOT IMPLEMENT NOW. Just analyze and plan the steps needed to implement the new feature.

---

## Result