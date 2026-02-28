/**
 * React Query hooks for channel management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { channelApi } from '@/lib/api'
import { Channel, ChannelCreateRequest, ChannelUpdateRequest, ChannelStatistics } from '@/types'

export const useChannels = (params?: { user_id?: number, search?: string, limit?: number }) => {
  return useQuery({
    queryKey: ['channels', params],
    queryFn: () => channelApi.getAll(params),
  })
}

export const useChannel = (id: number) => {
  return useQuery({
    queryKey: ['channel', id],
    queryFn: () => channelApi.getById(id),
    enabled: !!id,
  })
}

export const useChannelStatistics = (id: number) => {
  return useQuery({
    queryKey: ['channel-statistics', id],
    queryFn: () => channelApi.getStatistics(id),
    enabled: !!id,
  })
}

export const useCreateChannel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ChannelCreateRequest) => channelApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })
}

export const useUpdateChannel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number, data: ChannelUpdateRequest }) => 
      channelApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] })
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['channel-statistics', id] })
    },
  })
}

export const useDeleteChannel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => channelApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })
}