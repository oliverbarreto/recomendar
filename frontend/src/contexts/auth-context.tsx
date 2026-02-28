'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { User, LoginRequest } from '@/types'
import { authApi } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/api-url'
import { useActivityDetection } from '@/hooks/use-activity-detection'

// Transform backend user data (snake_case) to frontend format (camelCase)
function transformUserData(backendUser: any): User {
  return {
    id: backendUser.id,
    name: backendUser.name,
    email: backendUser.email,
    isAdmin: backendUser.is_admin,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at
  }
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isRefreshing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage utilities
const TOKEN_KEYS = {
  ACCESS_TOKEN: 'labcastarr_access_token',
  REFRESH_TOKEN: 'labcastarr_refresh_token',
  USER: 'labcastarr_user'
}

class TokenStorage {
  static setTokens(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
      localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    }
  }

  static getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
    }
    return null
  }

  static getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
    }
    return null
  }

  static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
    }
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(TOKEN_KEYS.USER)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static clearAll() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.USER)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    return !!(accessToken && refreshToken)
  }

  static isAccessTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true
    
    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
      return Date.now() >= (exp - bufferMs)
    } catch {
      return true // If we can't parse, consider expired
    }
  }

  static isRefreshTokenExpired(): boolean {
    const token = this.getRefreshToken()
    if (!token) return true
    
    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch {
      return true // If we can't parse, consider expired
    }
  }
}

// Custom API request function that includes JWT token
async function authenticatedApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = TokenStorage.getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  }

  // Add Authorization header if we have an access token
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const API_BASE_URL = getApiBaseUrl()
  const response = await fetch(`${API_BASE_URL}/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Memoized refresh function for activity detection
  const refreshToken = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      // Update stored tokens - use new refresh token if provided, otherwise keep existing (backward compatibility)
      const newRefreshToken = data.refresh_token || refreshTokenValue
      TokenStorage.setTokens(data.access_token, newRefreshToken)
      
      // Log token rotation for debugging
      if (data.refresh_token) {
        console.debug('Token rotated: new refresh token received')
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Activity-based token refresh (every 5 minutes of activity)
  useActivityDetection(
    user ? refreshToken : undefined,
    5 * 60 * 1000 // Refresh on activity every 5 minutes
  )

  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        const refreshTokenValue = TokenStorage.getRefreshToken()
        
        // CRITICAL: Refresh token BEFORE validation if refresh token exists
        // This allows inactive users to return after hours/days and stay logged in
        if (refreshTokenValue) {
          try {
            await refreshToken()
          } catch (refreshError) {
            // Refresh failed - refresh token expired or invalid
            console.error('Token refresh failed on initialization:', refreshError)
            TokenStorage.clearAll()
            setIsLoading(false)
            return
          }
        }

        // Now validate with fresh access token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [refreshToken])

  // Auto-refresh token functionality
  // Refresh at 80% of token lifetime (60 min * 0.8 = 48 min)
  useEffect(() => {
    if (!user) return

    const TOKEN_LIFETIME_MINUTES = 60 // Should match backend jwt_access_token_expire_minutes
    const REFRESH_PERCENTAGE = 0.8 // Refresh at 80% of token lifetime
    const refreshIntervalMs = TOKEN_LIFETIME_MINUTES * REFRESH_PERCENTAGE * 60 * 1000

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
        // If refresh fails, log out the user
        await logout()
      }
    }, refreshIntervalMs) // Refresh every 48 minutes (access token expires in 60)

    return () => clearInterval(refreshInterval)
  }, [user, refreshToken])

  // Smart window focus handler - refreshes token when user returns to tab
  // Only refreshes if token is expired/expiring soon, prevents excessive refreshes
  useEffect(() => {
    if (!user) return
    
    let lastFocusRefresh = 0
    const MIN_FOCUS_REFRESH_INTERVAL = 5 * 60 * 1000 // 5 minutes
    
    const handleFocus = async () => {
      // Only refresh if enough time has passed since last focus refresh
      const now = Date.now()
      if (now - lastFocusRefresh < MIN_FOCUS_REFRESH_INTERVAL) {
        return
      }
      
      // Only refresh if token is expired or expiring soon
      if (!TokenStorage.hasValidTokens() || !TokenStorage.isAccessTokenExpired()) {
        return
      }
      
      try {
        await refreshToken()
        lastFocusRefresh = now
      } catch (error) {
        // Refresh failed, but don't log out immediately
        // Let the next API call or initialization handle it
        console.warn('Focus refresh failed:', error)
      }
    }
    
    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [user, refreshToken])

  // REMOVED: Window focus refresh was too aggressive
  // This was triggering refreshes on every click between DevTools and page,
  // causing state loss and poor UX. The auto-refresh timer (every 48 min) is sufficient.
  //
  // useEffect(() => {
  //   const handleFocus = async () => {
  //     if (user && TokenStorage.hasValidTokens()) {
  //       try {
  //         await refreshToken()
  //       } catch (error) {
  //         console.error('Focus refresh failed:', error)
  //         await logout()
  //       }
  //     }
  //   }
  //
  //   window.addEventListener('focus', handleFocus)
  //   return () => window.removeEventListener('focus', handleFocus)
  // }, [user])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)

      // Call backend login endpoint directly
      const apiUrl = getApiBaseUrl()
      console.log('Login API URL:', apiUrl) // Debug logging for Safari troubleshooting

      const response = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()

        // Handle different error formats
        let errorMessage = 'Login failed'
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Handle FastAPI validation errors (array format)
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ')
        } else if (errorData.message) {
          errorMessage = errorData.message
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Store tokens and user data
      TokenStorage.setTokens(data.access_token, data.refresh_token)
      const transformedUser = transformUserData(data.user)
      TokenStorage.setUser(transformedUser)
      setUser(transformedUser)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (refreshTokenValue) {
        // Call backend logout endpoint
        await authenticatedApiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshTokenValue }),
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if backend call fails
    } finally {
      // Clear local storage and state
      TokenStorage.clearAll()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isRefreshing,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook to get the current access token
export function useAccessToken() {
  return TokenStorage.getAccessToken()
}

// Export token storage for use in API client
export { TokenStorage, authenticatedApiRequest }