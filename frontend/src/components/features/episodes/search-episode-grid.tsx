/**
 * Enhanced Episode Grid for Search Results with highlighting and relevance scores
 */

'use client'

import React from 'react'
import { SearchResult, SearchResponse } from '@/types'
import { SearchEpisodeCard } from './search-episode-card'
import { cn } from '@/lib/utils'
import { useAudio } from '@/contexts/audio-context'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ArrowUpDown, SortAsc, SortDesc } from 'lucide-react'

interface SearchEpisodeGridProps {
  searchResponse: SearchResponse
  onEditEpisode?: (episode: SearchResult) => void
  className?: string
  showRelevanceScores?: boolean
  showSearchInfo?: boolean
  sortBy?: 'relevance' | 'date' | 'title' | 'duration'
  sortOrder?: 'asc' | 'desc'
  onSortChange?: (sortBy: string, sortOrder: string) => void
}

export function SearchEpisodeGrid({
  searchResponse,
  onEditEpisode,
  className,
  showRelevanceScores = false,
  showSearchInfo = true,
  sortBy = 'relevance',
  sortOrder = 'desc',
  onSortChange,
}: SearchEpisodeGridProps) {
  const { results: episodes, total_count, search_time_ms, query } = searchResponse

  // Use global audio context
  const { playingEpisodeId, playEpisode } = useAudio()

  const handlePlayEpisode = (episode: SearchResult) => {
    // Convert SearchResult to Episode format for global audio context
    const episodeForAudio = {
      id: episode.id,
      channel_id: episode.channel_id,
      video_id: episode.video_url.split('/').pop() || episode.video_id || '',
      title: episode.title,
      description: episode.description,
      publication_date: episode.publication_date,
      audio_file_path: episode.audio_file_path,
      video_url: episode.video_url,
      thumbnail_url: episode.thumbnail_url,
      duration_seconds: episode.duration_seconds,
      keywords: episode.keywords || [],
      status: episode.status,
      retry_count: episode.retry_count || 0,
      download_date: episode.download_date,
      created_at: episode.created_at || '',
      updated_at: episode.updated_at || '',
      tags: episode.tags || [],
      // Additional fields that might be in Episode but not SearchResult
      media_file_size: episode.media_file_size,
      youtube_channel: episode.youtube_channel,
      youtube_channel_id: episode.youtube_channel_id,
      youtube_channel_url: episode.youtube_channel_url,
      is_favorited: episode.is_favorited || false
    }

    // Use global audio context to play episode
    playEpisode(episodeForAudio)
  }

  const handleSortToggle = (newSortBy: string) => {
    if (sortBy === newSortBy) {
      // Toggle order if same field
      const newOrder = sortOrder === 'asc' ? 'desc' : 'asc'
      onSortChange?.(sortBy, newOrder)
    } else {
      // New field, use default order
      const defaultOrder = newSortBy === 'relevance' ? 'desc' : 'asc'
      onSortChange?.(newSortBy, defaultOrder)
    }
  }

  const getSortIcon = (field: string) => {
    if (sortBy !== field) return <ArrowUpDown className="h-3 w-3" />
    return sortOrder === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />
  }

  if (episodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-muted-foreground mb-4">
          <svg
            className="w-16 h-16 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold mb-2">
          {query ? `No results for "${query}"` : 'No episodes found'}
        </h3>
        <p className="text-muted-foreground max-w-sm">
          {query 
            ? 'Try adjusting your search terms or filters to find what you\'re looking for.'
            : 'Start by searching for episodes or adjusting your filters.'
          }
        </p>
      </div>
    )
  }

  return (
    <>
      {/* Search Results Header */}
      {showSearchInfo && (
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold">
                {query ? `Search results for "${query}"` : 'Search results'}
              </h2>
              <Badge variant="secondary" className="text-xs">
                {total_count.toLocaleString()} episode{total_count !== 1 ? 's' : ''}
              </Badge>
            </div>
            
            {search_time_ms !== undefined && (
              <p className="text-sm text-muted-foreground">
                Found in {search_time_ms}ms
              </p>
            )}
          </div>

          {/* Sort Controls */}
          {onSortChange && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Sort by:</span>
              <div className="flex gap-1">
                <Button
                  variant={sortBy === 'relevance' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => handleSortToggle('relevance')}
                  className="h-7 px-2 gap-1"
                >
                  Relevance {getSortIcon('relevance')}
                </Button>
                <Button
                  variant={sortBy === 'date' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => handleSortToggle('date')}
                  className="h-7 px-2 gap-1"
                >
                  Date {getSortIcon('date')}
                </Button>
                <Button
                  variant={sortBy === 'title' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => handleSortToggle('title')}
                  className="h-7 px-2 gap-1"
                >
                  Title {getSortIcon('title')}
                </Button>
                <Button
                  variant={sortBy === 'duration' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => handleSortToggle('duration')}
                  className="h-7 px-2 gap-1"
                >
                  Duration {getSortIcon('duration')}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Episode Grid */}
      <div className={cn(
        'grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5',
        className
      )}>
        {episodes.map((episode, index) => (
          <SearchEpisodeCard
            key={episode.id}
            episode={episode}
            query={query}
            onPlay={handlePlayEpisode}
            onEdit={onEditEpisode}
            isPlaying={playingEpisodeId === episode.id}
            showRelevanceScore={showRelevanceScores}
            searchRank={index + 1}
          />
        ))}
      </div>

      {/* Global audio player will be shown automatically via GlobalMediaPlayer in layout */}

      {/* Bottom padding to account for audio player */}
      {currentEpisode && (
        <div className="h-20" />
      )}
    </>
  )
}