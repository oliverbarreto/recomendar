# Error Handling & Retries on the Frontend (Next.js)

## Prompt used to generate this file
```markdown
lets now provide the guidelines for Error Handling & Retries (Frontend)

- **Global Error Handling:** {How are API errors caught globally? (e.g., Via Axios response interceptor in `apiClient.ts`). How are they presented/logged? (e.g., Dispatches `uiSlice.actions.showGlobalErrorBanner({ message: error.message })`, logs detailed error to console/monitoring service). Is there a global error state? (e.g., `uiSlice.error`).}
- **Specific Error Handling:** {Components MAY handle specific API errors locally for more contextual feedback (e.g., displaying an inline message on a form field: "Invalid email address"). This MUST be documented in the component's specification if it deviates from global handling.}
- **Retry Logic:** {Is client-side retry logic implemented (e.g., using `axios-retry` with `apiClient`)? If so, specify configuration: max retries (e.g., 3), retry conditions (e.g., network errors, 5xx server errors), retry delay (e.g., exponential backoff). **MUST apply only to idempotent requests (GET, PUT, DELETE).**}

```

Okay, let's define the guidelines for Error Handling and Retries on the frontend (Next.js). This is crucial for creating a resilient and user-friendly application.

---


## Frontend Error Handling & Retries Guidelines

**1. Global Error Handling:**

*   **Mechanism:** API errors will be caught globally via an interceptor in the `apiClient.ts` utility (which wraps `fetch` or uses a library like `axios` that supports interceptors).
    *   **If using `fetch` directly:** A wrapper function around `fetch` will be created. This wrapper will make the actual `fetch` call, then check `response.ok`. If not `ok`, it will attempt to parse an error response (assuming the backend sends a JSON body like `{"detail": "Error message"}`), construct a standardized error object, and then throw it.
    *   **If using `axios`:** An `axios.interceptors.response.use(response => response, error => { ... })` will be configured.
*   **Error Object Standardization:** The `apiClient.ts` will ensure that errors thrown or propagated from API calls are standardized, perhaps an instance of a custom `ApiError` class or an object with consistent properties like:
    ```typescript
    interface StandardizedApiError {
      message: string;          // User-friendly message if available, or generic
      statusCode?: number;      // HTTP status code
      errorCode?: string;       // Backend-defined error code, if any
      details?: any;            // More specific error details from backend
      isNetworkError?: boolean; // True if it's a network issue, not an HTTP error
    }
    ```
*   **Presentation/Logging:**
    *   **Global Notifications:** Unhandled or globally significant errors caught by the interceptor will trigger a global notification. This will be done by dispatching an action to the `notificationStore` (Zustand).
        *   Example: `notificationStore.getState().addNotification({ message: extractedErrorMessage, type: 'error' });`
    *   **Console Logging:** Detailed error information (the full `StandardizedApiError` object, stack trace if available) WILL BE logged to the browser console (`console.error()`) for debugging during development.
    *   **Monitoring Service (Production):** In a production environment, these detailed errors SHOULD BE logged to an external monitoring service (e.g., Sentry, LogRocket, Datadog RUM). This would be integrated within the global error handler in `apiClient.ts` or a higher-level error boundary.
*   **Global Error State:**
    *   The `notificationStore` will manage the visible global error messages (toasts/banners).
    *   A specific "global error page" or a persistent "critical error" state in a UI slice is NOT planned for initial implementation unless a specific API failure mode requires the entire app to be in an error state (which is rare for this type of application). Most errors will be handled via notifications, allowing the user to continue interacting with other parts of the app if possible.

**2. Specific Error Handling:**

*   **Component-Level Responsibility:** Components or hooks initiating an API call (e.g., a form submission component, a data-fetching hook) MAY `try...catch` the promise returned by `apiClient.ts` functions to handle errors in a more context-specific way *before* they are caught by the global interceptor (or in addition to it).
*   **Contextual Feedback:**
    *   **Forms:** For form submissions, errors related to specific fields (e.g., "Email already taken," "Invalid YouTube URL") returned by the backend (ideally with field identifiers in the error response) SHOULD BE displayed as inline error messages next to the respective form fields. The `AuthForm` or `AddEpisodeForm` would catch the error, parse it, and set local state to display these messages.
        *   Example: If `apiClient.login()` throws an error, the login component catches it:
            ```typescript
            // In Login Page/Component
            const { login } = useAuthStore(); // Or a dedicated auth hook
            try {
              await login(formData);
              // Redirect on success
            } catch (error: any) {
              if (error.statusCode === 400 && error.details?.field === 'email') {
                setInlineEmailError(error.details.message);
              } else {
                setGlobalFormError(error.message || 'Login failed.');
                // Global handler in apiClient will also show a toast if not caught and re-thrown carefully
              }
            }
            ```
    *   **Data Display Components:** If a component fails to fetch its primary data, it might display a "Could not load [data]. Try refreshing." message inline, instead of just relying on a global toast.
*   **Preventing Double Notification:** If a component handles an error locally and displays contextual feedback, it should ideally prevent the global handler from also showing a generic toast for the same error. This can be achieved by:
    *   The `apiClient` functions could return a more structured result like `{ data: T | null, error: StandardizedApiError | null }` instead of always throwing. Components then check the `error` property.
    *   Or, if `apiClient` *does* throw, the component catches it, handles it, and does *not* re-throw it if it's fully handled. If it only partially handles it (e.g., logs it but can't show UI), it can re-throw. This needs careful design in `apiClient.ts`. A common pattern is for `apiClient` to always throw on error, and the global interceptor handles it unless the component's catch block specifically signals it's been handled (which is harder to implement cleanly).
    *   **Simpler approach for now:** `apiClient` throws. Global interceptor shows a toast. Components can *additionally* show inline messages by catching the error. The user might see two messages (toast + inline), which is often acceptable if the inline one is more specific.

**3. Retry Logic:**

*   **Implementation:** Client-side retry logic WILL BE implemented for certain types of API requests. This will be centralized in `apiClient.ts`.
    *   **If using `axios`:** `axios-retry` is a good library for this.
    *   **If using `fetch`:** A custom retry wrapper around `fetch` will be implemented.
*   **Configuration:**
    *   **Max Retries:** 3 (a common default).
    *   **Retry Conditions:**
        *   Network errors (e.g., DNS lookup failed, connection refused).
        *   5xx HTTP server errors (e.g., `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`). These are often transient.
        *   Possibly `429 Too Many Requests` if the backend uses it and a short retry is appropriate.
    *   **Retry Delay:** Exponential backoff with jitter.
        *   Example: 1st retry after 1s, 2nd after 2s, 3rd after 4s (plus a small random jitter to avoid thundering herd).
    *   **Idempotency:** Retry logic MUST strictly apply only to **idempotent requests**:
        *   `GET`
        *   `PUT` (if the backend endpoint is designed to be idempotent, which it should be for updates)
        *   `DELETE` (if the backend endpoint is designed to be idempotent, e.g., returns 404 if already deleted, not an error)
    *   **Non-Idempotent Requests (`POST`):** `POST` requests (like submitting a new episode, user registration) will generally NOT be retried automatically by the client to avoid creating duplicate resources. If a `POST` fails due to a network error, the user should be informed and may need to manually retry the action. The UI should provide clear feedback and potentially disable the submit button during the request and after a failure to prevent accidental multiple submissions.

**Summary of Error Handling Flow:**

1.  Component/Hook initiates an API call via `apiClient.ts`.
2.  `apiClient.ts` executes the request.
    *   If retry logic is configured for this request type/error:
        *   Automatic retries are attempted if initial request fails under specified conditions.
3.  If the request ultimately fails (after retries or if no retries for this type):
    *   `apiClient.ts` standardizes the error.
    *   The promise returned by `apiClient.ts` is rejected with the standardized error.
4.  **Specific Handling (Optional):**
    *   The calling component/hook can `try...catch` this error.
    *   If caught, it can update its local state to display context-specific error messages (e.g., inline form errors).
5.  **Global Handling (Default):**
    *   If the error is not caught by the component (or is re-thrown), the global error interceptor in `apiClient.ts` catches it.
    *   The global interceptor dispatches an action to `notificationStore` to display a user-friendly toast/banner.
    *   The global interceptor logs the detailed error to the console and (in production) to a monitoring service.

This layered approach ensures that users receive immediate contextual feedback where possible, and a global system catches and notifies about any other errors, while developers get the necessary details for debugging. The retry logic improves resilience against transient network or server issues for appropriate requests.
