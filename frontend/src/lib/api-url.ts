/**
 * Centralized API URL resolution utility
 *
 * Provides a single source of truth for determining the API base URL
 * across all frontend components and contexts.
 *
 * REQUIRED: NEXT_PUBLIC_API_URL must be set in environment configuration
 * - Production: Set to your API domain (e.g., https://api.yourdomain.com)
 * - Development: Set to http://localhost:8000 (or your dev server)
 */

/**
 * Get the API base URL from environment configuration
 *
 * @returns The API base URL to use for all API requests
 * @throws Error if NEXT_PUBLIC_API_URL is not configured in production
 */
export const getApiBaseUrl = (): string => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  // If configured, use it (production and development)
  if (apiUrl) {
    return apiUrl
  }

  // In development mode, provide a helpful fallback to localhost
  if (process.env.NODE_ENV === 'development') {
    console.warn(
      '⚠️  NEXT_PUBLIC_API_URL not set. Defaulting to http://localhost:8000\n' +
      '   For production builds, you MUST set NEXT_PUBLIC_API_URL in .env.production'
    )
    return 'http://localhost:8000'
  }

  // In production, this is a FATAL configuration error
  throw new Error(
    '❌ CONFIGURATION ERROR: NEXT_PUBLIC_API_URL is not set.\n\n' +
    'Please set NEXT_PUBLIC_API_URL in your .env.production file.\n' +
    'Example: NEXT_PUBLIC_API_URL=https://api.yourdomain.com\n\n' +
    'See documentation for more details.'
  )
}

/**
 * Get the full API URL for a given endpoint
 *
 * @param endpoint - The API endpoint path (should start with /)
 * @returns The full URL for the API endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl()
  const sanitizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${sanitizedEndpoint}`
}

/**
 * Log API configuration for debugging purposes
 * Useful for troubleshooting environment-specific issues
 */
export const logApiConfig = (): void => {
  if (typeof window !== 'undefined') {
    console.log('🔧 API Configuration:', {
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '(not set)',
      NODE_ENV: process.env.NODE_ENV,
      resolvedApiUrl: getApiBaseUrl(),
      windowLocation: window.location.origin,
      windowProtocol: window.location.protocol,
    })
  }
}
