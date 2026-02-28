/**
 * Search Episode Card with highlighting and relevance scoring
 */

'use client'

import React, { useState } from 'react'
import {
  Play,
  Pause,
  MoreVertical,
  ExternalLink,
  RefreshCw,
  Trash2,
  AlertCircle,
  Clock,
  CheckCircle2,
  Loader2,
  Star,
  Eye,
  Calendar,
  Hash
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Progress } from '@/components/ui/progress'

import { SearchResult, EpisodeStatus } from '@/types'
import { cn } from '@/lib/utils'

interface SearchEpisodeCardProps {
  episode: SearchResult
  query: string
  onPlay?: (episode: SearchResult) => void
  onEdit?: (episode: SearchResult) => void
  isPlaying?: boolean
  showRelevanceScore?: boolean
  searchRank?: number
}

// Utility function to highlight text
function highlightText(text: string, query: string, highlights?: Record<string, string>): React.ReactNode {
  if (!query || !text) return text

  // Use provided highlights if available
  const highlightedText = highlights?.[text] || text

  // If we have specific highlights, use them
  if (highlightedText !== text) {
    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />
  }

  // Otherwise, do simple text highlighting
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  const parts = text.split(regex)

  return parts.map((part, index) =>
    regex.test(part) ? (
      <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">
        {part}
      </mark>
    ) : (
      part
    )
  )
}

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

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export function SearchEpisodeCard({
  episode,
  query,
  onPlay,
  onEdit,
  isPlaying = false,
  showRelevanceScore = false,
  searchRank
}: SearchEpisodeCardProps) {
  const [imageError, setImageError] = useState(false)

  const statusColors = {
    [EpisodeStatus.COMPLETED]: 'text-green-600 dark:text-green-400',
    [EpisodeStatus.PROCESSING]: 'text-blue-600 dark:text-blue-400',
    [EpisodeStatus.PENDING]: 'text-yellow-600 dark:text-yellow-400',
    [EpisodeStatus.FAILED]: 'text-red-600 dark:text-red-400',
  }

  const statusIcons = {
    [EpisodeStatus.COMPLETED]: CheckCircle2,
    [EpisodeStatus.PROCESSING]: Loader2,
    [EpisodeStatus.PENDING]: Clock,
    [EpisodeStatus.FAILED]: AlertCircle,
  }

  const StatusIcon = statusIcons[episode.status]

  const handleImageError = () => {
    setImageError(true)
  }

  const handlePlayClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (episode.status === EpisodeStatus.COMPLETED) {
      onPlay?.(episode)
    }
  }

  return (
    <Card className="group hover:shadow-md transition-all duration-200 overflow-hidden">
      <div className="relative">
        {/* Search Rank Badge */}
        {searchRank && (
          <Badge
            variant="secondary"
            className="absolute top-2 left-2 z-10 h-6 w-6 p-0 text-xs font-bold rounded-full flex items-center justify-center"
          >
            {searchRank}
          </Badge>
        )}

        {/* Relevance Score Badge */}
        {showRelevanceScore && episode.relevance_score && (
          <Badge
            variant="outline"
            className="absolute top-2 right-2 z-10 text-xs gap-1"
          >
            <Star className="h-3 w-3 fill-current" />
            {(episode.relevance_score * 100).toFixed(0)}%
          </Badge>
        )}

        {/* Thumbnail */}
        <div className="relative aspect-video bg-muted">
          {!imageError && episode.thumbnail_url ? (
            <img
              src={episode.thumbnail_url}
              alt={episode.title}
              className="w-full h-full object-cover"
              onError={handleImageError}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Eye className="h-8 w-8 text-muted-foreground" />
            </div>
          )}

          {/* Play Button Overlay */}
          {episode.status === EpisodeStatus.COMPLETED && (
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
              <Button
                variant="secondary"
                size="icon"
                className="h-12 w-12 rounded-full shadow-lg"
                onClick={handlePlayClick}
              >
                {isPlaying ? (
                  <Pause className="h-6 w-6" />
                ) : (
                  <Play className="h-6 w-6 ml-0.5" />
                )}
              </Button>
            </div>
          )}

          {/* Duration Badge */}
          {episode.duration_seconds && (
            <Badge
              variant="secondary"
              className="absolute bottom-2 right-2 text-xs bg-black/70 text-white border-0"
            >
              {formatDuration(episode.duration_seconds)}
            </Badge>
          )}
        </div>
      </div>

      <CardContent className="p-4">
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

        {/* Title with highlighting */}
        <h3 className="font-semibold text-sm line-clamp-2 mb-2">
          {highlightText(episode.title, query, episode.highlights)}
        </h3>

        {/* Description with highlighting */}
        <p className="text-xs text-muted-foreground line-clamp-3 mb-3">
          {highlightText(episode.description, query, episode.highlights)}
        </p>

        {/* Metadata */}
        <div className="space-y-2">
          {/* Status and Date */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1">
              <StatusIcon
                className={cn(
                  'h-3 w-3',
                  statusColors[episode.status],
                  episode.status === EpisodeStatus.PROCESSING && 'animate-spin'
                )}
              />
              <span className={statusColors[episode.status]}>
                {episode.status.charAt(0).toUpperCase() + episode.status.slice(1)}
              </span>
            </div>

            <div className="flex items-center gap-1 text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <time>
                {formatDistanceToNow(new Date(episode.publication_date), { addSuffix: true })}
              </time>
            </div>
          </div>

          {/* Tags */}
          {episode.tags && episode.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {episode.tags.slice(0, 3).map(tag => (
                <Badge
                  key={tag.id}
                  variant="outline"
                  className="text-xs h-5 px-1.5"
                  style={{ borderColor: tag.color, color: tag.color }}
                >
                  {highlightText(tag.name, query)}
                </Badge>
              ))}
              {episode.tags.length > 3 && (
                <Badge variant="outline" className="text-xs h-5 px-1.5">
                  +{episode.tags.length - 3}
                </Badge>
              )}
            </div>
          )}

          {/* Matched Fields */}
          {episode.matched_fields && episode.matched_fields.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              <span>Matched in: {episode.matched_fields.join(', ')}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-1">
            {episode.status === EpisodeStatus.COMPLETED && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2"
                onClick={handlePlayClick}
              >
                {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3 ml-0.5" />}
                {isPlaying ? 'Playing' : 'Play'}
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2"
              onClick={() => window.open(episode.video_url, '_blank')}
            >
              <ExternalLink className="h-3 w-3" />
              Source
            </Button>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit?.(episode)}>
                Edit Episode
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => window.open(episode.video_url, '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Original
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Episode
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

      </CardContent>
    </Card>
  )
}