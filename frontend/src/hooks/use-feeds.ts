/**
 * React Query hooks for RSS feed management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { feedApi } from '@/lib/api'
import { FeedValidationResponse, FeedInfoResponse } from '@/types'

export const useFeedInfo = (channelId: number) => {
  return useQuery({
    queryKey: ['feed-info', channelId],
    queryFn: () => feedApi.getFeedInfo(channelId),
    enabled: !!channelId,
    staleTime: 0, // Always fetch fresh data
    gcTime: 0, // Don't cache in React Query (previously cacheTime)
  })
}

export const useAllFeeds = () => {
  return useQuery({
    queryKey: ['feeds'],
    queryFn: () => feedApi.getAllFeeds(),
  })
}

export const useRssFeed = (channelId: number, limit?: number) => {
  return useQuery({
    queryKey: ['rss-feed', channelId, limit],
    queryFn: () => feedApi.getRssFeed(channelId, limit),
    enabled: !!channelId,
  })
}

export const useValidateFeed = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (channelId: number) => feedApi.validateFeed(channelId),
    onSuccess: (_, channelId) => {
      queryClient.invalidateQueries({ queryKey: ['feed-info', channelId] })
    },
  })
}