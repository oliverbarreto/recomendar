# State Management

## Prompt used to generate this file
```markdown
Continuing with the frontend, lets focus on State Management In-Depth. This section should  expand on the State Management strategy and the the main aspects to consider in terms of state for the app

- **Chosen Solution:** Zustand
- **Decision Guide for State Location:**
    - **Global State (e.g., Redux/Zustand):** Data shared across many unrelated components; data persisting across routes; complex state logic managed via reducers/thunks. **MUST be used for session data, user preferences, application-wide notifications.**
    - **React Context API:** State primarily passed down a specific component subtree (e.g., theme, form context). Simpler state, fewer updates compared to global state. **MUST be used for localized state not suitable for prop drilling but not needed globally.**
    - **Local Component State (`useState`, `useReducer`):** UI-specific state, not needed outside the component or its direct children (e.g., form input values, dropdown open/close status). **MUST be the default choice unless criteria for Context or Global State are met.**

```

---

Okay, let's dive deep into the State Management strategy for the Next.js frontend, focusing on Zustand as the chosen global state solution and adhering to your decision guide for state location.

## Frontend State Management In-Depth

**Chosen Global Solution:** Zustand

**Justification for Zustand:**
Zustand is a small, fast, and scalable boilerplate-free state management solution built on simplified flux principles. It's known for:
*   **Simplicity and Minimal Boilerplate:** Easier to set up and use compared to Redux, requiring less code to achieve similar results.
*   **Performance:** Optimized for React, often leading to fewer re-renders.
*   **Flexibility:** Can be used with or without React Context. Supports middleware and devtools.
*   **Hooks-based API:** Feels very natural in a modern React/Next.js hooks-centric codebase.
*   **TypeScript Support:** Excellent TypeScript integration.

**Decision Guide for State Location (Reiterated for Clarity):**

1.  **Global State (Zustand Store):**
    *   **Criteria:** Data shared across many unrelated components, data that needs to persist across different routes/pages, complex state logic that benefits from centralized management, application-wide settings or data.
    *   **Mandatory Use Cases (as per your guide):**
        *   User Session Data (authentication status, user profile information).
        *   User Preferences (if any, e.g., theme preference if not handled by Next.js themes + CSS variables).
        *   Application-Wide Notifications/Toasts.
    *   **Other Potential Use Cases:**
        *   Caching fetched data that's used in multiple places and doesn't change frequently (though Next.js App Router's caching and server components might reduce the need for this).
        *   State for global modals or sidebars if their content/visibility is triggered from various parts of the app.

2.  **React Context API:**
    *   **Criteria:** State that needs to be passed down a specific component subtree without excessive prop drilling, but isn't truly global. Simpler state logic than what might go into Zustand, fewer updates.
    *   **Mandatory Use Cases (as per your guide):**
        *   Localized state not suitable for prop drilling but not needed globally.
    *   **Examples:**
        *   Theme context (if using a client-side theme switcher that affects a specific section).
        *   Context for a complex multi-step form if not using a dedicated form library that handles this internally.
        *   Context within a specific feature area if multiple components within that feature need to share state without polluting the global store.

3.  **Local Component State (`useState`, `useReducer`):**
    *   **Criteria:** UI-specific state that is not needed outside the component or its direct children. This is the default and most common type of state.
    *   **Mandatory Use Cases (as per your guide):**
        *   Default choice unless criteria for Context or Global State are met.
    *   **Examples:**
        *   Form input values before submission (often managed by libraries like React Hook Form, which use local state internally).
        *   Open/close status of dropdowns, modals (if the modal's trigger and content are closely related).
        *   Toggle states for UI elements.
        *   Loading/error states specific to a single component's data fetching.
        *   Data fetched by a component solely for its own rendering.

---

**Zustand Store Structure and Slices (Conceptual):**

We'll structure our Zustand store using "slices," a common pattern (though Zustand doesn't enforce it as strictly as Redux Toolkit). Each slice will manage a specific piece of the global state.

**File Structure (Example):**
```
frontend/
└── src/
    ├── store/
    │   ├── authStore.ts       // Manages authentication state, user profile
    │   ├── episodeStore.ts    // Manages episode list, SSE updates for statuses
    │   ├── notificationStore.ts // Manages global notifications/toasts
    │   └── index.ts           // Combines stores or exports hooks if needed (optional)
    └── hooks/
        ├── useAuthStore.ts    // Custom hook to access authStore
        ├── useEpisodeStore.ts // Custom hook to access episodeStore
        └── ...
```
Alternatively, and often simpler with Zustand, each store file (`authStore.ts`) directly exports its `useStore` hook.

**1. Auth Store (`store/authStore.ts`)**

*   **Purpose:** Manages user authentication state, the authenticated user's profile data, and related loading/error states.
*   **State:**
    *   `user: User | null`: The authenticated user object (from `types/index.ts`).
    *   `token: string | null`: The JWT.
    *   `isAuthenticated: boolean`: Derived from `token` and `user` presence.
    *   `isLoading: boolean`: True during login/registration API calls.
    *   `error: string | null`: Authentication-related error messages.
*   **Actions:**
    *   `login(credentials: UserLoginData): Promise<void>`:
        *   Sets `isLoading` to true.
        *   Calls `apiClient.login(credentials)`.
        *   On success: stores token (e.g., in an `httpOnly` cookie via a backend call or carefully in secure client storage if that's the strategy), fetches user profile, sets `user`, `token`, `isAuthenticated`, `isLoading` to false.
        *   On error: sets `error`, `isLoading` to false.
    *   `register(data: UserCreateData): Promise<void>`: Similar flow to login.
    *   `logout(): Promise<void>`:
        *   Clears `user`, `token`, `isAuthenticated`.
        *   Removes token from storage.
        *   (Optional) Calls a backend logout endpoint.
    *   `fetchUserProfile(): Promise<void>`: Fetches user profile if a token exists but user data isn't loaded.
    *   `setUser(user: User | null)`: Directly sets user (e.g., after profile update).
    *   `setToken(token: string | null)`: Directly sets token.
    *   `clearAuthError()`
*   **Usage:** Accessed via a custom hook `useAuthStore` (e.g., `const { user, login, isLoading } = useAuthStore();`).

**2. Episode Store (`store/episodeStore.ts`)**

*   **Purpose:** Manages the list of episodes for the authenticated user, handles real-time status updates from SSE, and manages loading/error states for episode-related actions.
*   **State:**
    *   `episodes: Episode[]`: List of episodes.
    *   `isLoadingEpisodes: boolean`: True when fetching the initial list of episodes.
    *   `episodeError: string | null`: Errors related to fetching or managing episodes.
    *   `sseConnectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'`: Status of the SSE connection.
    *   `episodeSubmissionStatus: { [youtubeUrl: string]: 'submitting' | 'submitted' | 'error' }`: Tracks status of *new* episode submissions before they get a proper ID and SSE updates.
*   **Actions:**
    *   `fetchEpisodes(): Promise<void>`:
        *   Sets `isLoadingEpisodes` to true.
        *   Calls `apiClient.getEpisodes()`.
        *   On success: sets `episodes`, `isLoadingEpisodes` to false.
        *   On error: sets `episodeError`, `isLoadingEpisodes` to false.
    *   `addEpisodeOptimistic(newEpisodeData: EpisodeCreateData)`: (Placeholder for optimistic UI, might be complex)
    *   `submitNewEpisode(youtubeUrl: string): Promise<{ success: boolean; episode?: Episode; error?: string }>`:
        *   Updates `episodeSubmissionStatus` for `youtubeUrl`.
        *   Calls `apiClient.submitEpisode({ youtubeUrl })`.
        *   On success from API (initial submission):
            *   Potentially add a placeholder to `episodes` or wait for first SSE update.
            *   Updates `episodeSubmissionStatus`.
            *   Returns success and the initial episode data if provided by API.
        *   On error: updates `episodeSubmissionStatus`, sets `episodeError`. Returns error.
    *   `deleteEpisode(episodeId: number): Promise<void>`:
        *   Optimistically remove from `episodes` list (or mark as deleting).
        *   Calls `apiClient.deleteEpisode(episodeId)`.
        *   On error: revert optimistic update, set `episodeError`.
    *   `handleSSEMessage(message: EpisodeStatusUpdateMessage): void`:
        *   Finds the episode in `episodes` by `message.episode_id`.
        *   Updates its `processingStatus`, `errorMessage`, `progressPercentage`, etc.
        *   If it's a new episode (first status update for it), add it to the list or update a placeholder.
    *   `setSSEConnectionStatus(status: 'disconnected' | 'connecting' | 'connected' | 'error')`
    *   `clearEpisodeError()`
*   **Usage:** Accessed via `useEpisodeStore`. The SSE hook (`useSSEConnection.ts`) would call `handleSSEMessage` and `setSSEConnectionStatus`.

**3. Notification Store (`store/notificationStore.ts`)**

*   **Purpose:** Manages a queue of global notifications or toasts to be displayed to the user.
*   **State:**
    *   `notifications: Array<{ id: string; message: string; type: 'success' | 'error' | 'info' | 'warning'; duration?: number }>`
*   **Actions:**
    *   `addNotification(notification: Omit<Notification, 'id'>): void`: Adds a new notification with a unique ID.
    *   `removeNotification(id: string): void`: Removes a notification.
    *   `clearNotifications(): void`
*   **Usage:** A global `<NotificationDisplay />` component would subscribe to this store and render active notifications. Various actions in other stores or components can call `addNotification`.

**Implementing State Updates via SSE in `episodeStore`:**

The `useSSEConnection` hook (e.g., `frontend/src/hooks/useSSEConnection.ts`) will be responsible for:
1.  Establishing the `EventSource` connection to the FastAPI backend's SSE endpoint (e.g., `/api/v1/episodes/status-stream`).
2.  Attaching the JWT to the `EventSource` request if needed (can be done by making the SSE endpoint require cookie auth or by passing the token as a query parameter if secure and necessary, though cookie is better).
3.  Listening to `message` events from the `EventSource`.
4.  When a message arrives, it parses the JSON data (which should be an `EpisodeStatusUpdateMessage`).
5.  It then calls an action from the `episodeStore`, like `episodeStore.getState().handleSSEMessage(parsedMessage)`.

**React Context API Usage Examples (as per guidelines):**

*   **Theme Context (If needed for a section, not globally):**
    *   If a specific part of the dashboard (e.g., a "focus mode" for an editor) needs its own theme toggler that doesn't affect the global app theme, Context is suitable.
    *   `contexts/FocusModeThemeContext.tsx`
*   **Complex Form Context (If not using React Hook Form's built-in context):**
    *   For a very large, multi-step form where intermediate state needs to be shared between steps *before* global submission, Context could be used. However, React Hook Form often handles this well enough with its own context.
*   **Modal Configuration Context:**
    *   If you have a generic modal component and different parts of the app need to open it with specific content and configurations, a `ModalContext` could manage `isOpen`, `modalContent`, `onClose` props.
        *   `contexts/ModalContext.tsx`
        *   State: `isOpen: boolean`, `content: ReactNode | null`, `modalProps: object`.
        *   Actions: `openModal(content, props)`, `closeModal()`.
        *   Zustand could also be used for this if modals are triggered from very disparate parts of the app. The choice depends on how "global" the modal triggers are.

**Local Component State (`useState`, `useReducer`) Examples:**

*   **`AuthForm.tsx`:**
    *   Input field values (if not using React Hook Form, though RHF is recommended and uses its own internal local state).
    *   Visibility of password.
*   **`EpisodeCard.tsx`:**
    *   `showConfirmDelete: boolean` (to show/hide a delete confirmation dialog specific to that card).
*   **`ChannelSettingsForm.tsx`:**
    *   `logoPreviewUrl: string | null` (to show a preview of an image before it's uploaded and its URL is persisted globally).
*   **Dropdowns, Accordions, Toggles:** Their open/closed state is almost always local component state.
*   **Data fetched by Server Components in Next.js App Router:** This data is effectively "props" to the server component and its children. If client components within that route need to interact with or manage parts of this data, it might be passed down as props, or small pieces of UI state related to it could be local.

**Decision Flow Summary for Developers/AI:**

1.  **Is this state for a single UI element's presentation (e.g., dropdown open)?** -> **Local State** (`useState`).
2.  **Is this state for a form's inputs and validation?** -> **React Hook Form** (uses local state internally) + Zod for schemas.
3.  **Does this state need to be shared between a parent and a few direct children, or within a clearly defined subtree, and isn't needed elsewhere?** -> **React Context API** (if prop drilling is too much) OR **Prop Drilling** (if simple).
4.  **Is this user session data (auth, profile)?** -> **Global State (Zustand `authStore`)**.
5.  **Are these application-wide notifications?** -> **Global State (Zustand `notificationStore`)**.
6.  **Is this data fetched from the API and used by multiple, unrelated components across different routes? (e.g., the list of all episodes for a user, updated by SSE)** -> **Global State (Zustand `episodeStore`)**.
7.  **Is the state logic complex and benefits from centralized actions/reducers, even if not used *everywhere*?** -> Consider **Global State (Zustand)** for better organization.

This detailed breakdown should provide clear guidance on how to approach state management throughout the frontend application, leveraging Zustand for global concerns and React's built-in mechanisms for more localized state.
