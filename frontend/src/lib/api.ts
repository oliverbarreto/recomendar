/**
 * API client for LabCastARR backend communication
 */
import {
  User, Channel, Episode, Tag, Event,
  ApiResponse, PaginatedResponse,
  CreateEpisodeRequest, UpdateEpisodeRequest,
  ChannelSettingsRequest, EpisodeStatus,
  HealthResponse, DetailedHealthResponse,
  LoginRequest, RegisterRequest, AuthResponse,
  CreateTagRequest, UpdateTagRequest,
  UserProfileRequest, PasswordChangeRequest,
  EpisodeSearchParams, EventFilterParams,
  EventType, EventStatus,
  ChannelCreateRequest, ChannelUpdateRequest,
  ChannelStatistics, FeedValidationResponse, FeedInfoResponse,
  SearchRequest, SearchResponse, SearchSuggestion, TagSuggestionsResponse
} from '@/types'
import { errorLogger } from './error-logging'
import { getApiBaseUrl, logApiConfig } from './api-url'

// Log API configuration on load for debugging (especially useful in production)
if (typeof window !== 'undefined') {
  logApiConfig()
}

const API_BASE_URL = getApiBaseUrl()
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'dev-secret-key-change-in-production'

class ApiError extends Error {
  constructor(public status: number, message: string, public response?: unknown) {
    super(message)
    this.name = 'ApiError'
  }
}

// Security utilities
const sanitizeInput = (input: string): string => {
  // Basic input sanitization
  return input
    .replace(/[<>]/g, '') // Remove basic HTML characters
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
    .slice(0, 1000) // Limit length
}

const validateUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

// Token storage utility for client-side access
const getAccessToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('labcastarr_access_token')
  }
  return null
}

// Check if access token is expired or expiring soon
const isAccessTokenExpired = (): boolean => {
  const token = getAccessToken()
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

// Global refresh promise to prevent duplicate refresh attempts
let refreshPromise: Promise<string | null> | null = null

/**
 * Perform token refresh with deduplication
 * Returns the new access token or null if refresh failed
 */
async function performTokenRefresh(): Promise<string | null> {
  const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('labcastarr_refresh_token') : null

  if (!refreshToken) {
    return null
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (response.ok) {
      const refreshData = await response.json()
      // Update the stored access token and refresh token (if provided)
      if (typeof window !== 'undefined') {
        localStorage.setItem('labcastarr_access_token', refreshData.access_token)
        // Store new refresh token if provided, otherwise keep existing (backward compatibility)
        if (refreshData.refresh_token) {
          localStorage.setItem('labcastarr_refresh_token', refreshData.refresh_token)
        }
      }
      return refreshData.access_token
    }

    return null
  } catch (error) {
    console.error('Token refresh error:', error)
    return null
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Validate endpoint
  if (!endpoint || typeof endpoint !== 'string') {
    throw new ApiError(400, 'Invalid endpoint')
  }

  // Sanitize endpoint
  const sanitizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${sanitizedEndpoint}`

  // Validate constructed URL
  if (!validateUrl(url)) {
    throw new ApiError(400, 'Invalid URL')
  }

  // Prepare secure headers
  const secureHeaders: HeadersInit = {
    'X-API-Key': API_KEY,
    'X-Requested-With': 'XMLHttpRequest', // CSRF protection
    ...options.headers,
  }

  // Add JWT token if available (for authenticated endpoints)
  // Check if token is expired and refresh proactively before making request
  let accessToken = getAccessToken()
  if (accessToken && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
    // Proactive refresh if token is expired or expiring soon
    if (isAccessTokenExpired()) {
      // Attempt refresh before making the request
      const newAccessToken = await performTokenRefresh()
      if (newAccessToken) {
        accessToken = newAccessToken
      } else {
        // Refresh failed, clear tokens
        if (typeof window !== 'undefined') {
          localStorage.removeItem('labcastarr_access_token')
          localStorage.removeItem('labcastarr_refresh_token')
          localStorage.removeItem('labcastarr_user')
        }
      }
    }
    
    if (accessToken) {
      secureHeaders['Authorization'] = `Bearer ${accessToken}`
    }
  }

  // Don't set Content-Type for FormData (let browser set it with boundary)
  if (!(options.body instanceof FormData)) {
    secureHeaders['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    headers: secureHeaders,
    credentials: 'same-origin', // Only send cookies to same origin
    ...options,
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }

    // Handle authentication errors with optimized refresh logic
    if (response.status === 401 && accessToken && !endpoint.includes('/auth/')) {
      // Use cached refresh promise to prevent multiple simultaneous refreshes
      if (!refreshPromise) {
        refreshPromise = performTokenRefresh()
      }

      try {
        const newAccessToken = await refreshPromise
        refreshPromise = null // Reset cache after completion

        if (newAccessToken) {
          // Retry the original request with new token
          const retryHeaders = { ...secureHeaders, 'Authorization': `Bearer ${newAccessToken}` }
          const retryResponse = await fetch(url, {
            ...options,
            headers: retryHeaders,
            credentials: 'same-origin',
          })

          if (retryResponse.ok) {
            const contentType = retryResponse.headers.get('content-type')
            if (contentType && contentType.includes('application/json')) {
              return retryResponse.json()
            }
            return retryResponse.text() as unknown as T
          }
        } else {
          // Refresh failed, clear tokens and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('labcastarr_access_token')
            localStorage.removeItem('labcastarr_refresh_token')
            localStorage.removeItem('labcastarr_user')
          }
        }
      } catch (refreshError) {
        refreshPromise = null // Reset cache on error
        // Clear tokens on refresh failure
        if (typeof window !== 'undefined') {
          localStorage.removeItem('labcastarr_access_token')
          localStorage.removeItem('labcastarr_refresh_token')
          localStorage.removeItem('labcastarr_user')
        }
        console.error('Token refresh failed:', refreshError)
      }
    }

    // Log API errors with security context
    errorLogger.logApiError(
      sanitizedEndpoint,
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )

    throw new ApiError(
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )
  }

  // Handle different response types
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

// Authentication API
export const authApi = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async logout(): Promise<void> {
    await apiRequest<void>('/auth/logout', {
      method: 'POST',
    })
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>('/auth/me')
    return response.data
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>('/auth/refresh', {
      method: 'POST',
    })
    return response.data
  }
}

// User API
export const userApi = {
  async getProfile(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>('/v1/users/profile')
    return response.data
  },

  async updateProfile(data: UserProfileRequest): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>('/v1/users/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiRequest<void>('/v1/users/password', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  async deleteAccount(): Promise<void> {
    await apiRequest<void>('/v1/users/profile', {
      method: 'DELETE',
    })
  }
}

// Health API
export const healthApi = {
  async check(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>('/health/')
  },

  async checkDatabase(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>('/health/db')
  },

  async checkDetailed(): Promise<DetailedHealthResponse> {
    return apiRequest<DetailedHealthResponse>('/health/detailed')
  }
}

// Episode API
export const episodeApi = {
  async getAll(channelId: number, params?: Omit<EpisodeSearchParams, 'channelId'>): Promise<PaginatedResponse<Episode>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 50).toString(),
    })

    if (params?.query) searchParams.set('q', params.query)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.tags?.length) searchParams.set('tags', params.tags.join(','))
    if (params?.startDate) searchParams.set('start_date', params.startDate)
    if (params?.endDate) searchParams.set('end_date', params.endDate)

    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/v1/episodes/?${searchParams.toString()}`
    )
    return response
  },

  async getById(id: number): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`)
    return response
  },

  async create(data: CreateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>('/v1/episodes/', {
      method: 'POST',
      body: JSON.stringify({
        channel_id: data.channel_id,
        video_url: sanitizeInput(data.video_url),
        tags: data.tags || [],
        audio_language: data.audio_language || null,
        audio_quality: data.audio_quality || null,
      }),
    })
    return response
  },

  async update(id: number, data: UpdateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        keywords: data.keywords,
        tags: data.tags
      }),
    })
    return response
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/v1/episodes/${id}`, {
      method: 'DELETE',
    })
  },

  async updateStatus(id: number, status: EpisodeStatus): Promise<Episode> {
    const response = await apiRequest<ApiResponse<Episode>>(`/v1/episodes/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    })
    return response.data
  },

  async getStatus(id: number): Promise<{ status: EpisodeStatus, progress?: number }> {
    const response = await apiRequest<ApiResponse<{ status: EpisodeStatus, progress?: number }>>(
      `/v1/episodes/${id}/status`
    )
    return response.data
  },

  async getByStatus(status: EpisodeStatus): Promise<Episode[]> {
    const response = await apiRequest<ApiResponse<Episode[]>>(`/v1/episodes/by-status?status=${status}`)
    return response.data
  },

  async analyzeYouTubeVideo(videoUrl: string): Promise<{
    video_id: string
    title: string
    description: string
    duration_seconds?: number
    thumbnail_url?: string
    uploader?: string
    view_count: number
    publication_date?: string
    keywords: string[]
    video_url: string
    availability?: string
  }> {
    const response = await apiRequest<{
      video_id: string
      title: string
      description: string
      duration_seconds?: number
      thumbnail_url?: string
      uploader?: string
      view_count: number
      publication_date?: string
      keywords: string[]
      video_url: string
      availability?: string
    }>('/v1/episodes/analyze', {
      method: 'POST',
      body: JSON.stringify({ video_url: sanitizeInput(videoUrl) }),
    })
    return response
  },

  async getProgress(id: number): Promise<{
    episode_id: number
    status: string
    percentage: string
    speed: string
    eta: string
    downloaded_bytes: number
    total_bytes: number
    error_message?: string
    started_at?: string
    completed_at?: string
    updated_at: string
  }> {
    const response = await apiRequest<{
      episode_id: number
      status: string
      percentage: string
      speed: string
      eta: string
      downloaded_bytes: number
      total_bytes: number
      error_message?: string
      started_at?: string
      completed_at?: string
      updated_at: string
    }>(`/v1/episodes/${id}/progress`)
    return response
  },

  async favorite(id: number): Promise<{ message: string, data: { episode_id: number, is_favorited: boolean } }> {
    const response = await apiRequest<{ message: string, data: { episode_id: number, is_favorited: boolean } }>(
      `/v1/episodes/${id}/favorite`,
      { method: 'POST' }
    )
    return response
  },

  async unfavorite(id: number): Promise<{ message: string, data: { episode_id: number, is_favorited: boolean } }> {
    const response = await apiRequest<{ message: string, data: { episode_id: number, is_favorited: boolean } }>(
      `/v1/episodes/${id}/favorite`,
      { method: 'DELETE' }
    )
    return response
  },

  async redownload(id: number): Promise<{ message: string, data: { episode_id: number } }> {
    const response = await apiRequest<{ message: string, data: { episode_id: number } }>(
      `/v1/episodes/${id}/retry`,
      { method: 'POST' }
    )
    return response
  },

  async getCount(channelId: number = 1): Promise<{
    success: boolean
    channel_id: number
    episode_count: number
    message: string
  }> {
    const response = await apiRequest<{
      success: boolean
      channel_id: number
      episode_count: number
      message: string
    }>(`/v1/episodes/stats/count?channel_id=${channelId}`)
    return response
  },

  async bulkDeleteAll(
    channelId: number = 1,
    options: {
      dryRun?: boolean
      confirmToken?: string
      timeout?: number
      maxRetries?: number
    } = {}
  ): Promise<{
    success: boolean
    total_episodes: number
    deleted_episodes: number
    failed_episodes: number
    deleted_files: number
    failed_files: number
    partial_completion: boolean
    error_message?: string
    failed_episode_details?: Array<{
      episode_id: number
      title: string
      errors: string[]
    }>
    message: string
    channel_id: number
    dry_run: boolean
    timestamp: string
  }> {
    const {
      dryRun = false,
      confirmToken,
      timeout = 300000, // 5 minutes default
      maxRetries = 3
    } = options

    // Build query parameters
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      dry_run: dryRun.toString()
    })

    if (confirmToken) {
      params.set('confirm_token', confirmToken)
    }

    const endpoint = `/v1/episodes/actions/bulk-delete-all?${params.toString()}`

    // Retry logic with exponential backoff
    let lastError: Error | null = null
    let retryDelay = 1000 // Start with 1 second

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await apiRequest<{
          success: boolean
          total_episodes: number
          deleted_episodes: number
          failed_episodes: number
          deleted_files: number
          failed_files: number
          partial_completion: boolean
          error_message?: string
          failed_episode_details?: Array<{
            episode_id: number
            title: string
            errors: string[]
          }>
          message: string
          channel_id: number
          dry_run: boolean
          timestamp: string
        }>(endpoint, {
          method: 'DELETE',
          signal: AbortSignal.timeout(timeout)
        })

        return response

      } catch (error) {
        lastError = error as Error
        const isApiError = error instanceof ApiError
        const isNetworkError = error instanceof TypeError && error.message.includes('fetch')
        const isTimeoutError = error instanceof DOMException && error.name === 'TimeoutError'

        // Log the error with context
        errorLogger.logApiError(
          endpoint,
          isApiError ? (error as ApiError).status : 0,
          `Bulk deletion attempt ${attempt}/${maxRetries} failed: ${error.message}`,
          {
            attempt,
            maxRetries,
            channelId,
            dryRun,
            errorType: isApiError ? 'api' : isNetworkError ? 'network' : isTimeoutError ? 'timeout' : 'unknown'
          }
        )

        // Determine if we should retry
        const shouldRetry = attempt < maxRetries && (
          isNetworkError ||
          isTimeoutError ||
          (isApiError && [408, 429, 500, 502, 503, 504].includes((error as ApiError).status))
        )

        if (!shouldRetry) {
          // Don't retry for client errors (400-499) except 408 (timeout) and 429 (rate limit)
          break
        }

        if (attempt < maxRetries) {
          // Wait before retrying with exponential backoff
          await new Promise(resolve => setTimeout(resolve, retryDelay))
          retryDelay *= 2 // Double the delay for next attempt
        }
      }
    }

    // If we get here, all retries failed
    if (lastError instanceof ApiError) {
      // Enhanced error information for API errors
      const errorData = lastError.response as any
      throw new ApiError(
        lastError.status,
        `Bulk deletion failed after ${maxRetries} attempts: ${lastError.message}`,
        {
          ...errorData,
          attempts: maxRetries,
          finalError: true,
          channelId,
          dryRun
        }
      )
    } else {
      // Network or other errors
      throw new Error(
        `Bulk deletion failed after ${maxRetries} attempts: ${lastError?.message || 'Unknown error'}. ` +
        'Please check your internet connection and try again.'
      )
    }
  }
}

// Channel API
export const channelApi = {
  async getAll(params?: { user_id?: number, search?: string, limit?: number }): Promise<Channel[]> {
    const searchParams = new URLSearchParams()
    if (params?.user_id) searchParams.set('user_id', params.user_id.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.limit) searchParams.set('limit', params.limit.toString())

    const query = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return apiRequest<Channel[]>(`/v1/channels/${query}`)
  },

  async getById(id: number): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`)
  },

  async create(data: ChannelCreateRequest): Promise<Channel> {
    return apiRequest<Channel>('/v1/channels/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async update(id: number, data: ChannelUpdateRequest): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/v1/channels/${id}`, {
      method: 'DELETE',
    })
  },

  async getStatistics(id: number): Promise<ChannelStatistics> {
    return apiRequest<ChannelStatistics>(`/v1/channels/${id}/statistics`)
  },

  async uploadImage(id: number, file: File): Promise<{ message: string, image_url: string, filename: string, file_size: number }> {
    const formData = new FormData()
    formData.append('file', file)

    return apiRequest<{ message: string, image_url: string, filename: string, file_size: number }>(
      `/v1/channels/${id}/upload-image`,
      {
        method: 'POST',
        body: formData,
      }
    )
  },

  getImageUrl(id: number): string {
    return `${API_BASE_URL}/v1/channels/${id}/image.png`
  }
}

// RSS Feed API
export const feedApi = {
  async getRssFeed(channelId: number, limit?: number): Promise<string> {
    const params = limit ? `?limit=${limit}` : ''
    return apiRequest<string>(`/v1/feeds/${channelId}/feed.xml${params}`)
  },

  async validateFeed(channelId: number): Promise<FeedValidationResponse> {
    return apiRequest<FeedValidationResponse>(`/v1/feeds/${channelId}/validate`, {
      method: 'POST',
    })
  },

  async getFeedInfo(channelId: number): Promise<FeedInfoResponse> {
    return apiRequest<FeedInfoResponse>(`/v1/feeds/${channelId}/info`)
  },

  async getAllFeeds(): Promise<FeedInfoResponse[]> {
    return apiRequest<FeedInfoResponse[]>('/v1/feeds/')
  }
}

// Search API
export const searchApi = {
  async searchEpisodes(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>('/v1/episodes/search', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async getSearchSuggestions(channelId: number, query: string, limit = 5): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(`/v1/episodes/search/suggestions?${params.toString()}`)
  },

  async getTrendingSearches(channelId: number, limit = 10): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(`/v1/episodes/search/trending?${params.toString()}`)
  },

  async getAvailableFilters(channelId: number): Promise<Record<string, Array<{ value: string | number, count: number }>>> {
    return apiRequest<Record<string, Array<{ value: string | number, count: number }>>>(`/v1/episodes/filters/${channelId}`)
  },

  async rebuildSearchIndex(channelId?: number): Promise<{ message: string }> {
    const params = channelId ? `?channel_id=${channelId}` : ''
    return apiRequest<{ message: string }>(`/v1/episodes/search/rebuild${params}`, {
      method: 'POST',
    })
  },

  async getTagSuggestions(channelId: number, query: string, limit = 10): Promise<TagSuggestionsResponse> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<TagSuggestionsResponse>(`/v1/tags/suggestions?${params.toString()}`)
  }
}

// Tag API
export const tagApi = {
  async getAll(channelId: number): Promise<{ tags: Tag[], total_count: number, channel_id: number }> {
    return apiRequest<{ tags: Tag[], total_count: number, channel_id: number }>(`/v1/tags/?channel_id=${channelId}`)
  },

  async getById(id: number): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`)
  },

  async create(channelId: number, data: CreateTagRequest): Promise<Tag> {
    return apiRequest<Tag>('/v1/tags/', {
      method: 'POST',
      body: JSON.stringify({ channel_id: channelId, ...data }),
    })
  },

  async update(id: number, data: UpdateTagRequest): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string, tag_id: number }> {
    return apiRequest<{ message: string, tag_id: number }>(`/v1/tags/${id}`, {
      method: 'DELETE',
    })
  },

  async getEpisodeTags(episodeId: number): Promise<Tag[]> {
    const response = await apiRequest<Episode>(`/v1/episodes/${episodeId}`)
    return response.tags || []
  },

  async addToEpisode(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: 'POST',
      body: JSON.stringify(tagIds),
    })
  },

  async removeFromEpisode(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: 'DELETE',
      body: JSON.stringify(tagIds),
    })
  },

  async replaceEpisodeTags(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: 'PUT',
      body: JSON.stringify(tagIds),
    })
  }
}

// Event API
export const eventApi = {
  async getAll(channelId: number, params?: Omit<EventFilterParams, 'channelId'>): Promise<PaginatedResponse<Event>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 100).toString(),
    })

    if (params?.eventType) searchParams.set('event_type', params.eventType)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.startDate) searchParams.set('start_date', params.startDate)
    if (params?.endDate) searchParams.set('end_date', params.endDate)

    const response = await apiRequest<ApiResponse<PaginatedResponse<Event>>>(
      `/v1/events?${searchParams.toString()}`
    )
    return response.data
  },

  async getById(id: number): Promise<Event> {
    const response = await apiRequest<ApiResponse<Event>>(`/v1/events/${id}`)
    return response.data
  },

  async getByEpisode(episodeId: number): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(`/v1/episodes/${episodeId}/events`)
    return response.data
  },

  async getByType(eventType: EventType): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(`/v1/events/by-type?type=${eventType}`)
    return response.data
  },

  async getByStatus(status: EventStatus): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(`/v1/events/by-status?status=${status}`)
    return response.data
  },

  async cleanup(olderThanDays: number): Promise<{ deleted: number }> {
    const response = await apiRequest<ApiResponse<{ deleted: number }>>('/v1/events/cleanup', {
      method: 'POST',
      body: JSON.stringify({ older_than_days: olderThanDays }),
    })
    return response.data
  }
}

// Export security utilities for external use
export { ApiError, sanitizeInput, validateUrl }