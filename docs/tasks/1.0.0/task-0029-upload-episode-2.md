# Prompt

@task-0029-upload-episode-plan-v2.md 

Read the file with the implementation plan for the feature we want to implement


---

### Results

🤖 I've read the implementation plan for the file upload episode creation feature. This is a comprehensive plan that adds the capability for users to upload audio files directly to create podcast episodes, as an alternative to the current YouTube-based workflow.

## Plan Summary

The plan proposes adding a file upload feature with these key characteristics:

**Architecture:**
- Unified `Episode` entity for both YouTube and uploaded episodes
- Single database table with `source_type` field to distinguish sources
- Accept multiple audio formats (MP3, M4A, WAV, OGG, FLAC) but store only MP3/M4A
- Auto-convert non-iTunes-compatible formats using FFmpeg

**Workflow:**
1. User selects audio file → Client-side validation
2. Preview step → User fills episode details (title, description, date, tags)
3. Upload with progress tracking → Server processes and validates
4. Episode created immediately (status: "completed")

**Implementation Phases:**
- **Phase 1**: Backend infrastructure (exceptions, schemas, validation, upload processing, endpoints, database migration)
- **Phase 2**: Frontend implementation (forms, drag-and-drop, progress tracking, error handling)
- **Phase 3**: Integration & testing (error scenarios, RSS feed compatibility, event logging)

Before I create a detailed execution plan, I need to clarify a few things:

1. **Scope preference for initial implementation?**
   - a) Full implementation as described (all 3 phases, ~22-28 hours)
   - b) MVP first (basic upload without format conversion, simpler UI)
   - c) Backend-only first, then frontend separately

2. **FFmpeg dependency - is it already installed on your system?**
   - a) Yes, FFmpeg is available
   - b) No, need to install it first
   - c) Not sure, need to check

3. **Database migration approach?**
   - a) Create and apply migration immediately
   - b) Create migration but I'll review before applying
   - c) Just show me the migration SQL first

4. **Testing preference?**
   - a) Implement with manual testing as we go
   - b) Write automated tests alongside implementation
   - c) Implement first, tests later

---


## Prompt

Here are my answers to the questions in the plan:

1. **Scope preference for initial implementation?**
   - Yes, with full implementation as described: All 3 phases: first the backend, then the frontend and finally testing it works with docker compose
   - The user must provide files with the proper format and size, otherwise the upload will fail. The app should identify the format and size of the file and if it is not supported, it should show an error message to the user, indicating the supported formats and sizes.

2. **FFmpeg dependency - is it already installed on your system?**
   - Yes, i think FFmpeg is available on the system since we are converting audio files when downloaded from YouTube, but check to be 100% sure.

3. **Database migration approach?**
   - Create and apply migration immediately. 
   - If needed, we can delete and create the development database to start fresh
   - For production, we should identify how to keep the current data. We MUST not lose any data.
   
4. **Testing preference?**
   - Implement with manual testing as we go. 
   - We msut test the app with docker compose in development and production to ensure it works as expected.


---

### Results

