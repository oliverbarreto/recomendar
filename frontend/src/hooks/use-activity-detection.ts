import { useEffect, useRef, useCallback } from 'react'

/**
 * Activity detection events to monitor
 *
 * Events that indicate user engagement:
 * - keypress: User is actively typing/interacting
 * - scroll: User is reading/browsing content
 * - touchstart: Mobile user is interacting with UI
 * - mousedown: User is clicking (more reliable than click)
 * - click: User is clicking buttons/links
 *
 * Note: mousemove is intentionally excluded as it's too noisy
 */
const ACTIVITY_EVENTS = [
    'keypress',
    'scroll',
    'touchstart',
    'mousedown',
    'click',
] as const

/**
 * Hook to detect user activity and trigger callbacks
 * 
 * @param onActivity - Callback function to execute when activity is detected
 * @param debounceMs - Minimum time between activity callbacks (default: 60000ms = 1 minute)
 * @returns Object with isActive state and manual trigger function
 */
export function useActivityDetection(
    onActivity?: () => void,
    debounceMs: number = 60000
) {
    const lastActivityRef = useRef<number>(Date.now())
    const timeoutRef = useRef<NodeJS.Timeout>()

    const handleActivity = useCallback(() => {
        const now = Date.now()
        const timeSinceLastActivity = now - lastActivityRef.current

        // Only trigger if enough time has passed since last activity
        if (timeSinceLastActivity >= debounceMs) {
            lastActivityRef.current = now
            onActivity?.()
        }

        // Clear existing timeout
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current)
        }

        // Set new timeout to detect inactivity
        timeoutRef.current = setTimeout(() => {
            // User is inactive
        }, debounceMs)
    }, [onActivity, debounceMs])

    useEffect(() => {
        // Add event listeners for activity detection
        ACTIVITY_EVENTS.forEach((event) => {
            window.addEventListener(event, handleActivity, { passive: true })
        })

        // Cleanup
        return () => {
            ACTIVITY_EVENTS.forEach((event) => {
                window.removeEventListener(event, handleActivity)
            })
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current)
            }
        }
    }, [handleActivity])

    return {
        manualTrigger: handleActivity,
    }
}

