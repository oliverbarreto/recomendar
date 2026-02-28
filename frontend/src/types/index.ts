/**
 * LabCastARR Frontend Type Definitions
 */

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// User types
export interface User {
  id: number
  name: string
  email: string
  isAdmin: boolean
  createdAt: string
  updatedAt: string
}

// Channel types
export interface Channel {
  id: number
  user_id: number
  name: string
  description: string
  website_url: string // Now required
  image_url?: string
  category: string
  language: string
  explicit_content: boolean
  author_name: string
  author_email: string
  owner_name: string
  owner_email: string
  feed_url: string
  created_at: string
  updated_at: string
}

export interface ChannelCreateRequest {
  user_id: number
  name: string
  description: string
  website_url: string // Now required
  author_name?: string
  author_email?: string
}

export interface ChannelUpdateRequest {
  name?: string
  description?: string
  website_url?: string
  image_url?: string
  category?: string
  language?: string
  explicit_content?: boolean
  author_name?: string
  author_email?: string
  owner_name?: string
  owner_email?: string
}

export interface ChannelStatistics {
  channel_id: number
  channel_name: string
  total_episodes: number
  published_episodes: number
  draft_episodes: number
  processing_episodes: number
  total_duration_seconds: number
  total_size_bytes: number
  unique_youtube_channels: number
  feed_validation_score?: number
  feed_last_updated?: string
  latest_episode?: {
    title: string
    publication_date: string
    duration?: number
  }
  created_at: string
  updated_at: string
}

// RSS Feed types
export interface FeedValidationResponse {
  channel_id: number
  is_valid: boolean
  score: number
  errors: string[]
  warnings: string[]
  recommendations: string[]
  validation_details: {
    total_episodes: number
    channel_complete: boolean
    itunes_complete: boolean
    episodes_valid: boolean
  }
  validated_at: string
}

export interface FeedInfoResponse {
  channel_id: number
  channel_name: string
  feed_url: string
  episode_count: number
  last_updated?: string
  validation_score?: number
  latest_episode_title?: string
  latest_episode_date?: string
}

// Episode types
export enum EpisodeStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface Episode {
  id: number
  channel_id: number
  video_id: string | null // Optional for uploaded episodes
  title: string
  description: string
  publication_date: string
  audio_file_path: string | null
  video_url: string
  thumbnail_url: string | null
  duration_seconds: number | null
  keywords: string[]
  status: EpisodeStatus
  retry_count: number
  download_date: string | null
  created_at: string
  updated_at: string
  tags: Array<{
    id: number
    name: string
    color: string
    usage_count: number
    is_system_tag: boolean
    created_at: string
    updated_at: string
  }>

  // YouTube channel information
  youtube_channel: string | null
  youtube_channel_id: string | null
  youtube_channel_url: string | null

  // User preferences
  is_favorited: boolean

  // New fields from enhancement
  media_file_size?: number

  // Episode numbering
  episode_number?: number

  // Audio language and quality (custom language feature)
  audio_language?: string | null  // Actual downloaded language
  audio_quality?: string | null   // Actual downloaded quality
  requested_language?: string | null  // What user requested
  requested_quality?: string | null   // What user requested
}

// Tag types
export interface Tag {
  id: number
  channel_id: number
  name: string
  color: string
  usage_count?: number
  is_system_tag?: boolean
  created_at: string
  updated_at: string
}

// Event types
export enum EventType {
  EPISODE_CREATED = "episode_created",
  EPISODE_UPDATED = "episode_updated",
  EPISODE_DELETED = "episode_deleted",
  DOWNLOAD_STARTED = "download_started",
  DOWNLOAD_COMPLETED = "download_completed",
  DOWNLOAD_FAILED = "download_failed",
  RSS_GENERATED = "rss_generated",
  CHANNEL_UPDATED = "channel_updated",
}

export enum EventStatus {
  REQUESTED = "requested",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface Event {
  id: number
  channelId: number
  episodeId?: number
  eventType: EventType
  message: string
  eventData: Record<string, unknown>
  status: EventStatus
  createdAt: string
}

// Authentication types
export interface LoginRequest {
  email: string
  password: string
  remember_me?: boolean // Optional: Extend session duration to 90 days when true
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface AuthResponse {
  user: User
  token?: string
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

// Form types
export interface CreateEpisodeRequest {
  channel_id: number
  video_url: string
  tags?: string[]
  audio_language?: string | null
  audio_quality?: string | null
}

export interface UpdateEpisodeRequest {
  title?: string
  description?: string
  keywords?: string[]
  tags?: number[]
}

export interface ChannelSettingsRequest {
  name?: string
  description?: string
  websiteUrl?: string
  category?: string
  language?: string
  explicitContent?: boolean
  authorName?: string
  authorEmail?: string
  ownerName?: string
  ownerEmail?: string
}

export interface CreateTagRequest {
  name: string
  color: string
}

export interface UpdateTagRequest {
  name?: string
  color?: string
}

export interface UserProfileRequest {
  name?: string
  email?: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

// Search and filter types
export interface EpisodeSearchParams {
  query?: string
  status?: EpisodeStatus
  tags?: number[]
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

export interface SearchFilters {
  channel_id?: number
  tags?: number[]
  status?: EpisodeStatus
  start_date?: string
  end_date?: string
  min_duration?: number
  max_duration?: number
  keywords?: string[]
}

export interface SearchRequest {
  query: string
  channel_id: number
  filters?: SearchFilters
  sort_by?: "relevance" | "date" | "title" | "duration"
  sort_order?: "asc" | "desc"
  limit?: number
  offset?: number
}

export interface SearchResult {
  id: number
  channel_id: number
  title: string
  description: string
  video_url: string
  thumbnail_url: string
  duration_seconds?: number
  publication_date: string
  status: EpisodeStatus
  tags?: Tag[]
  relevance_score?: number
  matched_fields?: string[]
  highlights?: Record<string, string>
  // Additional fields to match Episode interface for audio context
  video_id?: string
  audio_file_path: string | null
  keywords?: string[]
  retry_count?: number
  download_date?: string
  created_at?: string
  updated_at?: string
  media_file_size?: number
  youtube_channel?: string
  youtube_channel_id?: string
  youtube_channel_url?: string
  is_favorited?: boolean
  // Episode numbering
  episode_number?: number
}

export interface SearchResponse {
  results: SearchResult[]
  total_count: number
  search_time_ms: number
  query: string
  filters_applied: SearchFilters
  suggestions?: string[]
  facets?: Record<string, Array<{ value: string | number; count: number }>>
}

export interface SearchSuggestion {
  query: string
  type: "recent" | "popular" | "completion"
  count?: number
}

export interface TagSuggestion {
  id: number
  name: string
  color: string
  usage_count: number
  match_score: number
}

export interface TagSuggestionsResponse {
  suggestions: TagSuggestion[]
  query: string
  total_count: number
}

export interface EventFilterParams {
  eventType?: EventType
  status?: EventStatus
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

// Error types
export interface ApiError {
  status: number
  message: string
  details?: string
  timestamp: string
}

// UI State types
export interface LoadingState {
  [key: string]: boolean
}

export interface Toast {
  id: string
  type: "success" | "error" | "warning" | "info"
  message: string
  duration?: number
}

// Health check types
export interface HealthResponse {
  status: string
  service?: string
  version?: string
  timestamp: string
  database?: string
  error?: string
}

export interface DetailedHealthResponse extends HealthResponse {
  components: {
    database?: {
      status: string
      type?: string
      error?: string
    }
    filesystem?: {
      status: string
      media_path: string
      feeds_path: string
      media_accessible: boolean
      feeds_accessible: boolean
      error?: string
    }
  }
}

// Follow Channel Feature Types
export enum SubscriptionCheckFrequency {
  DAILY = "daily",
  WEEKLY = "weekly",
}

export enum YouTubeVideoState {
  PENDING_REVIEW = "pending_review",
  REVIEWED = "reviewed",
  QUEUED = "queued",
  DOWNLOADING = "downloading",
  EPISODE_CREATED = "episode_created",
  DISCARDED = "discarded",
}

export interface FollowedChannel {
  id: number
  user_id: number
  youtube_channel_id: string
  youtube_channel_name: string
  youtube_channel_url: string
  thumbnail_url?: string
  youtube_channel_description?: string
  auto_approve: boolean
  auto_approve_channel_id?: number
  last_checked?: string
  created_at: string
  updated_at: string
}

export interface FollowedChannelCreateRequest {
  channel_url: string
  auto_approve?: boolean
  auto_approve_channel_id?: number
}

export interface FollowedChannelUpdateRequest {
  auto_approve?: boolean
  auto_approve_channel_id?: number
}

export interface FollowedChannelWithStats extends FollowedChannel {
  pending_videos_count?: number
  reviewed_videos_count?: number
  episode_created_count?: number
  total_videos_count?: number
}

export interface BackfillRequest {
  year?: number
  max_videos?: number
}

export interface BackfillResponse {
  status: string
  task_id: string
  followed_channel_id: number
  year?: number
  max_videos: number
  message: string
}

export interface YouTubeVideo {
  id: number
  video_id: string
  followed_channel_id: number
  title: string
  description?: string
  url: string
  thumbnail_url?: string
  publish_date?: string
  duration?: number
  view_count?: number
  like_count?: number
  comment_count?: number
  state: YouTubeVideoState
  episode_id?: number
  reviewed_at?: string
  created_at: string
  updated_at: string
}

export interface YouTubeVideoListFilters {
  state?: YouTubeVideoState
  followed_channel_id?: number
  search?: string
  publish_year?: number
  skip?: number
  limit?: number
}

export interface CreateEpisodeFromVideoRequest {
  channel_id: number
  audio_language?: string | null
  audio_quality?: string | null
}

export type BulkActionType = "review" | "discard" | "create_episode"

export interface BulkActionRequest {
  video_ids: number[]
  action: BulkActionType
  channel_id?: number
  audio_language?: string | null
  audio_quality?: string | null
}

export interface BulkActionResult {
  video_id: number
  success: boolean
  error?: string
  task_id?: string
}

export interface BulkActionResponse {
  action: string
  total: number
  successful: number
  failed: number
  results: BulkActionResult[]
}

export type TaskStatus =
  | "PENDING"
  | "STARTED"
  | "PROGRESS"
  | "SUCCESS"
  | "FAILURE"
  | "RETRY"

export interface CeleryTaskStatus {
  id: number
  task_id: string
  task_name: string
  status: TaskStatus
  progress: number
  current_step?: string
  result_json?: string
  error_message?: string
  followed_channel_id?: number
  youtube_video_id?: number
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

export interface CreateEpisodeFromVideoResponse {
  status: string
  task_id: string
  youtube_video_id: number
  channel_id: number
  episode_id?: number
  message: string
}

export interface YouTubeVideoStats {
  pending_review: number
  reviewed: number
  queued: number
  downloading: number
  episode_created: number
  discarded: number
  total: number
}

export interface UserSettings {
  id: number
  user_id: number
  subscription_check_frequency: SubscriptionCheckFrequency
  preferred_check_hour: number
  preferred_check_minute: number
  timezone: string
  created_at: string
  updated_at: string
}

export interface UserSettingsUpdateRequest {
  subscription_check_frequency?: SubscriptionCheckFrequency
  preferred_check_hour?: number
  preferred_check_minute?: number
  timezone?: string
}

// Notification types
export enum NotificationType {
  VIDEO_DISCOVERED = "video_discovered",
  EPISODE_CREATED = "episode_created",
  CHANNEL_SEARCH_STARTED = "channel_search_started",
  CHANNEL_SEARCH_COMPLETED = "channel_search_completed",
  CHANNEL_SEARCH_ERROR = "channel_search_error",
}

export interface Notification {
  id: number
  userId: number
  type: NotificationType
  title: string
  message: string
  dataJson?: Record<string, any>
  read: boolean
  executedBy: "user" | "system"
  createdAt: string
  updatedAt: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  skip: number
  limit: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface DeleteNotificationResponse {
  success: boolean
  notification_id: number
}

export interface DeleteAllNotificationsResponse {
  success: boolean
  deleted_count: number
}
