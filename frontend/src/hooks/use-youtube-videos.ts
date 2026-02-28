/**
 * React Query hooks for YouTube video management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import {
    YouTubeVideo,
    YouTubeVideoListFilters,
    CreateEpisodeFromVideoRequest,
    CreateEpisodeFromVideoResponse,
    YouTubeVideoStats,
    YouTubeVideoState,
    BulkActionRequest,
    BulkActionResponse
} from '@/types'

// Query keys factory
export const youtubeVideoKeys = {
    all: ['youtube-videos'] as const,
    lists: () => [...youtubeVideoKeys.all, 'list'] as const,
    list: (filters?: YouTubeVideoListFilters) => [...youtubeVideoKeys.lists(), filters] as const,
    details: () => [...youtubeVideoKeys.all, 'detail'] as const,
    detail: (id: number) => [...youtubeVideoKeys.details(), id] as const,
    stats: () => [...youtubeVideoKeys.all, 'stats'] as const,
    channelStats: (channelId: number) => [...youtubeVideoKeys.all, 'channel-stats', channelId] as const,
}

// List YouTube videos hook
export function useYouTubeVideos(filters?: YouTubeVideoListFilters) {
    return useQuery({
        queryKey: youtubeVideoKeys.list(filters),
        queryFn: async () => {
            return await apiClient.getYouTubeVideos(filters)
        },
        staleTime: 30000, // 30 seconds
    })
}

// Get YouTube video hook
export function useYouTubeVideo(id: number) {
    return useQuery({
        queryKey: youtubeVideoKeys.detail(id),
        queryFn: async () => {
            const response = await apiClient.getYouTubeVideo(id)
            return response
        },
        enabled: !!id,
        staleTime: 30000,
    })
}

// Get video stats hook
export function useVideoStats() {
    return useQuery({
        queryKey: youtubeVideoKeys.stats(),
        queryFn: async () => {
            const response = await apiClient.getYouTubeVideoStats()
            return response
        },
        staleTime: 10000, // 10 seconds - refresh more often for notifications
        refetchInterval: 30000, // Refetch every 30 seconds
    })
}

// Mark video as reviewed mutation
export function useMarkVideoReviewed() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            const response = await apiClient.markVideoReviewed(id)
            return response
        },
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.all })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.detail(id) })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.stats() })
            toast.success('Video marked as reviewed')
        },
        onError: (error: Error) => {
            toast.error(`Failed to mark video as reviewed: ${error.message}`)
        },
    })
}

// Discard video mutation
export function useDiscardVideo() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            const response = await apiClient.discardVideo(id)
            return response
        },
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.all })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.detail(id) })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.stats() })
            toast.success('Video discarded')
        },
        onError: (error: Error) => {
            toast.error(`Failed to discard video: ${error.message}`)
        },
    })
}

// Create episode from video mutation
export function useCreateEpisodeFromVideo() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: CreateEpisodeFromVideoRequest }) => {
            const response = await apiClient.createEpisodeFromVideo(id, data)
            return response
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.all })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.detail(variables.id) })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.stats() })
            toast.success('Episode creation queued successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to create episode: ${error.message}`)
        },
    })
}

// Hook for pending videos count (for notification bell)
export function usePendingVideosCount() {
    const { data: stats } = useVideoStats()
    return stats?.pending_review ?? 0
}

// Bulk action mutation
export function useBulkAction() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (data: BulkActionRequest) => {
            const response = await apiClient.bulkActionVideos(data)
            return response
        },
        onSuccess: (response) => {
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.all })
            queryClient.invalidateQueries({ queryKey: youtubeVideoKeys.stats() })
            
            const actionName = response.action === 'review' ? 'reviewed' : 
                             response.action === 'discard' ? 'discarded' : 
                             'queued for episode creation'
            
            if (response.failed > 0) {
                toast.warning(
                    `Bulk action completed: ${response.successful} ${actionName}, ${response.failed} failed`
                )
            } else {
                toast.success(`Successfully ${actionName} ${response.successful} video(s)`)
            }
        },
        onError: (error: Error) => {
            toast.error(`Failed to perform bulk action: ${error.message}`)
        },
    })
}

/**
 * Hook for getting video stats for a specific followed channel
 * 
 * @param followedChannelId - ID of the followed channel
 * @param enabled - Whether the query should be enabled (default: true)
 * @returns Video stats for the channel
 */
export function useChannelVideoStats(followedChannelId: number | null | undefined, enabled: boolean = true) {
    return useQuery({
        queryKey: youtubeVideoKeys.channelStats(followedChannelId || 0),
        queryFn: async () => {
            if (!followedChannelId) return null
            return await apiClient.getChannelVideoStats(followedChannelId)
        },
        enabled: enabled && !!followedChannelId,
        staleTime: 30000, // 30 seconds
        refetchInterval: 60000, // Refetch every 60 seconds
    })
}

