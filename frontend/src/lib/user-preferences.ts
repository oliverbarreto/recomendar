/**
 * User Preferences Storage Utility
 *
 * Manages user preferences in localStorage with SSR-safe operations.
 * Follows the same pattern as TokenStorage in auth-context.tsx.
 */

// Storage keys for user preferences
const PREFERENCE_KEYS = {
  PAGINATION_PAGE_SIZE: 'labcastarr_pagination_page_size',
} as const

// Valid page size options
const VALID_PAGE_SIZES = [10, 20, 50, 100] as const
type PageSize = typeof VALID_PAGE_SIZES[number]

// Default values
const DEFAULTS = {
  PAGE_SIZE: 20,
} as const

/**
 * Utility class for managing user preferences in localStorage
 */
export class UserPreferences {
  /**
   * Get the user's preferred page size for pagination
   * @returns The stored page size or default (20) if not set
   */
  static getPageSize(): number {
    if (typeof window === 'undefined') {
      return DEFAULTS.PAGE_SIZE
    }

    try {
      const stored = localStorage.getItem(PREFERENCE_KEYS.PAGINATION_PAGE_SIZE)

      if (!stored) {
        return DEFAULTS.PAGE_SIZE
      }

      const parsed = parseInt(stored, 10)

      // Validate that the stored value is one of the allowed page sizes
      if (VALID_PAGE_SIZES.includes(parsed as PageSize)) {
        return parsed
      }

      // If invalid, clear it and return default
      console.warn(`Invalid page size in localStorage: ${parsed}. Resetting to default.`)
      this.clearPageSize()
      return DEFAULTS.PAGE_SIZE
    } catch (error) {
      console.error('Error reading page size from localStorage:', error)
      return DEFAULTS.PAGE_SIZE
    }
  }

  /**
   * Set the user's preferred page size for pagination
   * @param size - The page size to store (must be 10, 20, 50, or 100)
   * @returns true if successful, false otherwise
   */
  static setPageSize(size: number): boolean {
    if (typeof window === 'undefined') {
      return false
    }

    // Validate the page size
    if (!VALID_PAGE_SIZES.includes(size as PageSize)) {
      console.error(`Invalid page size: ${size}. Must be one of: ${VALID_PAGE_SIZES.join(', ')}`)
      return false
    }

    try {
      localStorage.setItem(PREFERENCE_KEYS.PAGINATION_PAGE_SIZE, size.toString())
      return true
    } catch (error) {
      console.error('Error saving page size to localStorage:', error)
      return false
    }
  }

  /**
   * Clear the stored page size preference
   */
  static clearPageSize(): void {
    if (typeof window === 'undefined') {
      return
    }

    try {
      localStorage.removeItem(PREFERENCE_KEYS.PAGINATION_PAGE_SIZE)
    } catch (error) {
      console.error('Error clearing page size from localStorage:', error)
    }
  }

  /**
   * Clear all user preferences
   * Useful for logout or reset functionality
   */
  static clearAll(): void {
    if (typeof window === 'undefined') {
      return
    }

    try {
      Object.values(PREFERENCE_KEYS).forEach(key => {
        localStorage.removeItem(key)
      })
    } catch (error) {
      console.error('Error clearing user preferences:', error)
    }
  }
}

// Export constants for use in components
export { VALID_PAGE_SIZES, DEFAULTS }
export type { PageSize }
