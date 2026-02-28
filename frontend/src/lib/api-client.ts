/**
 * API client for episode management
 */

import {
  Episode,
  EpisodeCreate,
  EpisodeUpdate,
  EpisodeListResponse,
  DownloadProgress,
  VideoMetadata,
  EpisodeFilters,
} from "@/types/episode"
import {
  FollowedChannel,
  FollowedChannelCreateRequest,
  FollowedChannelUpdateRequest,
  BackfillRequest,
  BackfillResponse,
  YouTubeVideo,
  YouTubeVideoListFilters,
  YouTubeVideoStats,
  CreateEpisodeFromVideoRequest,
  CreateEpisodeFromVideoResponse,
  BulkActionRequest,
  BulkActionResponse,
  CeleryTaskStatus,
  UserSettings,
  UserSettingsUpdateRequest,
  NotificationListResponse,
  UnreadCountResponse,
  DeleteNotificationResponse,
  DeleteAllNotificationsResponse,
} from "@/types"
import { getApiBaseUrl } from "./api-url"

class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) {
    super(message)
    this.name = "ApiError"
  }
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = `${baseUrl || getApiBaseUrl()}/v1`
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    // Get access token from localStorage
    const getAccessToken = (): string | null => {
      if (typeof window !== "undefined") {
        return localStorage.getItem("labcastarr_access_token")
      }
      return null
    }

    const accessToken = getAccessToken()
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      "X-API-Key": "dev-secret-key-change-in-production",
      ...options.headers,
    }

    // Add Authorization header if token is available
    if (
      accessToken &&
      !endpoint.includes("/auth/login") &&
      !endpoint.includes("/auth/refresh")
    ) {
      headers["Authorization"] = `Bearer ${accessToken}`
    }

    const config: RequestInit = {
      headers,
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        let errorCode: string | undefined

        try {
          const errorData = await response.json()

          // Handle different error response formats
          if (errorData.message) {
            // Custom formatted message from backend
            errorMessage = errorData.message
          } else if (errorData.error) {
            // Standard error field
            errorMessage = errorData.error
          } else if (errorData.detail) {
            // FastAPI detail field - can be string or array
            if (Array.isArray(errorData.detail)) {
              // Format validation errors array
              errorMessage = errorData.detail
                .map((err: any) => {
                  const field = err.field || err.loc?.join(".") || ""
                  const msg = err.message || err.msg || "Validation error"
                  return field ? `${field}: ${msg}` : msg
                })
                .join("; ")
            } else {
              // Detail is a string
              errorMessage = errorData.detail
            }
          }

          errorCode = errorData.code
        } catch {
          // If we can't parse the error response, use the status text
          errorMessage = response.statusText || errorMessage
        }

        throw new ApiError(errorMessage, response.status, errorCode)
      }

      // Handle 204 No Content responses
      if (response.status === 204) {
        return null as T
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      // Network or other errors
      throw new ApiError(
        error instanceof Error ? error.message : "Network error",
        0
      )
    }
  }

  // Episode API methods
  async createEpisode(data: EpisodeCreate): Promise<Episode> {
    return this.request<Episode>("/episodes/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getEpisodes(filters: EpisodeFilters): Promise<EpisodeListResponse> {
    const params = new URLSearchParams()

    params.set("channel_id", filters.channel_id.toString())

    if (filters.skip !== undefined) {
      params.set("skip", filters.skip.toString())
    }

    if (filters.limit !== undefined) {
      params.set("limit", filters.limit.toString())
    }

    if (filters.status) {
      params.set("status", filters.status)
    }

    if (filters.search) {
      params.set("search", filters.search)
    }

    return this.request<EpisodeListResponse>(`/episodes/?${params.toString()}`)
  }

  async getEpisode(id: number): Promise<Episode> {
    return this.request<Episode>(`/episodes/${id}`)
  }

  async updateEpisode(id: number, data: EpisodeUpdate): Promise<Episode> {
    return this.request<Episode>(`/episodes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async deleteEpisode(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/episodes/${id}`, {
      method: "DELETE",
    })
  }

  async getEpisodeProgress(id: number): Promise<DownloadProgress> {
    return this.request<DownloadProgress>(`/episodes/${id}/progress`)
  }

  async retryEpisodeDownload(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/episodes/${id}/retry`, {
      method: "POST",
    })
  }

  async analyzeVideo(videoUrl: string): Promise<VideoMetadata> {
    return this.request<VideoMetadata>("/episodes/analyze", {
      method: "POST",
      body: JSON.stringify({ video_url: videoUrl }),
    })
  }

  // Media API methods
  getEpisodeAudioUrl(episodeOrId: Episode | number): string {
    // If Episode object is passed
    if (typeof episodeOrId === "object") {
      // For YouTube episodes with video_id, use permanent video_id-based URL
      // This provides cache-friendly, permanent links that don't break when episodes are deleted
      if (episodeOrId.video_id) {
        const channelId = episodeOrId.channel_id || 1
        return `${this.baseUrl}/media/episodes/by-video-id/${episodeOrId.video_id}/audio?channel_id=${channelId}`
      }

      // For uploaded episodes (no video_id), use integer ID endpoint
      // This is the CORRECT approach for uploaded episodes as they don't have YouTube video IDs
      return `${this.baseUrl}/media/episodes/${episodeOrId.id}/audio`
    }

    // Fallback for legacy integer ID calls (DEPRECATED for YouTube episodes only)
    console.warn(
      "DEPRECATED: Using integer ID for audio URL. Please pass Episode object instead."
    )
    return `${this.baseUrl}/media/episodes/${episodeOrId}/audio`
  }

  getEpisodeThumbnailUrl(id: number): string {
    return `${this.baseUrl}/media/episodes/${id}/thumbnail`
  }

  async getStorageStats(): Promise<{
    total_files: number
    total_size_mb: number
    total_size_gb: number
    disk_usage_percent: number
  }> {
    return this.request<{
      total_files: number
      total_size_mb: number
      total_size_gb: number
      disk_usage_percent: number
    }>("/media/storage/stats")
  }

  // Followed Channels API methods
  async getFollowedChannels(): Promise<FollowedChannel[]> {
    return this.request<FollowedChannel[]>("/followed-channels")
  }

  async getFollowedChannel(id: number): Promise<FollowedChannel> {
    return this.request<FollowedChannel>(`/followed-channels/${id}`)
  }

  async followChannel(
    data: FollowedChannelCreateRequest
  ): Promise<FollowedChannel> {
    // Ensure auto_approve is always a boolean (true/false), never undefined
    // Remove undefined values for other fields to avoid serialization issues
    const cleanData: FollowedChannelCreateRequest = {
      channel_url: data.channel_url,
      auto_approve: data.auto_approve ?? false, // Always send true or false
      ...(data.auto_approve_channel_id !== undefined && {
        auto_approve_channel_id: data.auto_approve_channel_id,
      }),
    }

    return this.request<FollowedChannel>("/followed-channels", {
      method: "POST",
      body: JSON.stringify(cleanData),
    })
  }

  async updateFollowedChannel(
    id: number,
    data: FollowedChannelUpdateRequest
  ): Promise<FollowedChannel> {
    return this.request<FollowedChannel>(`/followed-channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async updateChannelMetadata(id: number): Promise<FollowedChannel> {
    return this.request<FollowedChannel>(`/followed-channels/${id}/metadata`, {
      method: "PUT",
    })
  }

  async unfollowChannel(id: number): Promise<void> {
    return this.request<void>(`/followed-channels/${id}`, {
      method: "DELETE",
    })
  }

  async triggerCheck(id: number): Promise<{
    task_id: string
    status: string
    message: string
    followed_channel_id: number
    method?: string
  }> {
    return this.request<{
      task_id: string
      status: string
      message: string
      followed_channel_id: number
      method?: string
    }>(`/followed-channels/${id}/check`, {
      method: "POST",
    })
  }

  async triggerCheckRss(id: number): Promise<{
    task_id: string
    status: string
    message: string
    followed_channel_id: number
    method: string
  }> {
    return this.request<{
      task_id: string
      status: string
      message: string
      followed_channel_id: number
      method: string
    }>(`/followed-channels/${id}/check-rss`, {
      method: "POST",
    })
  }

  async backfillChannel(
    id: number,
    data: BackfillRequest
  ): Promise<BackfillResponse> {
    return this.request<BackfillResponse>(`/followed-channels/${id}/backfill`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // YouTube Videos API methods
  async getYouTubeVideos(
    filters?: YouTubeVideoListFilters
  ): Promise<YouTubeVideo[]> {
    const params = new URLSearchParams()
    if (filters?.state) params.append("state", filters.state)
    if (filters?.followed_channel_id)
      params.append(
        "followed_channel_id",
        filters.followed_channel_id.toString()
      )
    if (filters?.search) params.append("search", filters.search)
    if (filters?.publish_year)
      params.append("publish_year", filters.publish_year.toString())
    if (filters?.skip !== undefined)
      params.append("skip", filters.skip.toString())
    if (filters?.limit !== undefined)
      params.append("limit", filters.limit.toString())

    const queryString = params.toString()
    const url = `/youtube-videos${queryString ? `?${queryString}` : ""}`

    return this.request<YouTubeVideo[]>(url)
  }

  async getYouTubeVideo(id: number): Promise<YouTubeVideo> {
    return this.request<YouTubeVideo>(`/youtube-videos/${id}`)
  }

  async getYouTubeVideoStats(): Promise<YouTubeVideoStats> {
    return this.request<YouTubeVideoStats>("/youtube-videos/stats")
  }

  async markVideoReviewed(id: number): Promise<YouTubeVideo> {
    return this.request<YouTubeVideo>(`/youtube-videos/${id}/review`, {
      method: "POST",
    })
  }

  async discardVideo(id: number): Promise<YouTubeVideo> {
    return this.request<YouTubeVideo>(`/youtube-videos/${id}/discard`, {
      method: "POST",
    })
  }

  async createEpisodeFromVideo(
    id: number,
    data: CreateEpisodeFromVideoRequest
  ): Promise<CreateEpisodeFromVideoResponse> {
    return this.request<CreateEpisodeFromVideoResponse>(
      `/youtube-videos/${id}/create-episode`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
  }

  async bulkActionVideos(data: BulkActionRequest): Promise<BulkActionResponse> {
    return this.request<BulkActionResponse>("/youtube-videos/bulk-action", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Celery Task Status API methods
  async getTaskStatus(taskId: string): Promise<CeleryTaskStatus> {
    return this.request<CeleryTaskStatus>(`/celery-tasks/${taskId}`)
  }

  async getChannelTaskStatus(
    channelId: number
  ): Promise<CeleryTaskStatus | null> {
    try {
      return await this.request<CeleryTaskStatus>(
        `/followed-channels/${channelId}/task-status`
      )
    } catch (error) {
      // Handle 404 gracefully - no task status exists yet
      if (error instanceof ApiError && error.status === 404) {
        return null
      }
      throw error
    }
  }

  async getTasksSummary(): Promise<{ total: number; by_status: Record<string, number> }> {
    return this.request<{ total: number; by_status: Record<string, number> }>(
      "/celery-tasks/summary"
    )
  }

  async revokeTask(taskId: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      `/celery-tasks/revoke/${taskId}`,
      {
        method: "POST",
      }
    )
  }

  async purgeTasks(
    status: string,
    olderThanMinutes?: number
  ): Promise<{ revoked: number; deleted: number }> {
    return this.request<{ revoked: number; deleted: number }>(
      "/celery-tasks/purge",
      {
        method: "POST",
        body: JSON.stringify({
          status,
          older_than_minutes: olderThanMinutes,
        }),
      }
    )
  }

  // User Settings API methods
  async getUserSettings(): Promise<UserSettings> {
    return this.request<UserSettings>("/users/settings")
  }

  async updateUserSettings(
    data: UserSettingsUpdateRequest
  ): Promise<UserSettings> {
    return this.request<UserSettings>("/users/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async getAvailableTimezones(): Promise<string[]> {
    return this.request<string[]>("/users/timezones")
  }

  // Notification methods

  /**
   * Get notifications for current user
   * @param skip - Number of notifications to skip (pagination)
   * @param limit - Maximum number of notifications to return
   * @param unreadOnly - Return only unread notifications
   */
  async getNotifications(
    skip = 0,
    limit = 20,
    unreadOnly = false
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
      unread_only: unreadOnly.toString(),
    })

    return this.request<NotificationListResponse>(
      `/notifications/?${params.toString()}`
    )
  }

  /**
   * Get unread notification count
   */
  async getUnreadNotificationCount(): Promise<UnreadCountResponse> {
    return this.request<UnreadCountResponse>("/notifications/unread-count")
  }

  /**
   * Mark a notification as read
   * @param notificationId - ID of notification to mark as read
   */
  async markNotificationAsRead(notificationId: number): Promise<void> {
    await this.request<void>(`/notifications/${notificationId}/read`, {
      method: "PUT",
    })
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsAsRead(): Promise<void> {
    await this.request<void>("/notifications/mark-all-read", {
      method: "PUT",
    })
  }

  /**
   * Delete a notification
   * @param notificationId - ID of notification to delete
   */
  async deleteNotification(
    notificationId: number
  ): Promise<DeleteNotificationResponse> {
    return this.request<DeleteNotificationResponse>(
      `/notifications/${notificationId}`,
      {
        method: "DELETE",
      }
    )
  }

  /**
   * Delete all notifications for current user
   */
  async deleteAllNotifications(): Promise<DeleteAllNotificationsResponse> {
    return this.request<DeleteAllNotificationsResponse>(
      "/notifications/delete-all",
      {
        method: "DELETE",
      }
    )
  }

  /**
   * Get video stats for a specific followed channel
   * @param followedChannelId - ID of the followed channel
   * @returns Video counts by state for the channel
   */
  async getChannelVideoStats(
    followedChannelId: number
  ): Promise<YouTubeVideoStats> {
    return this.request<YouTubeVideoStats>(
      `/youtube-videos/stats/channel/${followedChannelId}`
    )
  }
}

// Export singleton instance
export const apiClient = new ApiClient()
export { ApiError }
export type { ApiClient }
