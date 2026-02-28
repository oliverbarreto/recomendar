"use client"

/**
 * Episode Card Component - YouTube-style episode cards with status indicators
 */

import React from 'react'
import {
  Play,
  Square,
  Download,
  MoreVertical,
  ExternalLink,
  RefreshCw,
  Trash2,
  AlertCircle,
  Clock,
  CheckCircle2,
  Loader2,
  Edit,
  Heart,
  Youtube
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { useDeleteEpisode, useRetryEpisode, useEpisodeProgress, useFavoriteEpisode, useUnfavoriteEpisode } from '@/hooks/use-episodes'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'
import { Episode } from '@/types'
import { generateGradientStyle, getOptimalTextColor, generateEpisodeGradient } from '@/lib/colors'
import { useState } from 'react'
import { FollowChannelModal } from '@/components/features/subscriptions/follow-channel-modal'

// Simple date formatting utility
const formatDistanceToNow = (date: Date, options?: { addSuffix?: boolean }) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days > 0) {
    return options?.addSuffix ? `${days} day${days > 1 ? 's' : ''} ago` : `${days} day${days > 1 ? 's' : ''}`
  } else if (hours > 0) {
    return options?.addSuffix ? `${hours} hour${hours > 1 ? 's' : ''} ago` : `${hours} hour${hours > 1 ? 's' : ''}`
  } else {
    return options?.addSuffix ? `${minutes} minute${minutes > 1 ? 's' : ''} ago` : `${minutes} minute${minutes > 1 ? 's' : ''}`
  }
}

// Format bytes to human readable format
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Check if episode is from a local upload (not YouTube)
const isUploadedEpisode = (episode: Episode) => {
  return episode.video_id?.startsWith('up_') &&
    !episode.thumbnail_url &&
    !episode.youtube_channel
}

// Check if episode has a valid thumbnail (YouTube episode)
const hasValidThumbnail = (episode: Episode) => {
  return episode.thumbnail_url && episode.thumbnail_url.trim() !== ''
}

interface EpisodeCardProps {
  episode: Episode
  onPlay?: (episode: Episode) => void
  onStop?: (episode: Episode) => void
  onEdit?: (episode: Episode) => void
  onDelete?: (episode: Episode) => void
  onRetry?: (episode: Episode) => void
  onFavorite?: (episode: Episode) => void
  onUnfavorite?: (episode: Episode) => void
  onClick?: (episode: Episode) => void
  isPlaying?: boolean
  className?: string
}

export function EpisodeCard({
  episode,
  onPlay,
  onStop,
  onEdit,
  onDelete,
  onRetry,
  onFavorite,
  onUnfavorite,
  onClick,
  isPlaying = false,
  className
}: EpisodeCardProps) {
  const [followModalOpen, setFollowModalOpen] = useState(false)
  const router = useRouter()
  const deleteMutation = useDeleteEpisode()
  const retryMutation = useRetryEpisode()
  const favoriteMutation = useFavoriteEpisode()
  const unfavoriteMutation = useUnfavoriteEpisode()

  // Get real-time progress for processing episodes
  const { data: progressData } = useEpisodeProgress(
    episode.id,
    episode.status === 'processing',
    episode.status
  )

  const getStatusIcon = () => {
    switch (episode.status) {
      case 'completed':
        return <CheckCircle2 className="w-3 h-3 text-green-600" />
      case 'processing':
        return <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-3 h-3 text-red-600" />
      case 'pending':
        return <Clock className="w-3 h-3 text-yellow-600" />
      default:
        return null
    }
  }


  const getStatusIconOnly = () => {
    return getStatusIcon()
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }

    return `${minutes}m`
  }

  const canPlay = episode.status === 'completed' && episode.audio_file_path
  const canRetry = episode.status === 'failed'

  const handleDelete = () => {
    if (onDelete) {
      onDelete(episode)
    } else {
      deleteMutation.mutate(episode.id)
    }
  }

  const handleRetry = () => {
    if (onRetry) {
      onRetry(episode)
    } else {
      retryMutation.mutate(episode.id)
    }
  }

  const handleDownload = () => {
    if (episode.audio_file_path) {
      const audioUrl = apiClient.getEpisodeAudioUrl(episode.id)
      const link = document.createElement('a')
      link.href = audioUrl
      link.download = `${episode.title}.mp3`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success('Download started')
    } else {
      toast.error('Audio file not available')
    }
  }

  const handleFavorite = () => {
    if (episode.is_favorited) {
      if (onUnfavorite) {
        onUnfavorite(episode)
      } else {
        unfavoriteMutation.mutate(episode.id)
      }
    } else {
      if (onFavorite) {
        onFavorite(episode)
      } else {
        favoriteMutation.mutate(episode.id)
      }
    }
  }

  // Parse progress percentage from progress data (kept for potential future use)
  // const getProgressPercentage = () => {
  //   if (!progressData) return 0
  //   // progressData.percentage comes as string like "45%"
  //   const percentage = progressData.percentage?.replace('%', '')
  //   return percentage ? parseInt(percentage) : 0
  // }

  return (
    <Card
      className={cn(
        "group hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer h-full flex flex-col",
        className
      )}
      onClick={() => {
        if (onClick) {
          onClick(episode)
        } else {
          router.push(`/episodes/${episode.id}`)
        }
      }}
    >
      <CardContent className="pb-4 space-y-4 flex flex-col h-full">

        {/* Episode Number and Creation Date */}
        {(episode.episode_number || episode.created_at) && (
          <div className="flex-col items-start justify-between text-md">
            <div className="flex items-center gap-2">
              {episode.episode_number && (
                <span className="font-bold text-primary">
                  Episode #{episode.episode_number}
                </span>
              )}
            </div>

            {episode.created_at && (
              <span className="text-muted-foreground text-xs">
                {new Date(episode.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - Added {formatDistanceToNow(new Date(episode.created_at), { addSuffix: true })}
              </span>
            )}

          </div>
        )}

        {/* Thumbnail and Play Button */}
        <div className="relative aspect-video rounded-lg overflow-hidden group/thumbnail">
          {hasValidThumbnail(episode) ? (
            // YouTube episode with thumbnail
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={episode.thumbnail_url || ''}
              alt={episode.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='180' viewBox='0 0 320 180'%3E%3Crect width='320' height='180' fill='%23f1f5f9'/%3E%3Cpath d='M120 60l80 30-80 30z' fill='%23cbd5e1'/%3E%3C/svg%3E"
              }}
            />
          ) : isUploadedEpisode(episode) ? (
            // Uploaded episode - show colorful gradient background
            <div
              className="w-full h-full relative transition-all duration-300 hover:scale-105"
              style={generateGradientStyle(episode.video_id || 'up_default')}
            >
              {/* Episode title overlay at bottom right */}
              {/* <div className="absolute bottom-2 right-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-md text-white text-xs font-medium max-w-[65%] truncate shadow-lg border border-white/20">
                {episode.title}
              </div> */}

              {/* 🤖 Episode title overlay at top left */}
              <div className="absolute top-2 left-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-md text-white text-xs font-medium max-w-[65%] truncate shadow-lg border border-white/20">
                {episode.title}
              </div>

              {/* Play icon in center */}
              <div className="absolute inset-0 flex items-center justify-center">
                <Play className="w-8 h-8 text-white/95 drop-shadow-lg" />
              </div>
            </div>
          ) : (
            // Fallback for episodes without thumbnails (should be rare)
            <div className="w-full h-full flex items-center justify-center bg-muted">
              <Play className="w-8 h-8 text-muted-foreground" />
            </div>
          )}

          {/* Play Button Overlay */}
          {canPlay && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover/thumbnail:opacity-100 transition-opacity">
              <Button
                size="icon"
                variant="secondary"
                className="rounded-full h-12 w-12"
                onClick={(e) => {
                  e.stopPropagation() // Prevent card click
                  if (isPlaying && onStop) {
                    onStop(episode)
                  } else if (onPlay) {
                    onPlay(episode)
                  } else {
                    // Fallback: play audio directly
                    const audioUrl = apiClient.getEpisodeAudioUrl(episode.id)
                    const audio = new Audio(audioUrl)
                    audio.play().then(() => {
                      toast.success('Playing episode')
                    }).catch((error) => {
                      console.error('Error playing audio:', error)
                      toast.error('Failed to play episode')
                    })
                  }
                }}
              >
                {isPlaying ? (
                  <Square className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5 ml-0.5" />
                )}
              </Button>
            </div>
          )}

          {/* Duration Badge */}
          {episode.duration_seconds && (
            <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded font-medium">
              {formatDuration(episode.duration_seconds)}
            </div>
          )}

          {/* 🤖 Custom Language Badge - Only show if user requested a custom language */}
          {episode.requested_language && episode.audio_language && (
            <div className="absolute bottom-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold shadow-lg border border-white/20">
              {episode.audio_language.toUpperCase()}
            </div>
          )}

        </div>

        {/* Episode Info */}
        <div className="space-y-3 flex-1 flex flex-col">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-base line-clamp-2 leading-tight">
                {episode.title}
              </h3>
              {/* YouTube Channel Name */}
              {episode.youtube_channel && (
                <button
                  className="text-sm text-muted-foreground hover:text-foreground mt-1 truncate text-left transition-colors"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (episode.youtube_channel_url) {
                      window.open(episode.youtube_channel_url, '_blank')
                    }
                  }}
                  title={`Visit ${episode.youtube_channel} on YouTube`}
                >
                  {episode.youtube_channel}
                </button>
              )}
            </div>

            <div className="flex items-start gap-1 shrink-0">
              {/* Favorite Button */}
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={(e) => {
                  e.stopPropagation()
                  handleFavorite()
                }}
              >
                <Heart
                  className={cn(
                    "w-4 h-4",
                    episode.is_favorited
                      ? "fill-red-500 text-red-500"
                      : "text-muted-foreground hover:text-red-500"
                  )}
                />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {onEdit && (
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation()
                      onEdit(episode)
                    }}>
                      <Edit className="w-4 h-4 mr-2" />
                      Edit Episode
                    </DropdownMenuItem>
                  )}

                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation()
                      if (episode.video_url) {
                        window.open(episode.video_url, '_blank')
                      }
                    }}
                    disabled={!episode.video_url}
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View on YouTube
                  </DropdownMenuItem>

                  {episode.youtube_channel_url && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          setFollowModalOpen(true)
                        }}
                      >
                        <Youtube className="w-4 h-4 mr-2" />
                        Follow Channel
                      </DropdownMenuItem>
                    </>
                  )}

                  {canPlay && (
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation()
                      handleDownload()
                    }}>
                      <Download className="w-4 h-4 mr-2" />
                      Download Audio
                    </DropdownMenuItem>
                  )}

                  {canRetry && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        handleRetry()
                      }}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry Download
                      </DropdownMenuItem>
                    </>
                  )}

                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete()
                    }}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <p className="text-sm text-muted-foreground line-clamp-3 flex-1">
            {episode.description}
          </p>

          {/* Metadata - Publication Date and Status */}
          <div className="flex items-center justify-start text-xs gap-3">
            <div className="flex items-center gap-1">
              {getStatusIconOnly()}
            </div>
            <span className="text-muted-foreground">
              <p className="text-muted-foreground">Released:
                <span className="font-medium pl-1">{formatDistanceToNow(new Date(episode.publication_date), { addSuffix: true })}</span>
              </p>
            </span>
          </div>

          {/* Tags */}
          {episode.tags && episode.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {episode.tags.slice(0, 4).map((tag) => (
                <div
                  key={tag.id}
                  className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium text-white"
                  style={{ backgroundColor: tag.color }}
                >
                  {tag.name}
                </div>
              ))}
              {episode.tags.length > 4 && (
                <div className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                  +{episode.tags.length - 4}
                </div>
              )}
            </div>
          )}

          {/* Download Status for Processing Episodes */}
          {episode.status === 'processing' && (
            <div className="space-y-2">
              {progressData ? (
                progressData.status === 'completed' ? (
                  // Show processing status when download is done but episode is still processing
                  <div className="text-xs bg-purple-50 dark:bg-purple-950/50 p-3 rounded border-l-2 border-purple-500">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin text-purple-600" />
                      <span className="font-medium text-purple-700 dark:text-purple-300">
                        Processing audio file...
                      </span>
                    </div>
                    <div className="text-muted-foreground mt-1">
                      Converting and organizing files
                    </div>
                  </div>
                ) : (
                  // Show download progress
                  <div className="text-xs bg-blue-50 dark:bg-blue-950/50 p-3 rounded border-l-2 border-blue-500">
                    <div className="flex items-center gap-2 mb-2">
                      <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                      <span className="font-medium text-blue-700 dark:text-blue-300">
                        Downloading {progressData.percentage}
                      </span>
                    </div>

                    <div className="space-y-1 text-muted-foreground">
                      {progressData.speed && (
                        <div className="flex justify-between">
                          <span>Speed:</span>
                          <span className="font-medium">{progressData.speed}</span>
                        </div>
                      )}
                      {progressData.eta && progressData.eta !== 'N/A' && (
                        <div className="flex justify-between">
                          <span>ETA:</span>
                          <span className="font-medium">{progressData.eta}</span>
                        </div>
                      )}
                      {progressData.downloaded_bytes && progressData.total_bytes && (
                        <div className="flex justify-between">
                          <span>Downloaded:</span>
                          <span className="font-medium">
                            {formatBytes(progressData.downloaded_bytes)} / {formatBytes(progressData.total_bytes)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              ) : (
                <div className="text-xs bg-orange-50 dark:bg-orange-950/50 p-3 rounded border-l-2 border-orange-500">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3 h-3 animate-spin text-orange-600" />
                    <span className="font-medium text-orange-700 dark:text-orange-300">
                      Queued for download...
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Pending Status */}
          {episode.status === 'pending' && (
            <div className="text-xs text-orange-600 bg-orange-50 dark:bg-orange-950/50 p-2 rounded border-l-2 border-orange-500">
              <div className="flex items-center gap-2">
                <Clock className="w-3 h-3" />
                Queued for download
              </div>
            </div>
          )}

          {/* Error Message for Failed Episodes */}
          {episode.status === 'failed' && (
            <div className="text-xs text-destructive bg-destructive/10 p-2 rounded">
              Download failed. Video may be private or unavailable.
            </div>
          )}
        </div>
      </CardContent>

      {/* Follow Channel Modal */}
      <FollowChannelModal
        open={followModalOpen}
        onOpenChange={setFollowModalOpen}
        defaultChannelUrl={episode.youtube_channel_url || ''}
      />
    </Card>
  )
}