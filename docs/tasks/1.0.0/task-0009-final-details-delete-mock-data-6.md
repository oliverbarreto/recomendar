# Prompt
Now we are able to advance in the multi-step form
with the real data of the youtube url, but when we
get to the last step and the app tries to
download the audio, we get an error.\

## Error Type
Console TypeError

## Error Message
Cannot read properties of undefined (reading 'id')


    at handleSubmit (src/components/features/episo
des/add-episode-form.tsx:227:35)

## Code Frame
    225 |       })
    226 |
> 227 |       setCreatedEpisodeId(episode.id)
        |                                   ^
    228 |       toast.success('Episode created
successfully!')
    229 |
    230 |       // Start polling for progress

Next.js version: 15.5.2 (Webpack)
\
- See the error in this image [Image #1]



---

## Result

⏺ Perfect! Now the issue should be resolved. The
  problem was that the frontend and backend were
  using different field naming conventions:

  Issue Fixed: API Response Field Name Mismatch

  Problem: The frontend Episode interface was
  expecting camelCase field names (channelId,
  videoId, etc.) but the backend was returning
  snake_case field names (channel_id, video_id,
  etc.).

  Solution: Updated frontend types and API calls to
  use snake_case field names to match the backend
  schema:

  1. ✅ Updated Episode interface - Changed from
  channelId to channel_id, videoId to video_id, etc.
  2. ✅ Updated CreateEpisodeRequest interface -
  Changed from channelId/videoUrl to
  channel_id/video_url
  3. ✅ Updated API client - Now uses correct
  snake_case field names when making requests
  4. ✅ Updated form component - Now passes correct
  field names to the API

  Previously: episode.id was undefined because the
  response had channel_id but frontend expected
  channelId
  Now: Frontend correctly reads episode.id from the
  snake_case API response

  The add episode workflow should now work completely
   end-to-end without the "Cannot read properties of
  undefined (reading 'id')" error!


