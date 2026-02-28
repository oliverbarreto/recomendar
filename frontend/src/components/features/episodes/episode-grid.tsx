"use client"

/**
 * Episode Grid Component - Displays episodes in a responsive grid layout
 */
"use client"

import { useMemo, useEffect, useRef } from 'react'
import { EpisodeCard } from './episode-card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Plus, Mic } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useEpisodesWithPagination } from '@/hooks/use-episodes'
import { episodeApi } from '@/lib/api'
import { useAudio } from '@/contexts/audio-context'
import { getApiBaseUrl } from '@/lib/api-url'
import { Episode } from '@/types'

interface EpisodeGridProps {
  /**
   * Channel ID to fetch episodes for
   */
  channelId: number
  /**
   * Optional search query for filtering episodes
   */
  searchQuery?: string
  /**
   * Optional tag IDs for client-side filtering (server-side filtering not yet implemented)
   */
  selectedTagIds?: number[]
  /**
   * Optional flag to show only favorited episodes
   */
  favoritesOnly?: boolean
  /**
   * Current page number for pagination (1-based)
   */
  currentPage?: number
  /**
   * Number of episodes per page
   */
  pageSize?: number
  /**
   * Additional CSS classes for styling
   */
  className?: string
  /**
   * Callback fired when episode counts change
   * @param totalCount - Total number of episodes available
   * @param filteredCount - Number of episodes after applying filters
   */
  onEpisodeCountChange?: (totalCount: number, filteredCount: number) => void
  /**
   * Callback fired when pagination changes
   * @param page - New page number
   */
  onPaginationChange?: (page: number) => void
}

export function EpisodeGrid({
  channelId,
  searchQuery = '',
  selectedTagIds = [],
  favoritesOnly = false,
  currentPage = 1,
  pageSize = 20,
  className,
  onEpisodeCountChange,
  onPaginationChange
}: EpisodeGridProps) {
  const router = useRouter()

  // Use global audio context
  const { playingEpisodeId, playEpisode, stopEpisode } = useAudio()

  // Use enhanced episodes hook with pagination
  const {
    data: episodesData,
    isLoading,
    error,
    refetch,
    totalCount,
    filteredEpisodes,
    totalPages,
    hasNextPage,
    hasPrevPage,
    isPaginationLoading
  } = useEpisodesWithPagination(
    channelId,
    currentPage,
    pageSize,
    searchQuery,
    selectedTagIds,
    favoritesOnly
  )

  // Memoize episodes array to prevent unnecessary re-renders
  const episodes = useMemo(() => episodesData?.episodes || [], [episodesData?.episodes])

  // Track previous episodes for toast notifications
  const previousEpisodesRef = useRef<Episode[]>([])

  // Watch for status changes and show toast notifications
  useEffect(() => {
    const previousEpisodes = previousEpisodesRef.current

    if (previousEpisodes.length > 0 && episodes.length > 0) {
      episodes.forEach(currentEpisode => {
        const previousEpisode = previousEpisodes.find(prev => prev.id === currentEpisode.id)

        if (previousEpisode && previousEpisode.status !== currentEpisode.status) {
          // Status changed - show appropriate notification
          if (currentEpisode.status === 'completed') {
            toast.success(`Episode "${currentEpisode.title}" completed successfully!`)
          } else if (currentEpisode.status === 'failed') {
            toast.error(`Episode "${currentEpisode.title}" failed to process`)
          }
        }
      })
    }

    // Update previous episodes reference
    previousEpisodesRef.current = episodes
  }, [episodes])

  // Additional client-side filtering for features not supported by backend API
  const additionalFilteredEpisodes = useMemo(() => {
    let filtered = filteredEpisodes

    // Apply favorites filter - show only favorited episodes (client-side since backend doesn't support this)
    if (favoritesOnly) {
      filtered = filtered.filter(episode => episode.is_favorited === true)
    }

    // Apply tag filter - episode must have ALL selected tags (client-side since backend doesn't support this)
    if (selectedTagIds.length > 0) {
      filtered = filtered.filter(episode => {
        const episodeTagIds = episode.tags.map(tag => tag.id)
        return selectedTagIds.every(tagId => episodeTagIds.includes(tagId))
      })
    }

    return filtered
  }, [filteredEpisodes, selectedTagIds, favoritesOnly])

  // Notify parent about episode count changes
  useEffect(() => {
    if (onEpisodeCountChange) {
      onEpisodeCountChange(totalCount, additionalFilteredEpisodes.length)
    }
  }, [totalCount, additionalFilteredEpisodes.length, onEpisodeCountChange])

  const handlePlayEpisode = (episode: Episode) => {
    if (episode.status === 'completed' && episode.audio_file_path) {
      // Use global audio context to play episode
      playEpisode(episode)
    } else {
      toast.error('Episode is not ready for playback yet')
    }
  }

  const handleClosePlayer = () => {
    // Use global audio context to stop episode
    stopEpisode()
  }

  const handleEditEpisode = (episode: Episode) => {
    router.push(`/episodes/${episode.id}`)
  }

  const handleDeleteEpisode = async (episode: Episode) => {
    if (!confirm(`Are you sure you want to delete "${episode.title}"?`)) {
      return
    }

    try {
      // Use the episodeApi delete method which will automatically handle React Query cache updates
      await episodeApi.delete(episode.id)
      toast.success('Episode deleted successfully')
      // Refetch episodes to update the UI
      refetch()
    } catch (error) {
      console.error('Failed to delete episode:', error)
      toast.error('Failed to delete episode')
    }
  }

  const handleRetryEpisode = async (episode: Episode) => {
    if (episode.status !== 'failed') {
      toast.error('Episode is not in a failed state')
      return
    }

    try {
      // Use the episode API to retry
      const response = await fetch(`${getApiBaseUrl()}/v1/episodes/${episode.id}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to retry episode')
      }

      toast.success('Episode retry queued successfully')
      // Refetch episodes to update the UI
      refetch()
    } catch (error) {
      console.error('Failed to retry episode:', error)
      toast.error('Failed to retry episode')
    }
  }

  if (isLoading && currentPage === 1) {
    return (
      <div className={cn(
        "grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        className
      )}>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="aspect-video bg-muted rounded-lg mb-3" />
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded" />
              <div className="h-3 bg-muted rounded w-3/4" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Show loading overlay for pagination changes (not initial load)
  if (isPaginationLoading) {
    return (
      <div className="relative">
        <div className={cn(
          "grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 opacity-50 pointer-events-none",
          className
        )}>
          {additionalFilteredEpisodes.map((episode) => (
            <EpisodeCard
              key={episode.id}
              episode={episode}
              onPlay={handlePlayEpisode}
              onStop={handleClosePlayer}
              onEdit={handleEditEpisode}
              onDelete={handleDeleteEpisode}
              onRetry={episode.status === 'failed' ? handleRetryEpisode : undefined}
              isPlaying={playingEpisodeId === episode.id}
            />
          ))}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
            <span className="text-sm text-muted-foreground">Loading page {currentPage}...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
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
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold mb-2">Failed to load episodes</h3>
        <p className="text-muted-foreground max-w-sm mb-4">
          {error instanceof Error ? error.message : 'An error occurred while loading episodes'}
        </p>
        <Button onClick={() => refetch()} variant="outline">
          Try Again
        </Button>
      </div>
    )
  }

  if (additionalFilteredEpisodes.length === 0 && (searchQuery || selectedTagIds.length > 0 || favoritesOnly)) {
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
        <h3 className="text-lg font-semibold mb-2">No episodes found</h3>
        <p className="text-muted-foreground max-w-sm">
          Try adjusting your search terms or browse all episodes.
        </p>
      </div>
    )
  }

  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-muted-foreground mb-4">
          <Mic className="w-16 h-16 mx-auto mb-4" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No episodes yet</h3>
        <p className="text-muted-foreground max-w-sm mb-6">
          Start by adding your first episode from a YouTube URL. Your episodes will appear here once they&apos;re processed.
        </p>
        <Button onClick={() => router.push('/episodes/add')} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Your First Episode
        </Button>
      </div>
    )
  }

  return (
    <>
      <div className={cn(
        "grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        className
      )}>
        {additionalFilteredEpisodes.map((episode) => (
          <EpisodeCard
            key={episode.id}
            episode={episode}
            onPlay={handlePlayEpisode}
            onStop={handleClosePlayer}
            onEdit={handleEditEpisode}
            onDelete={handleDeleteEpisode}
            onRetry={episode.status === 'failed' ? handleRetryEpisode : undefined}
            isPlaying={playingEpisodeId === episode.id}
          />
        ))}
      </div>

      {/* Global audio player will be shown automatically via GlobalMediaPlayer in layout */}
      {/* Bottom padding to account for global audio player */}
      {playingEpisodeId && (
        <div className="h-20" />
      )}

      {/* Pagination info for debugging (remove in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="text-xs text-muted-foreground text-center mt-4">
          Page {currentPage} of {totalPages} • {totalCount} total episodes • {additionalFilteredEpisodes.length} displayed
        </div>
      )}
    </>
  )
}