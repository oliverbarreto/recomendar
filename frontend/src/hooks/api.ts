/**
 * React Query hooks for LabCastARR API operations
 */
import { 
  useQuery, 
  useMutation, 
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions
} from '@tanstack/react-query'

import {
  authApi, userApi, healthApi, episodeApi, 
  channelApi, tagApi, eventApi, ApiError
} from '@/lib/api'

import type {
  User, Channel, Episode, Tag, Event,
  PaginatedResponse, HealthResponse, DetailedHealthResponse,
  LoginRequest, RegisterRequest, AuthResponse,
  CreateEpisodeRequest, UpdateEpisodeRequest,
  ChannelSettingsRequest, CreateTagRequest, UpdateTagRequest,
  UserProfileRequest, PasswordChangeRequest,
  EpisodeSearchParams, EventFilterParams,
  EpisodeStatus, EventType, EventStatus
} from '@/types'

// Query Keys
export const queryKeys = {
  // Auth
  auth: ['auth'] as const,
  currentUser: () => [...queryKeys.auth, 'currentUser'] as const,
  
  // Users
  users: ['users'] as const,
  userProfile: () => [...queryKeys.users, 'profile'] as const,
  
  // Health
  health: ['health'] as const,
  healthCheck: () => [...queryKeys.health, 'check'] as const,
  healthDb: () => [...queryKeys.health, 'db'] as const,
  healthDetailed: () => [...queryKeys.health, 'detailed'] as const,
  
  // Channels
  channels: ['channels'] as const,
  channel: () => [...queryKeys.channels, 'current'] as const,
  
  // Episodes
  episodes: ['episodes'] as const,
  episodesList: (channelId: number, params?: Omit<EpisodeSearchParams, 'channelId'>) => 
    [...queryKeys.episodes, 'list', channelId, params] as const,
  episodeDetail: (id: number) => [...queryKeys.episodes, 'detail', id] as const,
  episodeStatus: (id: number) => [...queryKeys.episodes, 'status', id] as const,
  episodesByStatus: (status: EpisodeStatus) => [...queryKeys.episodes, 'byStatus', status] as const,
  
  // Tags
  tags: ['tags'] as const,
  tagsList: (channelId: number) => [...queryKeys.tags, 'list', channelId] as const,
  tagDetail: (id: number) => [...queryKeys.tags, 'detail', id] as const,
  episodeTags: (episodeId: number) => [...queryKeys.tags, 'episode', episodeId] as const,
  
  // Events
  events: ['events'] as const,
  eventsList: (channelId: number, params?: Omit<EventFilterParams, 'channelId'>) =>
    [...queryKeys.events, 'list', channelId, params] as const,
  eventDetail: (id: number) => [...queryKeys.events, 'detail', id] as const,
  eventsByEpisode: (episodeId: number) => [...queryKeys.events, 'byEpisode', episodeId] as const,
  eventsByType: (type: EventType) => [...queryKeys.events, 'byType', type] as const,
  eventsByStatus: (status: EventStatus) => [...queryKeys.events, 'byStatus', status] as const,
}

// Auth Hooks
export const useLogin = (options?: UseMutationOptions<AuthResponse, ApiError, LoginRequest>) => {
  return useMutation({
    mutationFn: authApi.login,
    ...options,
  })
}

export const useRegister = (options?: UseMutationOptions<AuthResponse, ApiError, RegisterRequest>) => {
  return useMutation({
    mutationFn: authApi.register,
    ...options,
  })
}

export const useLogout = (options?: UseMutationOptions<void, ApiError, void>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.clear()
    },
    ...options,
  })
}

export const useCurrentUser = (options?: UseQueryOptions<User, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.currentUser(),
    queryFn: authApi.getCurrentUser,
    ...options,
  })
}

// User Hooks
export const useUserProfile = (options?: UseQueryOptions<User, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.userProfile(),
    queryFn: userApi.getProfile,
    ...options,
  })
}

export const useUpdateProfile = (options?: UseMutationOptions<User, ApiError, UserProfileRequest>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userProfile() })
    },
    ...options,
  })
}

export const useChangePassword = (options?: UseMutationOptions<void, ApiError, PasswordChangeRequest>) => {
  return useMutation({
    mutationFn: userApi.changePassword,
    ...options,
  })
}

// Health Hooks
export const useHealthCheck = (options?: UseQueryOptions<HealthResponse, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.healthCheck(),
    queryFn: healthApi.check,
    ...options,
  })
}

export const useHealthDb = (options?: UseQueryOptions<HealthResponse, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.healthDb(),
    queryFn: healthApi.checkDatabase,
    ...options,
  })
}

export const useHealthDetailed = (options?: UseQueryOptions<DetailedHealthResponse, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.healthDetailed(),
    queryFn: healthApi.checkDetailed,
    ...options,
  })
}

// Channel Hooks
export const useChannel = (options?: UseQueryOptions<Channel, ApiError>) => {
  return useQuery({
    queryKey: queryKeys.channel(),
    queryFn: channelApi.get,
    ...options,
  })
}

export const useUpdateChannel = (options?: UseMutationOptions<Channel, ApiError, ChannelSettingsRequest>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: channelApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.channel() })
    },
    ...options,
  })
}

export const useRegenerateFeed = (options?: UseMutationOptions<{ feedUrl: string }, ApiError, void>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: channelApi.regenerateFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.channel() })
    },
    ...options,
  })
}

// Episode Hooks
export const useEpisodes = (
  channelId: number,
  params?: Omit<EpisodeSearchParams, 'channelId'>,
  options?: UseQueryOptions<PaginatedResponse<Episode>, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.episodesList(channelId, params),
    queryFn: () => episodeApi.getAll(channelId, params),
    ...options,
  })
}

export const useEpisode = (
  id: number,
  options?: UseQueryOptions<Episode, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.episodeDetail(id),
    queryFn: () => episodeApi.getById(id),
    ...options,
  })
}

export const useCreateEpisode = (options?: UseMutationOptions<Episode, ApiError, CreateEpisodeRequest>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: episodeApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.episodes })
    },
    ...options,
  })
}

export const useUpdateEpisode = (options?: UseMutationOptions<Episode, ApiError, { id: number; data: UpdateEpisodeRequest }>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => episodeApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.episodeDetail(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.episodes })
    },
    ...options,
  })
}

export const useDeleteEpisode = (options?: UseMutationOptions<void, ApiError, number>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: episodeApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.episodes })
    },
    ...options,
  })
}

export const useEpisodeStatus = (
  id: number,
  options?: UseQueryOptions<{ status: EpisodeStatus, progress?: number }, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.episodeStatus(id),
    queryFn: () => episodeApi.getStatus(id),
    ...options,
  })
}

export const useUpdateEpisodeStatus = (options?: UseMutationOptions<Episode, ApiError, { id: number; status: EpisodeStatus }>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }) => episodeApi.updateStatus(id, status),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.episodeDetail(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.episodeStatus(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.episodes })
    },
    ...options,
  })
}

// Tag Hooks
export const useTags = (
  channelId: number,
  options?: UseQueryOptions<Tag[], ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.tagsList(channelId),
    queryFn: () => tagApi.getAll(channelId),
    ...options,
  })
}

export const useTag = (
  id: number,
  options?: UseQueryOptions<Tag, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.tagDetail(id),
    queryFn: () => tagApi.getById(id),
    ...options,
  })
}

export const useCreateTag = (options?: UseMutationOptions<Tag, ApiError, { channelId: number; data: CreateTagRequest }>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ channelId, data }) => tagApi.create(channelId, data),
    onSuccess: (_, { channelId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tagsList(channelId) })
    },
    ...options,
  })
}

export const useUpdateTag = (options?: UseMutationOptions<Tag, ApiError, { id: number; data: UpdateTagRequest }>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => tagApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tagDetail(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.tags })
    },
    ...options,
  })
}

export const useDeleteTag = (options?: UseMutationOptions<void, ApiError, number>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: tagApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tags })
    },
    ...options,
  })
}

export const useEpisodeTags = (
  episodeId: number,
  options?: UseQueryOptions<Tag[], ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.episodeTags(episodeId),
    queryFn: () => tagApi.getEpisodeTags(episodeId),
    ...options,
  })
}

// Event Hooks
export const useEvents = (
  channelId: number,
  params?: Omit<EventFilterParams, 'channelId'>,
  options?: UseQueryOptions<PaginatedResponse<Event>, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.eventsList(channelId, params),
    queryFn: () => eventApi.getAll(channelId, params),
    ...options,
  })
}

export const useEvent = (
  id: number,
  options?: UseQueryOptions<Event, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.eventDetail(id),
    queryFn: () => eventApi.getById(id),
    ...options,
  })
}

export const useEventsByEpisode = (
  episodeId: number,
  options?: UseQueryOptions<Event[], ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.eventsByEpisode(episodeId),
    queryFn: () => eventApi.getByEpisode(episodeId),
    ...options,
  })
}

export const useCleanupEvents = (options?: UseMutationOptions<{ deleted: number }, ApiError, number>) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: eventApi.cleanup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.events })
    },
    ...options,
  })
}