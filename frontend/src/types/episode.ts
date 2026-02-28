/**
 * Episode-related TypeScript interfaces
 */

export enum EpisodeStatus {
  PENDING = "pending",
  PROCESSING = "processing", 
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface Episode {
  id: number
  channel_id: number
  video_id: string
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

  // Audio language and quality
  audio_language: string | null
  audio_quality: string | null
  requested_language: string | null
  requested_quality: string | null
}

export interface EpisodeCreate {
  channel_id: number
  video_url: string
  tags?: string[]
  audio_language?: string | null
  audio_quality?: string | null
}

export interface EpisodeUpdate {
  title?: string
  description?: string
  keywords?: string[]
  tags?: number[]
}

export interface EpisodeListResponse {
  episodes: Episode[]
  total: number
  skip: number
  limit: number
}

export interface DownloadProgress {
  episode_id: number
  status: string
  percentage: string
  speed: string
  eta: string
  downloaded_bytes: number
  total_bytes: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  updated_at: string
}

export interface VideoMetadata {
  video_id: string
  title: string
  description: string
  duration_seconds: number | null
  thumbnail_url: string | null
  uploader: string | null
  view_count: number
  publication_date: string | null
  keywords: string[]
  video_url: string
  availability: string | null

  // YouTube channel information
  channel: string | null
  channel_id: string | null
  channel_url: string | null
}

export interface EpisodeFilters {
  channel_id: number
  status?: EpisodeStatus
  search?: string
  skip?: number
  limit?: number
  order_by?: string
  order_desc?: boolean
}