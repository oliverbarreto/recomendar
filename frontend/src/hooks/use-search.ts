/**
 * React Query hooks for episode search functionality
 */

import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { toast } from 'sonner'
import { searchApi } from '@/lib/api'
import { 
  SearchRequest, 
  SearchResponse, 
  SearchSuggestion, 
  SearchFilters,
  TagSuggestionsResponse
} from '@/types'

// Query keys factory
export const searchKeys = {
  all: ['search'] as const,
  searches: () => [...searchKeys.all, 'searches'] as const,
  search: (request: SearchRequest) => [...searchKeys.searches(), request] as const,
  suggestions: () => [...searchKeys.all, 'suggestions'] as const,
  suggestion: (channelId: number, query: string) => [...searchKeys.suggestions(), { channelId, query }] as const,
  trending: (channelId: number) => [...searchKeys.suggestions(), 'trending', channelId] as const,
  filters: (channelId: number) => [...searchKeys.all, 'filters', channelId] as const,
  tagSuggestions: (channelId: number, query: string) => [...searchKeys.all, 'tagSuggestions', { channelId, query }] as const
}

// Search episodes hook
export function useSearchEpisodes(request: SearchRequest, enabled = true) {
  return useQuery({
    queryKey: searchKeys.search(request),
    queryFn: () => searchApi.searchEpisodes(request),
    enabled: enabled && !!request.query && !!request.channel_id,
    staleTime: 30 * 1000, // 30 seconds
    placeholderData: keepPreviousData, // For pagination
  })
}

// Search suggestions hook with debouncing
export function useSearchSuggestions(channelId: number, query: string, limit = 5) {
  return useQuery({
    queryKey: searchKeys.suggestion(channelId, query),
    queryFn: () => searchApi.getSearchSuggestions(channelId, query, limit),
    enabled: !!channelId && !!query && query.length > 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
    select: (data) => data || [],
  })
}

// Trending searches hook
export function useTrendingSearches(channelId: number, limit = 10) {
  return useQuery({
    queryKey: searchKeys.trending(channelId),
    queryFn: () => searchApi.getTrendingSearches(channelId, limit),
    enabled: !!channelId,
    staleTime: 15 * 60 * 1000, // 15 minutes
    select: (data) => data || [],
  })
}

// Available filters hook
export function useAvailableFilters(channelId: number) {
  return useQuery({
    queryKey: searchKeys.filters(channelId),
    queryFn: () => searchApi.getAvailableFilters(channelId),
    enabled: !!channelId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    select: (data) => data || {},
  })
}

// Tag suggestions hook with debouncing
export function useTagSuggestions(channelId: number, query: string, limit = 10) {
  return useQuery({
    queryKey: searchKeys.tagSuggestions(channelId, query),
    queryFn: () => searchApi.getTagSuggestions(channelId, query, limit),
    enabled: !!channelId && !!query && query.length > 1,
    staleTime: 2 * 60 * 1000, // 2 minutes
    select: (data) => data || { suggestions: [], query: '', total_count: 0 },
  })
}

// Rebuild search index mutation
export function useRebuildSearchIndex() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (channelId?: number) => searchApi.rebuildSearchIndex(channelId),
    onSuccess: (data, channelId) => {
      // Invalidate all search-related queries
      queryClient.invalidateQueries({ queryKey: searchKeys.searches() })
      
      if (channelId) {
        queryClient.invalidateQueries({ queryKey: searchKeys.filters(channelId) })
      }
      
      toast.success('Search index rebuilt successfully')
    },
    onError: (error) => {
      console.error('Failed to rebuild search index:', error)
      toast.error('Failed to rebuild search index')
    }
  })
}

// Custom hook for debounced search with local state management
export function useDebouncedSearch(initialChannelId?: number) {
  const [searchState, setSearchState] = React.useState({
    query: '',
    channelId: initialChannelId || 0,
    filters: {},
    isSearching: false,
  })

  const debouncedQuery = useDebounce(searchState.query, 300)

  const searchRequest: SearchRequest = {
    query: debouncedQuery,
    channel_id: searchState.channelId,
    filters: searchState.filters,
    limit: 20,
    offset: 0,
  }

  const searchResults = useSearchEpisodes(searchRequest, !!debouncedQuery)
  const suggestions = useSearchSuggestions(
    searchState.channelId, 
    searchState.query, 
    5
  )

  const handleSearch = (query: string) => {
    setSearchState(prev => ({ ...prev, query, isSearching: true }))
  }

  const handleChannelChange = (channelId: number) => {
    setSearchState(prev => ({ ...prev, channelId }))
  }

  const handleFiltersChange = (filters: SearchFilters) => {
    setSearchState(prev => ({ ...prev, filters }))
  }

  const clearSearch = () => {
    setSearchState(prev => ({ ...prev, query: '', isSearching: false }))
  }

  React.useEffect(() => {
    if (searchResults.data || searchResults.error) {
      setSearchState(prev => ({ ...prev, isSearching: false }))
    }
  }, [searchResults.data, searchResults.error])

  return {
    query: searchState.query,
    channelId: searchState.channelId,
    filters: searchState.filters,
    isSearching: searchState.isSearching,
    searchResults,
    suggestions,
    handleSearch,
    handleChannelChange,
    handleFiltersChange,
    clearSearch,
  }
}

// Simple debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value)

  React.useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

// Import React for hooks
import React from 'react'