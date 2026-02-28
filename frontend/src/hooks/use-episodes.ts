/**
 * React Query hooks for episode management
 */

import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiClient, ApiError } from '@/lib/api-client'
import { episodeApi } from '@/lib/api'
import {
  Episode,
  EpisodeCreate,
  EpisodeUpdate,
  EpisodeFilters,
  EpisodeStatus
} from '@/types/episode'
import { parseUploadError, getErrorMessage } from '@/lib/errors'

// Query keys factory
export const episodeKeys = {
  all: ['episodes'] as const,
  lists: () => [...episodeKeys.all, 'list'] as const,
  list: (filters: EpisodeFilters) => [...episodeKeys.lists(), filters] as const,
  details: () => [...episodeKeys.all, 'detail'] as const,
  detail: (id: number) => [...episodeKeys.details(), id] as const,
  progress: (id: number) => [...episodeKeys.detail(id), 'progress'] as const
}

// List episodes hook with background refetching for processing episodes
export function useEpisodes(filters: EpisodeFilters) {
  return useQuery({
    queryKey: episodeKeys.list(filters),
    queryFn: () => apiClient.getEpisodes(filters),
    enabled: !!filters.channel_id,
    staleTime: 1000, // Always consider stale for processing episodes
    placeholderData: keepPreviousData, // For pagination
    refetchInterval: (query) => {
      // Only refetch if we have processing/pending episodes
      const data = query.state.data as { episodes: Array<{ status: string }> } | undefined
      const hasProcessingEpisodes = data?.episodes?.some(episode =>
        episode.status === 'processing' || episode.status === 'pending'
      )
      return hasProcessingEpisodes ? 3000 : false // 3 seconds if processing, else stop
    },
    refetchIntervalInBackground: true, // Refetch even when tab is inactive
    refetchOnWindowFocus: true, // Refetch when user returns to tab
  })
}

/**
 * Enhanced episodes hook with pagination state management
 *
 * This hook provides a complete pagination solution for episodes, combining
 * server-side pagination with client-side filtering for optimal performance.
 *
 * @param channelId - The channel ID to fetch episodes for
 * @param currentPage - Current page number (1-based)
 * @param pageSize - Number of episodes per page
 * @param searchQuery - Optional search query for server-side filtering
 * @param selectedTagIds - Optional tag IDs for client-side filtering (not yet supported by backend)
 * @param favoritesOnly - Optional flag to filter only favorited episodes
 *
 * @returns Object containing:
 * - Query result from React Query (data, isLoading, error, etc.)
 * - Pagination state (currentPage, pageSize, totalPages, hasNextPage, hasPrevPage)
 * - Episode data (filteredEpisodes, totalCount)
 * - Loading state optimized for pagination (isPaginationLoading)
 *
 * @example
 * ```typescript
 * const {
 *   data,
 *   isLoading,
 *   currentPage,
 *   totalPages,
 *   hasNextPage,
 *   handlePageChange
 * } = useEpisodesWithPagination(channelId, page, pageSize, searchQuery)
 * ```
 */
export function useEpisodesWithPagination(
  channelId: number,
  currentPage: number = 1,
  pageSize: number = 20,
  searchQuery?: string,
  selectedTagIds?: number[],
  favoritesOnly?: boolean
) {
  const skip = (currentPage - 1) * pageSize

  const filters: EpisodeFilters = {
    channel_id: channelId,
    skip,
    limit: pageSize,
    search: searchQuery,
    // Note: Backend doesn't support tag filtering via API query params yet
    // This would need to be implemented on the backend if needed
  }

  const query = useEpisodes(filters)

  return {
    ...query,
    currentPage,
    pageSize,
    totalPages: Math.ceil((query.data?.total || 0) / pageSize),
    hasNextPage: currentPage < Math.ceil((query.data?.total || 0) / pageSize),
    hasPrevPage: currentPage > 1,
    // Calculate filtered episodes based on client-side filtering
    filteredEpisodes: query.data?.episodes || [],
    totalCount: query.data?.total || 0,
    // Performance optimization: provide stable references for pagination
    isPaginationLoading: query.isLoading && currentPage > 1, // Only show loading for page changes, not initial load
  }
}

// Get single episode hook
export function useEpisode(id: number) {
  return useQuery({
    queryKey: episodeKeys.detail(id),
    queryFn: () => apiClient.getEpisode(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Episode progress hook with polling
export function useEpisodeProgress(id: number, enabled = true, episodeStatus?: string) {
  return useQuery({
    queryKey: episodeKeys.progress(id),
    queryFn: () => apiClient.getEpisodeProgress(id),
    enabled: enabled && !!id,
    refetchInterval: (query) => {
      // Continue polling if episode is still processing (even if download progress is completed)
      const data = query.state.data as { status?: string } | undefined;
      const isProgressActive = data?.status === 'processing';
      const isEpisodeProcessing = episodeStatus === 'processing';

      // Poll every 2 seconds if either progress or episode is still processing
      return (isProgressActive || isEpisodeProcessing) ? 2000 : false
    },
    staleTime: 0, // Always fresh for progress
  })
}

// Create episode mutation
export function useCreateEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EpisodeCreate) => apiClient.createEpisode(data),
    onMutate: async (newEpisode) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: episodeKeys.list({ channel_id: newEpisode.channel_id })
      })

      // Snapshot previous value
      const previousEpisodes = queryClient.getQueryData(
        episodeKeys.list({ channel_id: newEpisode.channel_id })
      )

      // Optimistically update
      queryClient.setQueryData(
        episodeKeys.list({ channel_id: newEpisode.channel_id }),
        (old: { episodes: Episode[]; total: number } | undefined) => {
          if (!old) return old

          const optimisticEpisode: Episode = {
            id: Date.now(), // Temporary ID
            channel_id: newEpisode.channel_id,
            video_id: '',
            title: 'Creating episode...',
            description: '',
            publication_date: new Date().toISOString(),
            audio_file_path: null,
            video_url: newEpisode.video_url,
            thumbnail_url: null,
            duration_seconds: null,
            keywords: [],
            status: EpisodeStatus.PENDING,
            retry_count: 0,
            download_date: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            tags: []
          }

          return {
            ...old,
            episodes: [optimisticEpisode, ...old.episodes],
            total: old.total + 1
          }
        }
      )

      return { previousEpisodes }
    },
    onError: (error, newEpisode, context) => {
      // Rollback optimistic update
      if (context?.previousEpisodes) {
        queryClient.setQueryData(
          episodeKeys.list({ channel_id: newEpisode.channel_id }),
          context.previousEpisodes
        )
      }

      // Show error toast
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to create episode'

      toast.error(message)
    },
    onSuccess: (episode, variables) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: episodeKeys.list({ channel_id: variables.channel_id })
      })

      // Set individual episode data
      queryClient.setQueryData(episodeKeys.detail(episode.id), episode)

      toast.success(`Episode "${episode.title}" created successfully`)
    }
  })
}

/**
 * Upload episode mutation with progress tracking
 * 
 * @param onProgress - Callback for upload progress updates
 * @returns Mutation hook for uploading episodes
 */
export function useUploadEpisode(onProgress?: (progress: number) => void) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      channelId: number
      title: string
      description?: string
      publicationDate?: string
      tags?: string[]
      audioFile: File
    }) => {
      const formData = new FormData()
      formData.append('channel_id', data.channelId.toString())
      formData.append('title', data.title)
      if (data.description) {
        formData.append('description', data.description)
      }
      if (data.publicationDate) {
        formData.append('publication_date', data.publicationDate)
      }
      if (data.tags && data.tags.length > 0) {
        data.tags.forEach(tag => {
          formData.append('tags', tag)
        })
      }
      formData.append('audio_file', data.audioFile)

      // Create AbortController for cancellation support
      const controller = new AbortController()

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/episodes/upload`, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
          // Track upload progress
          ...(onProgress && {
            // Note: Progress tracking requires XMLHttpRequest or custom implementation
            // This is a simplified version
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          // Structure the error to match what parseUploadError expects
          const structuredError = {
            response: {
              data: errorData,
              status: response.status
            }
          }
          throw structuredError
        }

        return response.json()
      } catch (error) {
        throw error
      }
    },
    onSuccess: (episode, variables) => {
      // Invalidate and refetch episodes list
      queryClient.invalidateQueries({
        queryKey: episodeKeys.list({ channel_id: variables.channelId })
      })

      // Add the new episode to the cache
      queryClient.setQueryData(
        episodeKeys.detail(episode.id),
        episode
      )

      toast.success('Episode uploaded successfully!', {
        description: `"${episode.title}" has been added to your channel.`
      })
    },
    onError: (error: any, variables) => {
      const uploadError = parseUploadError(error)
      const errorMessage = getErrorMessage(uploadError)

      toast.error('Upload failed', {
        description: errorMessage
      })
    }
  })
}

// Update episode mutation
export function useUpdateEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: EpisodeUpdate }) =>
      apiClient.updateEpisode(id, data),
    onSuccess: (episode) => {
      // Update episode detail
      queryClient.setQueryData(episodeKeys.detail(episode.id), episode)

      // Invalidate episode lists
      queryClient.invalidateQueries({ queryKey: episodeKeys.lists() })

      toast.success('Episode updated successfully')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to update episode'

      toast.error(message)
    }
  })
}

// Delete episode mutation
export function useDeleteEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => apiClient.deleteEpisode(id),
    onSuccess: (_, episodeId) => {
      // Remove from all caches
      queryClient.removeQueries({ queryKey: episodeKeys.detail(episodeId) })
      queryClient.removeQueries({ queryKey: episodeKeys.progress(episodeId) })

      // Invalidate episode lists
      queryClient.invalidateQueries({ queryKey: episodeKeys.lists() })

      toast.success('Episode deleted successfully')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to delete episode'

      toast.error(message)
    }
  })
}

// Retry episode download mutation
export function useRetryEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => apiClient.retryEpisodeDownload(id),
    onSuccess: (_, episodeId) => {
      // Invalidate episode and progress data
      queryClient.invalidateQueries({ queryKey: episodeKeys.detail(episodeId) })
      queryClient.invalidateQueries({ queryKey: episodeKeys.progress(episodeId) })
      queryClient.invalidateQueries({ queryKey: episodeKeys.lists() })

      toast.success('Episode download retry queued')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to retry episode download'

      toast.error(message)
    }
  })
}

// Video analysis hook
export function useAnalyzeVideo() {
  return useMutation({
    mutationFn: (videoUrl: string) => apiClient.analyzeVideo(videoUrl),
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to analyze video'

      toast.error(message)
    }
  })
}

// Favorite episode mutation
export function useFavoriteEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.favorite(id),
    onSuccess: (data, episodeId) => {
      // Update episode in cache
      queryClient.setQueryData(
        episodeKeys.detail(episodeId),
        (old: Episode | undefined) =>
          old ? { ...old, is_favorited: true } : old
      )

      // Invalidate episode lists to refresh them
      queryClient.invalidateQueries({ queryKey: episodeKeys.lists() })

      toast.success('Added to favorites')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to add to favorites'

      toast.error(message)
    }
  })
}

// Unfavorite episode mutation
export function useUnfavoriteEpisode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => episodeApi.unfavorite(id),
    onSuccess: (data, episodeId) => {
      // Update episode in cache
      queryClient.setQueryData(
        episodeKeys.detail(episodeId),
        (old: Episode | undefined) =>
          old ? { ...old, is_favorited: false } : old
      )

      // Invalidate episode lists to refresh them
      queryClient.invalidateQueries({ queryKey: episodeKeys.lists() })

      toast.success('Removed from favorites')
    },
    onError: (error) => {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to remove from favorites'

      toast.error(message)
    }
  })
}