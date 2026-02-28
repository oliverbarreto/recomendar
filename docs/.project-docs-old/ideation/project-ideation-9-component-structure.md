# Component Structure

## Prompt used to generate this file
```markdown
let's now focus on the frontend to conduct an analysis to identify needed UI components.

For each significant UI component identified from the UI/UX Specification and design files (Figma), the following details MUST be provided. Repeat this subsection for each component. The level of detail MUST be sufficient for an AI agent or developer to implement it with minimal ambiguity. }

### Component: `{ComponentName}` (e.g., `UserProfileCard`, `ProductDetailsView`)

- **Purpose:** {Briefly describe what this component does and its role in the UI. MUST be clear and concise.}
- **Source File(s):** {e.g., `frontend/src/components/user-profile/UserProfileCard.tsx`. MUST be the exact path.}
- **Visual Reference:** {description}
- **Props (Properties):**
  { List each prop the component accepts. For each prop, all columns in the table MUST be filled. }
  | Prop Name | Type                                      | Required? | Default Value | Description                                                                                                |
  | :-------------- | :---------------------------------------- | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------- |
  | `userId`        | `string`                                  | Yes       | N/A           | The ID of the user to display. MUST be a valid UUID.                                                     |
  | `avatarUrl`     | `string \| null`                          | No        | `null`        | URL for the user\'s avatar image. MUST be a valid HTTPS URL if provided.                                    |
  | `onEdit`        | `() => void`                              | No        | N/A           | Callback function when an edit action is triggered.                                                        |
  | `variant`       | `\'compact\' \| \'full\'`                     | No        | `\'full\'`        | Controls the display mode of the card.                                                                   |
  | `{anotherProp}` | `{Specific primitive, imported type, or inline interface/type definition}` | {Yes/No}  | {If any}    | {MUST clearly state the prop\'s purpose and any constraints, e.g., \'Must be a positive integer.\'}         |
- **Internal State (if any):**
  { Describe any significant internal state the component manages. Only list state that is *not* derived from props or global state. If state is complex, consider if it should be managed by a custom hook or global state solution instead. }
  | State Variable | Type      | Initial Value | Description                                                                    |
  | :-------------- | :-------- | :------------ | :----------------------------------------------------------------------------- |
  | `isLoading`     | `boolean` | `false`       | Tracks if data for the component is loading.                                   |
  | `{anotherState}`| `{type}`  | `{value}`     | {Description of state variable and its purpose.}                               |
- **Key UI Elements / Structure:**
  { Provide a pseudo-HTML or JSX-like structure representing the component\'s DOM. Include key conditional rendering logic if applicable. **This structure dictates the primary output for the AI agent.** }
  ```html
  <div> <!-- Main card container with specific class e.g., styles.cardFull or styles.cardCompact based on variant prop -->
    <img src="{avatarUrl || defaultAvatar}" alt="User Avatar" class="{styles.avatar}" />
    <h2>{userName}</h2>
    <p class="{variant === 'full' ? styles.emailFull : styles.emailCompact}">{userEmail}</p>
    {variant === 'full' && onEdit && <button onClick={onEdit} class="{styles.editButton}">Edit</button>}
  </div>
  ```
- **Events Handled / Emitted:**
  - **Handles:** {e.g., `onClick` on the edit button (triggers `onEdit` prop).}
  - **Emits:** {If the component emits custom events/callbacks not covered by props, describe them with their exact signature. e.g., `onFollow: (payload: { userId: string; followed: boolean }) => void`}
- **Actions Triggered (Side Effects):**
  - **State Management:** {e.g., "Dispatches `userSlice.actions.setUserName(newName)` from `src/store/slices/userSlice.ts`. Action payload MUST match the defined action creator." OR "Calls `updateUserProfileOptimistic(newData)` from a local `useReducer` hook."}
  - **API Calls:** {Specify which service/function from the "API Interaction Layer" is called. e.g., "Calls `userService.fetchUser(userId)` from `src/services/userService.ts` on mount. Request payload: `{ userId }`. Success response populates internal state `userData`. Error response dispatches `uiSlice.actions.showErrorToast({ message: 'Failed to load user details' })`.}
- **Styling Notes:**
  - {MUST reference specific Design System component names (e.g., "Uses `<Button variant='primary'>` from UI library") OR specify Tailwind CSS classes / CSS module class names to be applied (e.g., "Container uses `p-4 bg-white rounded-lg shadow-md`. Title uses `text-xl font-semibold`.") OR specify SCSS custom component classes to be applied (e.g., "Container uses `@apply p-4 bg-white rounded-lg shadow-md`. Title uses `@apply text-xl font-semibold`."). Any dynamic styling logic based on props or state MUST be described. If Tailwind CSS is used, list primary utility classes or `@apply` directives for custom component classes. AI Agent should prioritize direct utility class usage for simple cases and propose reusable component classes/React components for complex styling patterns.}
- **Accessibility Notes:**
  - {MUST list specific ARIA attributes and their values (e.g., `aria-label="User profile card"`, `role="article"`), required keyboard navigation behavior (e.g., "Tab navigates to avatar, name, email, then edit button. Edit button is focusable and activated by Enter/Space."), and any focus management requirements (e.g., "If this component opens a modal, focus MUST be trapped inside. On modal close, focus returns to the trigger element.").}
```

---

Okay, let's conduct an analysis to identify the needed UI components for the frontend based on our revised use cases and the proposed Next.js application structure. I will detail several key components following the format you've provided.

This will be a representative list; a full application would have many more granular components (like custom `Button`, `Input`, `Modal` primitives if not using a library like Shadcn/ui extensively). We'll focus on more composite or feature-specific components here.

Given we've decided on Tailwind CSS and potentially Shadcn/ui, the styling notes will reflect that.

---

### Component: `AuthForm`

-   **Purpose:** Provides a user interface for both login and registration. It adapts its fields and submission logic based on whether the user is trying to log in or register.
-   **Source File(s):** `frontend/src/components/forms/AuthForm.tsx`
-   **Visual Reference:** A standard centered form with a title ("Login" or "Register"), input fields for email/username and password, and an additional "Confirm Password" field for registration. A submit button and a link to toggle between login and registration modes.
-   **Props (Properties):**
    | Prop Name   | Type                                  | Required? | Default Value | Description                                                                                                                               |
    | :---------- | :------------------------------------ | :-------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
    | `variant`   | `'login' \| 'register'`               | Yes       | N/A           | Determines if the form is for login or registration, affecting fields shown and submission logic.                                         |
    | `onSubmit`  | `(data: AuthFormData) => Promise<void>` | Yes       | N/A           | Async callback function when the form is submitted. `AuthFormData` will contain email, password, and optionally name/confirmPassword. |
    | `isLoading` | `boolean`                             | No        | `false`       | If true, disables the form and shows a loading state on the submit button.                                                                |
    | `serverError`| `string \| null`                        | No        | `null`        | Displays a general error message from the server above the form.                                                                            |
-   **Internal State (if any):** (Managed by React Hook Form + Zod typically)
    | State Variable     | Type         | Initial Value | Description                                                                                                                          |
    | :----------------- | :----------- | :------------ | :----------------------------------------------------------------------------------------------------------------------------------- |
    | `formData`         | `AuthFormData` | `{...empty}`  | Holds the current values of the input fields (email, name, password, confirmPassword). Typically managed by React Hook Form.       |
    | `validationErrors` | `object`     | `{}`          | Holds client-side validation errors for each field. Typically managed by React Hook Form integration with Zod.                         |
-   **Key UI Elements / Structure:**
    ```html
    <form onSubmit={handleSubmit(internalOnSubmit)}>
      <h2>{variant === 'login' ? 'Login' : 'Register'}</h2>
      {serverError && <p className="text-red-500">{serverError}</p>}

      {variant === 'register' && (
        <div>
          <label htmlFor="name">Name</label>
          <input type="text" id="name" {...register('name')} />
          {/* Display validation error for name */}
        </div>
      )}

      <div>
        <label htmlFor="email">Email</label>
        <input type="email" id="email" {...register('email')} />
        {/* Display validation error for email */}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input type="password" id="password" {...register('password')} />
        {/* Display validation error for password */}
      </div>

      {variant === 'register' && (
        <div>
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input type="password" id="confirmPassword" {...register('confirmPassword')} />
          {/* Display validation error for confirmPassword */}
        </div>
      )}

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Processing...' : (variant === 'login' ? 'Login' : 'Register')}
      </button>

      {variant === 'login' ? (
        <p>Don't have an account? <a href="/register">Register</a></p>
      ) : (
        <p>Already have an account? <a href="/login">Login</a></p>
      )}
    </form>
    ```
-   **Events Handled / Emitted:**
    -   **Handles:** `onSubmit` of the form element (triggers internal validation and then the `onSubmit` prop). Clicks on the toggle link (navigates user).
-   **Actions Triggered (Side Effects):**
    -   **State Management:** Updates local form state (managed by React Hook Form).
    -   **API Calls:** The `onSubmit` prop is expected to call the relevant authentication function (e.g., from `useAuth` hook or `authClient.ts`) which in turn calls the backend API (`POST /auth/login` or `POST /auth/register`).
-   **Styling Notes:**
    -   Form container: `max-w-md mx-auto p-6 bg-white rounded-lg shadow-xl mt-10`.
    -   Labels: `block text-sm font-medium text-gray-700 mb-1`.
    -   Inputs: `block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm`. (Shadcn/ui `<Input />` would be ideal here).
    -   Button: `w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`. (Shadcn/ui `<Button />` would be ideal).
    -   Error messages (client-side & server): `text-red-500 text-xs mt-1`.
-   **Accessibility Notes:**
    -   Each input MUST have a corresponding `<label>` with a `htmlFor` attribute matching the input's `id`.
    -   Inputs should have `aria-describedby` pointing to error message elements if applicable.
    -   Submit button is focusable and activated by Enter/Space.
    -   Form should have `aria-live="polite"` region for server error messages.
    -   Focus should be managed appropriately, e.g., on the first invalid field on submission error.

---

### Component: `EpisodeCard`

-   **Purpose:** Displays a summary of a single podcast episode, including its title, thumbnail, status, and actions like delete.
-   **Source File(s):** `frontend/src/components/episode/EpisodeCard.tsx`
-   **Visual Reference:** A card-like container. Shows a thumbnail image on one side, episode title, author/date, current processing status (with potential progress bar), and a delete button.
-   **Props (Properties):**
    | Prop Name | Type                                                                | Required? | Default Value | Description                                                                                                            |
    | :---------- | :------------------------------------------------------------------ | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------------------- |
    | `episode`   | `Episode` (from `frontend/src/types/index.ts`)                      | Yes       | N/A           | The episode object containing all its data.                                                                            |
    | `onDelete`  | `(episodeId: number) => Promise<void>`                              | Yes       | N/A           | Async callback function when the delete action is triggered for this episode.                                            |
    | `isDeleting`| `boolean`                                                           | No        | `false`       | If true, shows a loading/disabled state for the delete action specifically for this card.                                |
-   **Internal State (if any):**
    | State Variable | Type      | Initial Value | Description                                                                    |
    | :-------------- | :-------- | :------------ | :----------------------------------------------------------------------------- |
    | `showConfirmDelete` | `boolean` | `false`   | Controls visibility of a confirmation dialog/modal before actual deletion. |
-   **Key UI Elements / Structure:**
    ```html
    <div className="bg-white shadow-lg rounded-lg overflow-hidden flex flex-col md:flex-row">
      <img
        src={episode.thumbnailUrl || '/placeholder-thumbnail.png'}
        alt={`Thumbnail for ${episode.title}`}
        className="w-full md:w-1/3 h-48 md:h-auto object-cover"
      />
      <div className="p-4 flex-grow flex flex-col justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{episode.title}</h3>
          {episode.author && <p className="text-sm text-gray-600 mt-1">By: {episode.author}</p>}
          {episode.publishedAt && <p className="text-xs text-gray-500 mt-1">Published: {new Date(episode.publishedAt).toLocaleDateString()}</p>}
          <EpisodeProcessingStatus
            status={episode.processingStatus}
            errorMessage={episode.errorMessage}
            // progressPercentage={episode.progressPercentage} // If we add this to Episode type
          />
        </div>
        <div className="mt-4 flex justify-end">
          {/* Delete button would trigger showConfirmDelete state change */}
          <button
            onClick={() => setShowConfirmDelete(true)}
            disabled={isDeleting || episode.processingStatus !== 'completed' && episode.processingStatus !== 'failed'}
            className="text-red-500 hover:text-red-700 disabled:opacity-50"
            aria-label={`Delete episode ${episode.title}`}
          >
            {/* Icon for delete, e.g., Trash Can */}
            Delete
          </button>
        </div>
      </div>
      {/* Confirmation Modal/Dialog for delete would be rendered here based on showConfirmDelete */}
      {/* e.g., <ConfirmDeleteModal isOpen={showConfirmDelete} onConfirm={() => onDelete(episode.id)} onCancel={() => setShowConfirmDelete(false)} /> */}
    </div>
    ```
-   **Events Handled / Emitted:**
    -   **Handles:** `onClick` on the delete button (sets `showConfirmDelete` to true). Confirmation dialog would handle actual call to `onDelete` prop.
-   **Actions Triggered (Side Effects):**
    -   **API Calls:** The `onDelete` prop is expected to call a function (e.g., from `useEpisodes` hook) that triggers `DELETE /episodes/{episode.id}` via `apiClient.ts`.
-   **Styling Notes:**
    -   Main container: `bg-white shadow-lg rounded-lg overflow-hidden flex flex-col md:flex-row mb-4`.
    -   Thumbnail: `w-full md:w-1/3 h-48 md:h-auto object-cover`.
    -   Content section: `p-4 flex-grow flex flex-col justify-between`.
    -   Title: `text-lg font-semibold text-gray-800`.
    -   Delete button: `text-red-500 hover:text-red-700 disabled:opacity-50 px-3 py-1 rounded border border-red-500 hover:bg-red-50`. (Shadcn/ui `<Button variant="destructive">` could be used).
    -   Uses `EpisodeProcessingStatus` component for status display.
-   **Accessibility Notes:**
    -   Card container `role="listitem"` if part of a list, or `role="article"`.
    -   Thumbnail `alt` text MUST be descriptive.
    -   Delete button MUST have an `aria-label` providing context (e.g., "Delete episode [episode title]").
    -   Interactive elements like delete button MUST be focusable and operable with keyboard.
    -   If a confirmation modal is used, it MUST trap focus and handle Esc key for closing, and focus should return to the delete button (or next logical element) upon closing.

---

### Component: `EpisodeProcessingStatus`

-   **Purpose:** Displays the current processing status of an episode, including any progress or error messages.
-   **Source File(s):** `frontend/src/components/episode/EpisodeProcessingStatus.tsx`
-   **Visual Reference:** A small text display, possibly with an icon. Can show "Pending", "Processing Metadata...", "Downloading Audio (X%)", "Completed", "Error: [message]". May include a simple progress bar.
-   **Props (Properties):**
    | Prop Name             | Type                                          | Required? | Default Value | Description                                                                   |
    | :-------------------- | :-------------------------------------------- | :-------- | :------------ | :---------------------------------------------------------------------------- |
    | `status`              | `ProcessingStatus` (enum from `types/index.ts`) | Yes       | N/A           | The current processing status of the episode.                                   |
    | `errorMessage`        | `string \| null \| undefined`                 | No        | `null`        | An error message to display if the status is 'failed'.                        |
    | `progressPercentage`  | `number \| null \| undefined`                 | No        | `null`        | Optional progress percentage (0-100) for statuses like 'downloading_audio'. |
-   **Internal State (if any):** None significant.
-   **Key UI Elements / Structure:**
    ```html
    <div className="mt-2 text-sm">
      {status === 'pending' && <p className="text-gray-500">Status: Pending submission...</p>}
      {status === 'processing_metadata' && <p className="text-blue-500">Status: Fetching video details...</p>}
      {status === 'downloading_thumbnail' && <p className="text-blue-500">Status: Downloading thumbnail...</p>}
      {status === 'downloading_audio' && (
        <div>
          <p className="text-blue-500">Status: Downloading audio...</p>
          {typeof progressPercentage === 'number' && (
            <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1">
              <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progressPercentage}%` }}></div>
            </div>
          )}
        </div>
      )}
      {status === 'fetching_transcript' && <p className="text-blue-500">Status: Extracting transcript...</p>}
      {status === 'completed' && <p className="text-green-500">Status: Ready!</p>}
      {status === 'failed' && (
        <p className="text-red-500">
          Status: Failed. {errorMessage && `Error: ${errorMessage}`}
        </p>
      )}
    </div>
    ```
-   **Events Handled / Emitted:** None.
-   **Actions Triggered (Side Effects):** None.
-   **Styling Notes:**
    -   General text: `mt-2 text-sm`.
    -   Status-specific colors: `text-gray-500` (pending), `text-blue-500` (processing), `text-green-500` (completed), `text-red-500` (failed).
    -   Progress bar container: `w-full bg-gray-200 rounded-full h-2.5 mt-1`.
    -   Progress bar fill: `bg-blue-600 h-2.5 rounded-full`.
    -   Consider using icons alongside text for clearer visual indication (e.g., from `lucide-react` or a similar library if Shadcn/ui is used).
-   **Accessibility Notes:**
    -   Use `aria-live="polite"` on the container if statuses can change dynamically without a full page reload (which they will with SSE) to ensure screen readers announce updates.
    -   If a progress bar is used, it should have appropriate ARIA attributes: `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`.

---

### Component: `AddEpisodeForm`

-   **Purpose:** Allows authenticated users to submit a new YouTube URL to be processed into a podcast episode.
-   **Source File(s):** `frontend/src/components/forms/AddEpisodeForm.tsx`
-   **Visual Reference:** A simple form with one input field for the YouTube URL and a submit button. May show status messages (e.g., "Submitting...", "Episode submitted successfully!").
-   **Props (Properties):**
    | Prop Name        | Type                                    | Required? | Default Value | Description                                                                 |
    | :--------------- | :-------------------------------------- | :-------- | :------------ | :-------------------------------------------------------------------------- |
    | `onSubmit`       | `(youtubeUrl: string) => Promise<void>` | Yes       | N/A           | Async callback when the form is submitted with a valid YouTube URL.         |
    | `isLoading`      | `boolean`                               | No        | `false`       | If true, disables the form and shows a loading state on the submit button.  |
    | `submissionStatus` | `'idle' \| 'success' \| 'error'`    | No        | `'idle'`      | To display feedback messages after submission attempt.                      |
    | `errorMessage`   | `string \| null`                          | No        | `null`        | Error message to display if `submissionStatus` is 'error'.                  |
-   **Internal State (if any):** (Managed by React Hook Form + Zod)
    | State Variable | Type     | Initial Value | Description                                                                                    |
    | :------------- | :------- | :------------ | :--------------------------------------------------------------------------------------------- |
    | `youtubeUrl`   | `string` | `""`          | Current value of the YouTube URL input field. Managed by React Hook Form.                    |
    | `validationError`| `string \| null` | `null` | Client-side validation error for the URL field. Managed by React Hook Form + Zod. |
-   **Key UI Elements / Structure:**
    ```html
    <form onSubmit={handleSubmit(internalOnSubmit)} className="space-y-4">
      <div>
        <label htmlFor="youtubeUrl" className="block text-sm font-medium text-gray-700">YouTube Video URL</label>
        <input
          type="url"
          id="youtubeUrl"
          {...register('youtubeUrl')}
          placeholder="https://www.youtube.com/watch?v=..."
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
        {/* Display validationError for youtubeUrl */}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {isLoading ? 'Submitting...' : 'Add Episode'}
      </button>

      {submissionStatus === 'success' && <p className="text-green-600">Episode submitted! Processing has started.</p>}
      {submissionStatus === 'error' && <p className="text-red-600">{errorMessage || 'Failed to submit episode.'}</p>}
    </form>
    ```
-   **Events Handled / Emitted:**
    -   **Handles:** `onSubmit` of the form element.
-   **Actions Triggered (Side Effects):**
    -   **API Calls:** The `onSubmit` prop is expected to call a function (e.g., from `useEpisodes` hook) that triggers `POST /episodes` with the `youtubeUrl` payload via `apiClient.ts`.
-   **Styling Notes:**
    -   Form container: `space-y-4 p-6 bg-white rounded-lg shadow`.
    -   Label: `block text-sm font-medium text-gray-700`.
    -   Input: `mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm`. (Shadcn/ui `<Input />`).
    -   Button: `w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50`. (Shadcn/ui `<Button />`).
    -   Feedback messages: `text-green-600` or `text-red-600`.
-   **Accessibility Notes:**
    -   Input MUST have a corresponding `<label>` with `htmlFor`.
    -   Submit button is focusable and operable by keyboard.
    -   Feedback messages should be associated with an `aria-live` region (e.g., "polite" or "assertive" depending on urgency) if they appear/disappear dynamically.

---

### Component: `ChannelSettingsForm`

-   **Purpose:** Allows authenticated users to update the metadata (name, description, etc.) and logo for their podcast channel.
-   **Source File(s):** `frontend/src/components/forms/ChannelSettingsForm.tsx`
-   **Visual Reference:** A multi-field form. Sections for text inputs (name, description, website, language, category, authors, owner), a toggle for "explicit content," and a file input for the channel logo with a preview of the current logo.
-   **Props (Properties):**
    | Prop Name           | Type                                            | Required? | Default Value | Description                                                                                             |
    | :------------------ | :---------------------------------------------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------ |
    | `initialData`       | `Channel` (from `types/index.ts`)               | Yes       | N/A           | The current channel data to pre-fill the form.                                                          |
    | `onUpdateMetadata`  | `(data: ChannelUpdateData) => Promise<void>`    | Yes       | N/A           | Async callback when the textual metadata part of the form is submitted.                                 |
    | `onUpdateLogo`      | `(logoFile: File) => Promise<void>`             | Yes       | N/A           | Async callback when a new logo image is selected and ready for upload.                                    |
    | `isUpdatingMetadata`| `boolean`                                       | No        | `false`       | If true, disables the metadata section's submit button and shows loading.                               |
    | `isUpdatingLogo`    | `boolean`                                       | No        | `false`       | If true, disables the logo upload part and shows loading.                                               |
    | `metadataError`     | `string \| null`                                | No        | `null`        | Error message related to metadata update.                                                                 |
    | `logoError`         | `string \| null`                                | No        | `null`        | Error message related to logo update.                                                                     |
-   **Internal State (if any):** (Managed by React Hook Form + Zod for metadata; local state for logo preview)
    | State Variable | Type             | Initial Value         | Description                                                                                              |
    | :------------- | :--------------- | :-------------------- | :------------------------------------------------------------------------------------------------------- |
    | `metadataForm` | `ChannelUpdateData`| `initialData` (subset) | Current values for metadata fields. Managed by React Hook Form.                                        |
    | `logoPreviewUrl`| `string \| null` | `initialData.imageUrl`| URL for displaying a preview of the selected logo file before upload, or the current channel logo.         |
    | `selectedLogoFile`| `File \| null`   | `null`                | The new logo file selected by the user.                                                                  |
-   **Key UI Elements / Structure:**
    ```html
    <form onSubmit={handleMetadataSubmit(internalMetadataSubmit)} className="space-y-6">
      {/* Section 1: Channel Logo */}
      <div className="border-b pb-6">
        <h3 className="text-lg font-medium">Channel Logo</h3>
        <img src={logoPreviewUrl || '/default-channel-logo.png'} alt="Channel Logo Preview" className="w-32 h-32 rounded-md object-cover my-2" />
        <input type="file" accept="image/*" onChange={handleLogoFileChange} disabled={isUpdatingLogo} />
        <button type="button" onClick={handleLogoUpload} disabled={!selectedLogoFile || isUpdatingLogo}>
          {isUpdatingLogo ? 'Uploading Logo...' : 'Upload New Logo'}
        </button>
        {logoError && <p className="text-red-500">{logoError}</p>}
      </div>

      {/* Section 2: Channel Metadata */}
      <div>
        <h3 className="text-lg font-medium">Channel Details</h3>
        {/* Input for name, description, website, language, category, authors, owner_name, owner_email etc. */}
        {/* Example for 'name': */}
        <div>
          <label htmlFor="channelName">Channel Name</label>
          <input type="text" id="channelName" {...registerMetadata('name')} />
        </div>
        {/* ... other metadata fields ... */}
        <div>
          <label htmlFor="channelExplicit">Explicit Content</label>
          <input type="checkbox" id="channelExplicit" {...registerMetadata('explicit')} />
        </div>
        {metadataError && <p className="text-red-500">{metadataError}</p>}
        <button type="submit" disabled={isUpdatingMetadata}>
          {isUpdatingMetadata ? 'Saving Details...' : 'Save Channel Details'}
        </button>
      </div>
    </form>
    ```
-   **Events Handled / Emitted:**
    -   **Handles:** `onSubmit` for metadata section. `onChange` for logo file input. `onClick` for "Upload New Logo" button.
-   **Actions Triggered (Side Effects):**
    -   **API Calls:**
        *   `onUpdateMetadata` prop calls backend to update channel text details (`PUT /me/channel`).
        *   `onUpdateLogo` prop calls backend to upload new channel logo (`POST /me/channel/image`).
-   **Styling Notes:**
    -   Form: `space-y-6 p-6 bg-white rounded-lg shadow`.
    -   Section headings: `text-lg font-medium text-gray-900`.
    -   Inputs/Textareas/Selects: Use consistent styling (Shadcn/ui `<Input>`, `<Textarea>`, `<Switch>`, `<Select>`).
    -   Logo preview: `w-32 h-32 rounded-md object-cover my-2 border`.
    -   Buttons: Consistent styling (Shadcn/ui `<Button>`).
-   **Accessibility Notes:**
    -   All form inputs MUST have associated labels.
    -   File input should be keyboard accessible.
    -   Image preview should have appropriate `alt` text.
    -   Error messages should be linked to inputs via `aria-describedby`.
    -   Logical tabbing order through form fields and buttons.

---

This covers a few of the most significant custom components. Many other smaller, reusable UI primitives (buttons, inputs, modals, cards, etc.) would either come from a library like Shadcn/ui or be built as part of `frontend/src/components/ui/`. The level of detail here should allow an AI agent to generate the basic structure and functionality, which can then be refined.
