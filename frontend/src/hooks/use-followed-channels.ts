/**
 * React Query hooks for followed channel management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import {
    FollowedChannel,
    FollowedChannelCreateRequest,
    FollowedChannelUpdateRequest,
    BackfillRequest,
    BackfillResponse
} from '@/types'

// Query keys factory
export const followedChannelKeys = {
    all: ['followed-channels'] as const,
    lists: () => [...followedChannelKeys.all, 'list'] as const,
    list: () => [...followedChannelKeys.lists()] as const,
    details: () => [...followedChannelKeys.all, 'detail'] as const,
    detail: (id: number) => [...followedChannelKeys.details(), id] as const,
}

// List followed channels hook
export function useFollowedChannels() {
    return useQuery({
        queryKey: followedChannelKeys.list(),
        queryFn: async () => {
            const response = await apiClient.getFollowedChannels()
            return response
        },
        staleTime: 30000, // 30 seconds
    })
}

// Get followed channel hook
export function useFollowedChannel(id: number) {
    return useQuery({
        queryKey: followedChannelKeys.detail(id),
        queryFn: async () => {
            const response = await apiClient.getFollowedChannel(id)
            return response
        },
        enabled: !!id,
        staleTime: 30000,
    })
}

// Follow channel mutation
export function useFollowChannel() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (data: FollowedChannelCreateRequest) => {
            const response = await apiClient.followChannel(data)
            return response
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })
            toast.success('Channel followed successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to follow channel: ${error.message}`)
        },
    })
}

// Unfollow channel mutation
export function useUnfollowChannel() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            await apiClient.unfollowChannel(id)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })
            toast.success('Channel unfollowed successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to unfollow channel: ${error.message}`)
        },
    })
}

// Update followed channel mutation
export function useUpdateFollowedChannel() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: FollowedChannelUpdateRequest }) => {
            const response = await apiClient.updateFollowedChannel(id, data)
            return response
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.detail(variables.id) })
            toast.success('Channel settings updated successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to update channel: ${error.message}`)
        },
    })
}

// Trigger check mutation (yt-dlp full method)
export function useTriggerCheck() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            const response = await apiClient.triggerCheck(id)
            return { channelId: id, taskId: response.task_id }
        },
        onSuccess: (data) => {
            // Invalidate to refresh channel list
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })

            // Start polling for this specific channel's task status
            queryClient.invalidateQueries({
                queryKey: ['task-status', 'channel', data.channelId]
            })

            // Also invalidate notifications to show the new "search started" notification
            queryClient.invalidateQueries({ queryKey: ['notifications'] })

            toast.success('Check task queued successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to trigger check: ${error.message}`)
        },
    })
}

// Trigger check RSS mutation (RSS feed method)
export function useTriggerCheckRss() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            const response = await apiClient.triggerCheckRss(id)
            return { channelId: id, taskId: response.task_id }
        },
        onSuccess: (data) => {
            // Invalidate to refresh channel list
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })

            // Start polling for this specific channel's task status
            queryClient.invalidateQueries({
                queryKey: ['task-status', 'channel', data.channelId]
            })

            // Also invalidate notifications
            queryClient.invalidateQueries({ queryKey: ['notifications'] })

            toast.success('RSS check task queued successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to trigger RSS check: ${error.message}`)
        },
    })
}

// Backfill channel mutation
export function useBackfillChannel() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: BackfillRequest }) => {
            const response = await apiClient.backfillChannel(id, data)
            return response
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })
            toast.success('Backfill task queued successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to trigger backfill: ${error.message}`)
        },
    })
}

// Update channel metadata mutation
export function useUpdateChannelMetadata() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (id: number) => {
            return await apiClient.updateChannelMetadata(id)
        },
        onSuccess: (_, channelId) => {
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })
            queryClient.invalidateQueries({ queryKey: followedChannelKeys.detail(channelId) })
            toast.success('Channel information updated successfully')
        },
        onError: (error: Error) => {
            toast.error(`Failed to update channel info: ${error.message}`)
        },
    })
}

