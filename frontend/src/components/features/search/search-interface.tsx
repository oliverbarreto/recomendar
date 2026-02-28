/**
 * Advanced search interface with filtering and sorting capabilities
 */
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { EpisodeGrid } from '@/components/features/episodes/episode-grid'
import { PaginationControls, usePagination } from '@/components/shared/pagination-controls'
import {
  Search,
  X,
  Filter,
  Tag as TagIcon,
  Heart
} from 'lucide-react'
import { channelApi, tagApi } from '@/lib/api'

interface Tag {
  id: number
  name: string
  color: string
  usage_count: number
  is_system_tag: boolean
  created_at: string
  updated_at: string
}



interface SearchInterfaceProps {
  /**
   * Optional callback to track episode count changes
   * @param total - Total number of episodes
   * @param filtered - Number of episodes after filtering
   */
  onEpisodeCountChange?: (total: number, filtered: number) => void
  /**
   * Initial search query from URL parameters
   */
  initialSearchQuery?: string
  /**
   * Initial tag IDs from URL parameters
   */
  initialTagIds?: number[]
  /**
   * Initial favorites filter state from URL parameters
   */
  initialFavoritesOnly?: boolean
  /**
   * Initial page number from URL parameters
   */
  initialPage?: number
  /**
   * Initial page size from URL parameters
   */
  initialPageSize?: number
  /**
   * Optional callback to toggle search visibility
   */
  onToggleVisibility?: () => void
  /**
   * Optional callback when filters are cleared
   */
  onClearFilters?: () => void
  /**
   * Whether the search panel is currently visible
   */
  isSearchVisible?: boolean
}

export function SearchInterface({
  onEpisodeCountChange,
  initialSearchQuery = '',
  initialTagIds = [],
  initialFavoritesOnly = false,
  initialPage = 1,
  initialPageSize,
  onToggleVisibility,
  onClearFilters,
  isSearchVisible = false
}: SearchInterfaceProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const searchInputRef = useRef<HTMLInputElement>(null)

  const [searchQuery, setSearchQuery] = useState(initialSearchQuery)
  const [channelId, setChannelId] = useState<number | null>(null)
  const [isLoadingChannel, setIsLoadingChannel] = useState(true)
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>(initialTagIds)
  const [favoritesOnly, setFavoritesOnly] = useState(initialFavoritesOnly)
  const [availableTags, setAvailableTags] = useState<Tag[]>([])
  const [, setIsLoadingTags] = useState(false)
  const [episodeCounts, setEpisodeCounts] = useState({ total: 0, filtered: 0 })

  // Pagination state management using the usePagination hook
  // This provides state management for current page and page size
  const {
    currentPage,
    pageSize,
    handlePageChange,
    handlePageSizeChange,
    reset: resetPagination
  } = usePagination(initialPage, initialPageSize)

  // Function to update URL parameters
  const updateURLParams = (query: string, tagIds: number[], favorites: boolean, page: number, pageSize: number) => {
    const params = new URLSearchParams(searchParams.toString())

    if (query.trim()) {
      params.set('q', query.trim())
    } else {
      params.delete('q')
    }

    if (tagIds.length > 0) {
      params.set('tags', tagIds.join(','))
    } else {
      params.delete('tags')
    }

    if (favorites) {
      params.set('favorites', 'true')
    } else {
      params.delete('favorites')
    }

    if (page > 1) {
      params.set('page', page.toString())
    } else {
      params.delete('page')
    }

    if (pageSize !== 20) {
      params.set('pageSize', pageSize.toString())
    } else {
      params.delete('pageSize')
    }

    // Use replace to avoid adding to history stack for each keystroke
    router.replace(`/channel?${params.toString()}`, { scroll: false })
  }

  // Load channel ID and tags on component mount
  useEffect(() => {
    const loadChannelId = async () => {
      try {
        setIsLoadingChannel(true)
        const channels = await channelApi.getAll({ limit: 1 })
        if (channels.length > 0) {
          const channel = channels[0]
          setChannelId(channel.id)
          // Load tags for this channel
          await loadTags(channel.id)
        }
      } catch (error) {
        console.error('Failed to load channel:', error)
      } finally {
        setIsLoadingChannel(false)
      }
    }

    loadChannelId()
  }, [])

  // Load tags for the channel
  const loadTags = async (channelId: number) => {
    try {
      setIsLoadingTags(true)
      const response = await tagApi.getAll(channelId)
      setAvailableTags(response.tags)
    } catch (error) {
      console.error('Failed to load tags:', error)
      setAvailableTags([])
    } finally {
      setIsLoadingTags(false)
    }
  }

  // Sync URL when search query, tags, favorites, or pagination change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      updateURLParams(searchQuery, selectedTagIds, favoritesOnly, currentPage, pageSize)
    }, 300) // Debounce to avoid too many URL updates

    return () => clearTimeout(timeoutId)
  }, [searchQuery, selectedTagIds, favoritesOnly, currentPage, pageSize, router, searchParams])

  // Handle search query change
  const handleSearchQueryChange = (value: string) => {
    setSearchQuery(value)
  }

  // Handle tag selection
  const handleTagToggle = (tagId: number) => {
    setSelectedTagIds(prev => {
      const newTagIds = prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
      return newTagIds
    })
  }

  // Handle favorites toggle
  const handleFavoritesToggle = () => {
    setFavoritesOnly(prev => !prev)
  }

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('')
    setSelectedTagIds([])
    setFavoritesOnly(false)
    resetPagination()
    onClearFilters?.()
  }

  // Auto focus search input when search becomes visible
  useEffect(() => {
    if (onToggleVisibility && searchInputRef.current) {
      // Small delay to ensure the animation has started
      const timeoutId = setTimeout(() => {
        searchInputRef.current?.focus()
      }, 100)
      return () => clearTimeout(timeoutId)
    }
  }, [onToggleVisibility])

  // Stable callback for episode count changes
  const handleEpisodeCountChange = useCallback((total: number, filtered: number) => {
    onEpisodeCountChange?.(total, filtered)
    setEpisodeCounts({ total, filtered })
  }, [onEpisodeCountChange])

  // Filter status component
  const FilterStatus = ({ totalCount, filteredCount }: { totalCount: number; filteredCount: number }) => {
    const hasFilters = searchQuery || selectedTagIds.length > 0 || favoritesOnly
    const selectedTags = availableTags.filter(tag => selectedTagIds.includes(tag.id))
    const startItem = Math.min((currentPage - 1) * pageSize + 1, totalCount)
    const endItem = Math.min(currentPage * pageSize, totalCount)

    if (!hasFilters && currentPage === 1) {
      return (
        <div className="flex items-center justify-between py-3 px-4 bg-muted/50 rounded-lg border">
          <span className="text-sm text-muted-foreground">
            Showing {totalCount} episode{totalCount !== 1 ? 's' : ''} in total
          </span>
          {onToggleVisibility && (
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleVisibility}
              className="gap-2"
              title="Search Episodes (Cmd+F)"
            >
              <Search className="h-4 w-4" />
              Search
            </Button>
          )}
        </div>
      )
    }

    return (
      <div className="flex items-center justify-between py-3 px-4 bg-muted/50 rounded-lg border">
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium">
            {hasFilters ? (
              `Showing ${filteredCount} out of ${totalCount} episode${totalCount !== 1 ? 's' : ''} in total`
            ) : (
              `Showing ${startItem.toLocaleString()} to ${endItem.toLocaleString()} of ${totalCount.toLocaleString()} episode${totalCount !== 1 ? 's' : ''}`
            )}
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {searchQuery && (
              <Badge variant="secondary" className="gap-1">
                <Search className="h-3 w-3" />
                &quot;{searchQuery}&quot;
              </Badge>
            )}
            {favoritesOnly && (
              <Badge variant="secondary" className="gap-1">
                <Heart className="h-3 w-3 fill-current text-red-500" />
                Favorites Only
              </Badge>
            )}
            {selectedTags.map((tag) => (
              <Badge
                key={tag.id}
                variant="secondary"
                className="gap-1"
                style={{
                  backgroundColor: `${tag.color}20`,
                  borderColor: tag.color,
                  color: tag.color
                }}
              >
                <TagIcon className="h-3 w-3" />
                {tag.name}
              </Badge>
            ))}
            {!hasFilters && currentPage > 1 && (
              <Badge variant="outline" className="gap-1">
                Page {currentPage}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onToggleVisibility && (
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleVisibility}
              className="gap-2"
              title="Search Episodes (Cmd+F)"
            >
              <Search className="h-4 w-4" />
              Search
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={clearFilters}
            className="gap-2"
          >
            <X className="h-3 w-3" />
            Clear Filters
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search Bar with Tag Filter - Only show when search is visible */}
      {onToggleVisibility && isSearchVisible && (
        <div className="animate-in slide-in-from-top-2 fade-in-0 duration-300">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">Search Episodes</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleVisibility}
                className="h-8 w-8 p-0 hover:bg-secondary"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="pt-0">
              {/* Search Input */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  ref={searchInputRef}
                  placeholder="Search episodes by title, description, tags, or keywords..."
                  value={searchQuery}
                  onChange={(e) => handleSearchQueryChange(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Favorites Filter */}
              <div className="flex items-center gap-2 mb-4">
                <Button
                  variant={favoritesOnly ? "default" : "outline"}
                  size="sm"
                  onClick={handleFavoritesToggle}
                  className="gap-2"
                >
                  <Heart className={`h-4 w-4 ${favoritesOnly ? 'fill-current text-white' : 'text-red-500'}`} />
                  {favoritesOnly ? 'Show All' : 'Favorites Only'}
                </Button>
              </div>

              {/* Tag Filter Section */}
              {availableTags.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground">
                      Filter by Tags
                      {selectedTagIds.length > 0 && (
                        <Badge variant="secondary" className="ml-2">
                          {selectedTagIds.length} selected
                        </Badge>
                      )}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {availableTags.map((tag) => {
                      const isSelected = selectedTagIds.includes(tag.id)
                      return (
                        <Badge
                          key={tag.id}
                          variant={isSelected ? "default" : "outline"}
                          className={`cursor-pointer hover:bg-secondary transition-colors ${isSelected ? 'border-primary' : ''
                            }`}
                          style={{
                            backgroundColor: isSelected ? tag.color : undefined,
                            borderColor: isSelected ? tag.color : undefined
                          }}
                          onClick={() => handleTagToggle(tag.id)}
                        >
                          <TagIcon className="h-3 w-3 mr-1" />
                          {tag.name}
                          {tag.usage_count > 0 && (
                            <span className="ml-1 text-xs opacity-70">
                              ({tag.usage_count})
                            </span>
                          )}
                        </Badge>
                      )
                    })}
                  </div>

                  {(searchQuery || selectedTagIds.length > 0 || favoritesOnly) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={clearFilters}
                      className="gap-2"
                    >
                      <X className="h-3 w-3" />
                      Clear All Filters
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results Grid - Always show */}
      {isLoadingChannel ? (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading episodes...</p>
        </div>
      ) : channelId ? (
        <div className="space-y-4">
          {/* Filter Status Bar */}
          <FilterStatus totalCount={episodeCounts.total} filteredCount={episodeCounts.filtered} />

          <EpisodeGrid
            channelId={channelId}
            searchQuery={searchQuery}
            selectedTagIds={selectedTagIds}
            favoritesOnly={favoritesOnly}
            currentPage={currentPage}
            pageSize={pageSize}
            onEpisodeCountChange={handleEpisodeCountChange}
            onPaginationChange={handlePageChange}
          />

          {/* Pagination Controls */}
          {episodeCounts.total > 0 && (
            <PaginationControls
              currentPage={currentPage}
              totalCount={episodeCounts.total}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              className="mt-6"
            />
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Search className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No channel found</h3>
              <p className="text-muted-foreground">
                Please create a channel first to search episodes
              </p>
            </div>
          </CardContent>
        </Card>
      )}

    </div>
  )
}