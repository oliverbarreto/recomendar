# Implement selection toggle button for videos

_Exported on 1/12/2025 at 13:02:46 WET from Cursor (2.1.41)_

---

**User**

@task-0060-FEATURE-bulk-operations-select-unselect-videos.md (11-17)

We use this button to toggle selection mode<button data-slot="button" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([c…" title="Enter selection mode"></button>

Place the new button to select and to deselect in this row<ForwardRef dir="ltr" data-orientation="horizontal" data-slot="tabs" className="flex flex-col gap-2" children="[Object]" ref={null}>All Videos (50) Pending (50) Reviewed (0) Episodes (0)</ForwardRef>

<div dir="ltr" data-orientation="horizontal" data-slot="tabs" class="flex flex-col gap-2">All Videos (50) Pending (50) Reviewed (0) Episodes (0)</div>

---

**Cursor**

Reviewing the task file and locating the subscriptions/videos page component to add "Select All" and "Deselect All" buttons.

Reading the video-list component to understand the selection logic:

Adding "Select All" and "Deselect All" buttons to the tabs row, visible only in selection mode. Updating the component:

Adding separate "Select All" and "Deselect All" handlers and placing buttons in the tabs row:

```typescriptreact
/**
 * Video List Component
 *
 * Displays a list of YouTube videos with filtering and search
 */
"use client"

import React, { useState, useEffect } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import { Search, Filter, Grid, List as ListIcon, Loader2, CheckSquare, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { YouTubeVideoCard } from "./youtube-video-card"
import {
  useYouTubeVideos,
  useMarkVideoReviewed,
  useDiscardVideo,
  useCreateEpisodeFromVideo,
  useBulkAction,
} from "@/hooks/use-youtube-videos"
import { useChannels } from "@/hooks/use-channels"
import { useFollowedChannels } from "@/hooks/use-followed-channels"
import { YouTubeVideo, YouTubeVideoState, Channel } from "@/types"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select as ChannelSelect,
  SelectContent as ChannelSelectContent,
  SelectItem as ChannelSelectItem,
  SelectTrigger as ChannelSelectTrigger,
  SelectValue as ChannelSelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface VideoListProps {
  className?: string
  viewMode?: "grid" | "list"
  onViewModeChange?: (mode: "grid" | "list") => void
}

export function VideoList({
  className,
  viewMode = "grid",
  onViewModeChange,
}: VideoListProps) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  // Check if we're on the videos page to enable URL params
  const isVideosPage = pathname?.startsWith("/subscriptions/videos")

  // Read initial values from URL params if on videos page
  const getInitialState = (): YouTubeVideoState | "all" => {
    if (!isVideosPage) return "all"
    const stateParam = searchParams.get("state")
    if (!stateParam || stateParam === "all") return "all"
    try {
      return stateParam as YouTubeVideoState
    } catch {
      return "all"
    }
  }

  const getInitialChannel = (): number | "all" => {
    if (!isVideosPage) return "all"
    const channelParam = searchParams.get("channel")
    if (!channelParam || channelParam === "all") return "all"
    const channelId = parseInt(channelParam)
    return isNaN(channelId) ? "all" : channelId
  }

  const getInitialSearch = (): string => {
    if (!isVideosPage) return ""
    return searchParams.get("search") || ""
  }

  const [searchQuery, setSearchQuery] = useState(getInitialSearch)
  const [selectedState, setSelectedState] = useState<YouTubeVideoState | "all">(
    getInitialState
  )
  const [selectedChannel, setSelectedChannel] = useState<number | "all">(
    getInitialChannel
  )
  const [selectedYear, setSelectedYear] = useState<number | "all">("all")
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedVideoIds, setSelectedVideoIds] = useState<Set<number>>(new Set())
  const [createEpisodeDialogOpen, setCreateEpisodeDialogOpen] = useState(false)
  const [bulkCreateEpisodeDialogOpen, setBulkCreateEpisodeDialogOpen] = useState(false)
  const [selectedVideoForEpisode, setSelectedVideoForEpisode] =
    useState<YouTubeVideo | null>(null)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  // Track if we're updating from URL to prevent loops
  const isUpdatingFromURL = React.useRef(false)

  // Update URL when filters change (only on videos page)
  const updateURLParams = React.useCallback(
    (
      state: YouTubeVideoState | "all",
      channel: number | "all",
      search: string
    ) => {
      if (!isVideosPage || isUpdatingFromURL.current) return

      const params = new URLSearchParams()

      if (state && state !== "all") {
        params.set("state", state)
      }

      if (channel && channel !== "all") {
        params.set("channel", channel.toString())
      }

      if (search.trim()) {
        params.set("search", search.trim())
      }

      const queryString = params.toString()
      const newUrl = `/subscriptions/videos${
        queryString ? `?${queryString}` : ""
      }`
      const currentUrl = `/subscriptions/videos${
        searchParams.toString() ? `?${searchParams.toString()}` : ""
      }`

      // Only update if URL actually changed
      if (newUrl !== currentUrl) {
        router.replace(newUrl, { scroll: false })
      }
    },
    [isVideosPage, router, searchParams]
  )

  // Sync state with URL params when URL changes (e.g., browser back/forward)
  useEffect(() => {
    if (!isVideosPage) return

    const urlState = getInitialState()
    const urlChannel = getInitialChannel()
    const urlSearch = getInitialSearch()

    // Check if URL params differ from current state
    if (
      urlState !== selectedState ||
      urlChannel !== selectedChannel ||
      urlSearch !== searchQuery
    ) {
      isUpdatingFromURL.current = true
      if (urlState !== selectedState) setSelectedState(urlState)
      if (urlChannel !== selectedChannel) setSelectedChannel(urlChannel)
      if (urlSearch !== searchQuery) setSearchQuery(urlSearch)
      // Reset flag after state updates
      setTimeout(() => {
        isUpdatingFromURL.current = false
      }, 0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.toString(), isVideosPage]) // Only depend on searchParams string representation

  // Debounced search update
  useEffect(() => {
    if (!isVideosPage) return

    const timeoutId = setTimeout(() => {
      updateURLParams(selectedState, selectedChannel, searchQuery)
    }, 300) // 300ms debounce for search

    return () => clearTimeout(timeoutId)
  }, [
    searchQuery,
    isVideosPage,
    updateURLParams,
    selectedState,
    selectedChannel,
  ])

  // Immediate update for state and channel changes (not debounced, but skip if search is changing)
  useEffect(() => {
    if (!isVideosPage || isUpdatingFromURL.current) return
    // Only update immediately for state/channel, search is handled by debounced effect
    updateURLParams(selectedState, selectedChannel, searchQuery)
  }, [
    selectedState,
    selectedChannel,
    isVideosPage,
    updateURLParams,
    searchQuery,
  ])

  // Build filters
  const filters = {
    search: searchQuery || undefined,
    state: selectedState !== "all" ? selectedState : undefined,
    followed_channel_id:
      selectedChannel !== "all" ? selectedChannel : undefined,
    publish_year: selectedYear !== "all" ? selectedYear : undefined,
    skip: 0,
    limit: 50,
  }

  const { data: videos = [], isLoading, error } = useYouTubeVideos(filters)
  const { data: channels = [] } = useChannels()
  const { data: followedChannels = [] } = useFollowedChannels()
  const markReviewedMutation = useMarkVideoReviewed()
  const discardMutation = useDiscardVideo()
  const createEpisodeMutation = useCreateEpisodeFromVideo()
  const bulkActionMutation = useBulkAction()

  // Auto-select channel when dialog opens and channels are loaded
  useEffect(() => {
    if (
      createEpisodeDialogOpen &&
      channels.length === 1 &&
      !selectedPodcastChannel
    ) {
      setSelectedPodcastChannel(channels[0].id)
    }
  }, [createEpisodeDialogOpen, channels, selectedPodcastChannel])

  const handleReview = async (video: YouTubeVideo) => {
    await markReviewedMutation.mutateAsync(video.id)
  }

  const handleDiscard = async (video: YouTubeVideo) => {
    await discardMutation.mutateAsync(video.id)
  }

  const handleCreateEpisode = (video: YouTubeVideo) => {
    setSelectedVideoForEpisode(video)
    // Pre-select the first channel if there's only one available
    if (channels.length === 1) {
      setSelectedPodcastChannel(channels[0].id)
    }
    setCreateEpisodeDialogOpen(true)
  }

  const handleCreateEpisodeSubmit = async () => {
    if (!selectedVideoForEpisode || !selectedPodcastChannel) return

    await createEpisodeMutation.mutateAsync({
      id: selectedVideoForEpisode.id,
      data: { channel_id: selectedPodcastChannel },
    })

    setCreateEpisodeDialogOpen(false)
    setSelectedVideoForEpisode(null)
    setSelectedPodcastChannel(null)
  }

  const handleViewYouTube = (video: YouTubeVideo) => {
    window.open(video.url, "_blank")
  }

  const handleDialogClose = (open: boolean) => {
    setCreateEpisodeDialogOpen(open)
    if (!open) {
      // Reset state when dialog closes
      setSelectedVideoForEpisode(null)
      setSelectedPodcastChannel(null)
    }
  }

  // Toggle selection mode
  const handleToggleSelectionMode = () => {
    setSelectionMode(!selectionMode)
    setSelectedVideoIds(new Set())
  }

  // Toggle video selection
  const handleToggleVideoSelection = (videoId: number) => {
    const newSelection = new Set(selectedVideoIds)
    if (newSelection.has(videoId)) {
      newSelection.delete(videoId)
    } else {
      newSelection.add(videoId)
    }
    setSelectedVideoIds(newSelection)
  }

  // Select all videos
  const handleSelectAll = () => {
    if (selectedVideoIds.size === videos.length) {
      setSelectedVideoIds(new Set())
    } else {
      setSelectedVideoIds(new Set(videos.map(v => v.id)))
    }
  }

  // Select all videos (separate handler for clarity)
  const handleSelectAllVideos = () => {
    setSelectedVideoIds(new Set(videos.map(v => v.id)))
  }

  // Deselect all videos
  const handleDeselectAllVideos = () => {
    setSelectedVideoIds(new Set())
  }

  // Bulk action handlers
  const handleBulkReview = async () => {
    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'review'
    })
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
  }

  const handleBulkDiscard = async () => {
    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'discard'
    })
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
  }

  const handleBulkCreateEpisode = () => {
    setBulkCreateEpisodeDialogOpen(true)
  }

  const handleBulkCreateEpisodeSubmit = async () => {
    if (!selectedPodcastChannel) return

    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'create_episode',
      channel_id: selectedPodcastChannel
    })
    setBulkCreateEpisodeDialogOpen(false)
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
    setSelectedPodcastChannel(null)
  }

  // Generate year options (current year back to 2020)
  const currentYear = new Date().getFullYear()
  const yearOptions = Array.from(
    { length: currentYear - 2020 + 1 },
    (_, i) => currentYear - i
  )

  // Calculate counts for all videos regardless of current filter
  // We need to fetch all videos to get accurate counts, but for now we'll use the current filtered list
  const pendingVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.PENDING_REVIEW
  )
  const reviewedVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.REVIEWED
  )
  const episodeCreatedVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.EPISODE_CREATED
  )

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search videos..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              // Update URL immediately for search (debounced in URL update effect)
            }}
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={
              selectedChannel === "all"
                ? "all"
                : selectedChannel.toString()
            }
            onValueChange={(value) =>
              setSelectedChannel(value === "all" ? "all" : parseInt(value))
            }
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by channel" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Channels</SelectItem>
              {followedChannels.map((channel) => (
                <SelectItem key={channel.id} value={channel.id.toString()}>
                  {channel.youtube_channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by state" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All States</SelectItem>
              <SelectItem value={YouTubeVideoState.PENDING_REVIEW}>
                Pending Review
              </SelectItem>
              <SelectItem value={YouTubeVideoState.REVIEWED}>
                Reviewed
              </SelectItem>
              <SelectItem value={YouTubeVideoState.EPISODE_CREATED}>
                Episode Created
              </SelectItem>
              <SelectItem value={YouTubeVideoState.DOWNLOADING}>
                Downloading
              </SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={selectedYear === "all" ? "all" : selectedYear.toString()}
            onValueChange={(value) =>
              setSelectedYear(value === "all" ? "all" : parseInt(value))
            }
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Filter by year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {yearOptions.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex gap-2">
            <Button
              variant={selectionMode ? "default" : "outline"}
              size="icon"
              onClick={handleToggleSelectionMode}
              title={selectionMode ? "Exit selection mode" : "Enter selection mode"}
            >
              {selectionMode ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => onViewModeChange?.("grid")}
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="icon"
              onClick={() => onViewModeChange?.("list")}
            >
              <ListIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectionMode && selectedVideoIds.size > 0 && (
        <div className="bg-muted p-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">
              {selectedVideoIds.size} video(s) selected
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
            >
              {selectedVideoIds.size === videos.length ? "Deselect All" : "Select All"}
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkReview}
              disabled={bulkActionMutation.isPending}
            >
              Mark as Reviewed
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkDiscard}
              disabled={bulkActionMutation.isPending}
            >
              Discard
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleBulkCreateEpisode}
              disabled={bulkActionMutation.isPending}
            >
              Create Episodes
            </Button>
          </div>
        </div>
      )}

      {/* Tabs for quick filtering */}
      <Tabs
        value={selectedState === "all" ? "all" : selectedState}
        onValueChange={(value) =>
          setSelectedState(value as YouTubeVideoState | "all")
        }
      >
        <TabsList>
          <TabsTrigger value="all">All Videos ({videos.length})</TabsTrigger>
          <TabsTrigger value={YouTubeVideoState.PENDING_REVIEW}>
            Pending ({pendingVideos.length})
          </TabsTrigger>
          <TabsTrigger value={YouTubeVideoState.REVIEWED}>
            Reviewed ({reviewedVideos.length})
          </TabsTrigger>
          <TabsTrigger value={YouTubeVideoState.EPISODE_CREATED}>
            Episodes ({episodeCreatedVideos.length})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Video Grid/List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="text-center py-12 text-destructive">
          Error loading videos:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No videos found. Try adjusting your filters.
        </div>
      ) : (
        <div
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
              : "space-y-4"
          )}
        >
          {videos.map((video) => (
            <YouTubeVideoCard
              key={video.id}
              video={video}
              onReview={handleReview}
              onDiscard={handleDiscard}
              onCreateEpisode={handleCreateEpisode}
              onViewYouTube={handleViewYouTube}
              selectionMode={selectionMode}
              isSelected={selectedVideoIds.has(video.id)}
              onToggleSelection={handleToggleVideoSelection}
            />
          ))}
        </div>
      )}

      {/* Create Episode Dialog */}
      <Dialog open={createEpisodeDialogOpen} onOpenChange={handleDialogClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Episode from Video</DialogTitle>
            <DialogDescription>
              Select a podcast channel where the episode will be created.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Podcast Channel</Label>
              <ChannelSelect
                value={selectedPodcastChannel?.toString()}
                onValueChange={(value) =>
                  setSelectedPodcastChannel(parseInt(value))
                }
              >
                <ChannelSelectTrigger>
                  <ChannelSelectValue placeholder="Select a podcast channel" />
                </ChannelSelectTrigger>
                <ChannelSelectContent>
                  {channels.map((channel: Channel) => (
                    <ChannelSelectItem
                      key={channel.id}
                      value={channel.id.toString()}
                    >
                      {channel.name}
                    </ChannelSelectItem>
                  ))}
                </ChannelSelectContent>
              </ChannelSelect>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setCreateEpisodeDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateEpisodeSubmit}
                disabled={
                  !selectedPodcastChannel || createEpisodeMutation.isPending
                }
              >
                {createEpisodeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Episode"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Bulk Create Episode Dialog */}
      <Dialog open={bulkCreateEpisodeDialogOpen} onOpenChange={setBulkCreateEpisodeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Episodes from Videos</DialogTitle>
            <DialogDescription>
              Select a podcast channel where {selectedVideoIds.size} episode(s) will be created.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Podcast Channel</Label>
              <ChannelSelect
                value={selectedPodcastChannel?.toString()}
                onValueChange={(value) =>
                  setSelectedPodcastChannel(parseInt(value))
                }
              >
                <ChannelSelectTrigger>
                  <ChannelSelectValue placeholder="Select a podcast channel" />
                </ChannelSelectTrigger>
                <ChannelSelectContent>
                  {channels.map((channel: Channel) => (
                    <ChannelSelectItem
                      key={channel.id}
                      value={channel.id.toString()}
                    >
                      {channel.name}
                    </ChannelSelectItem>
                  ))}
                </ChannelSelectContent>
              </ChannelSelect>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setBulkCreateEpisodeDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleBulkCreateEpisodeSubmit}
                disabled={
                  !selectedPodcastChannel || bulkActionMutation.isPending
                }
              >
                {bulkActionMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  `Create ${selectedVideoIds.size} Episode(s)`
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

```typescriptreact
/**
 * Video List Component
 *
 * Displays a list of YouTube videos with filtering and search
 */
"use client"

import React, { useState, useEffect } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import { Search, Filter, Grid, List as ListIcon, Loader2, CheckSquare, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { YouTubeVideoCard } from "./youtube-video-card"
import {
  useYouTubeVideos,
  useMarkVideoReviewed,
  useDiscardVideo,
  useCreateEpisodeFromVideo,
  useBulkAction,
} from "@/hooks/use-youtube-videos"
import { useChannels } from "@/hooks/use-channels"
import { useFollowedChannels } from "@/hooks/use-followed-channels"
import { YouTubeVideo, YouTubeVideoState, Channel } from "@/types"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select as ChannelSelect,
  SelectContent as ChannelSelectContent,
  SelectItem as ChannelSelectItem,
  SelectTrigger as ChannelSelectTrigger,
  SelectValue as ChannelSelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface VideoListProps {
  className?: string
  viewMode?: "grid" | "list"
  onViewModeChange?: (mode: "grid" | "list") => void
}

export function VideoList({
  className,
  viewMode = "grid",
  onViewModeChange,
}: VideoListProps) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  // Check if we're on the videos page to enable URL params
  const isVideosPage = pathname?.startsWith("/subscriptions/videos")

  // Read initial values from URL params if on videos page
  const getInitialState = (): YouTubeVideoState | "all" => {
    if (!isVideosPage) return "all"
    const stateParam = searchParams.get("state")
    if (!stateParam || stateParam === "all") return "all"
    try {
      return stateParam as YouTubeVideoState
    } catch {
      return "all"
    }
  }

  const getInitialChannel = (): number | "all" => {
    if (!isVideosPage) return "all"
    const channelParam = searchParams.get("channel")
    if (!channelParam || channelParam === "all") return "all"
    const channelId = parseInt(channelParam)
    return isNaN(channelId) ? "all" : channelId
  }

  const getInitialSearch = (): string => {
    if (!isVideosPage) return ""
    return searchParams.get("search") || ""
  }

  const [searchQuery, setSearchQuery] = useState(getInitialSearch)
  const [selectedState, setSelectedState] = useState<YouTubeVideoState | "all">(
    getInitialState
  )
  const [selectedChannel, setSelectedChannel] = useState<number | "all">(
    getInitialChannel
  )
  const [selectedYear, setSelectedYear] = useState<number | "all">("all")
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedVideoIds, setSelectedVideoIds] = useState<Set<number>>(new Set())
  const [createEpisodeDialogOpen, setCreateEpisodeDialogOpen] = useState(false)
  const [bulkCreateEpisodeDialogOpen, setBulkCreateEpisodeDialogOpen] = useState(false)
  const [selectedVideoForEpisode, setSelectedVideoForEpisode] =
    useState<YouTubeVideo | null>(null)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  // Track if we're updating from URL to prevent loops
  const isUpdatingFromURL = React.useRef(false)

  // Update URL when filters change (only on videos page)
  const updateURLParams = React.useCallback(
    (
      state: YouTubeVideoState | "all",
      channel: number | "all",
      search: string
    ) => {
      if (!isVideosPage || isUpdatingFromURL.current) return

      const params = new URLSearchParams()

      if (state && state !== "all") {
        params.set("state", state)
      }

      if (channel && channel !== "all") {
        params.set("channel", channel.toString())
      }

      if (search.trim()) {
        params.set("search", search.trim())
      }

      const queryString = params.toString()
      const newUrl = `/subscriptions/videos${
        queryString ? `?${queryString}` : ""
      }`
      const currentUrl = `/subscriptions/videos${
        searchParams.toString() ? `?${searchParams.toString()}` : ""
      }`

      // Only update if URL actually changed
      if (newUrl !== currentUrl) {
        router.replace(newUrl, { scroll: false })
      }
    },
    [isVideosPage, router, searchParams]
  )

  // Sync state with URL params when URL changes (e.g., browser back/forward)
  useEffect(() => {
    if (!isVideosPage) return

    const urlState = getInitialState()
    const urlChannel = getInitialChannel()
    const urlSearch = getInitialSearch()

    // Check if URL params differ from current state
    if (
      urlState !== selectedState ||
      urlChannel !== selectedChannel ||
      urlSearch !== searchQuery
    ) {
      isUpdatingFromURL.current = true
      if (urlState !== selectedState) setSelectedState(urlState)
      if (urlChannel !== selectedChannel) setSelectedChannel(urlChannel)
      if (urlSearch !== searchQuery) setSearchQuery(urlSearch)
      // Reset flag after state updates
      setTimeout(() => {
        isUpdatingFromURL.current = false
      }, 0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.toString(), isVideosPage]) // Only depend on searchParams string representation

  // Debounced search update
  useEffect(() => {
    if (!isVideosPage) return

    const timeoutId = setTimeout(() => {
      updateURLParams(selectedState, selectedChannel, searchQuery)
    }, 300) // 300ms debounce for search

    return () => clearTimeout(timeoutId)
  }, [
    searchQuery,
    isVideosPage,
    updateURLParams,
    selectedState,
    selectedChannel,
  ])

  // Immediate update for state and channel changes (not debounced, but skip if search is changing)
  useEffect(() => {
    if (!isVideosPage || isUpdatingFromURL.current) return
    // Only update immediately for state/channel, search is handled by debounced effect
    updateURLParams(selectedState, selectedChannel, searchQuery)
  }, [
    selectedState,
    selectedChannel,
    isVideosPage,
    updateURLParams,
    searchQuery,
  ])

  // Build filters
  const filters = {
    search: searchQuery || undefined,
    state: selectedState !== "all" ? selectedState : undefined,
    followed_channel_id:
      selectedChannel !== "all" ? selectedChannel : undefined,
    publish_year: selectedYear !== "all" ? selectedYear : undefined,
    skip: 0,
    limit: 50,
  }

  const { data: videos = [], isLoading, error } = useYouTubeVideos(filters)
  const { data: channels = [] } = useChannels()
  const { data: followedChannels = [] } = useFollowedChannels()
  const markReviewedMutation = useMarkVideoReviewed()
  const discardMutation = useDiscardVideo()
  const createEpisodeMutation = useCreateEpisodeFromVideo()
  const bulkActionMutation = useBulkAction()

  // Auto-select channel when dialog opens and channels are loaded
  useEffect(() => {
    if (
      createEpisodeDialogOpen &&
      channels.length === 1 &&
      !selectedPodcastChannel
    ) {
      setSelectedPodcastChannel(channels[0].id)
    }
  }, [createEpisodeDialogOpen, channels, selectedPodcastChannel])

  const handleReview = async (video: YouTubeVideo) => {
    await markReviewedMutation.mutateAsync(video.id)
  }

  const handleDiscard = async (video: YouTubeVideo) => {
    await discardMutation.mutateAsync(video.id)
  }

  const handleCreateEpisode = (video: YouTubeVideo) => {
    setSelectedVideoForEpisode(video)
    // Pre-select the first channel if there's only one available
    if (channels.length === 1) {
      setSelectedPodcastChannel(channels[0].id)
    }
    setCreateEpisodeDialogOpen(true)
  }

  const handleCreateEpisodeSubmit = async () => {
    if (!selectedVideoForEpisode || !selectedPodcastChannel) return

    await createEpisodeMutation.mutateAsync({
      id: selectedVideoForEpisode.id,
      data: { channel_id: selectedPodcastChannel },
    })

    setCreateEpisodeDialogOpen(false)
    setSelectedVideoForEpisode(null)
    setSelectedPodcastChannel(null)
  }

  const handleViewYouTube = (video: YouTubeVideo) => {
    window.open(video.url, "_blank")
  }

  const handleDialogClose = (open: boolean) => {
    setCreateEpisodeDialogOpen(open)
    if (!open) {
      // Reset state when dialog closes
      setSelectedVideoForEpisode(null)
      setSelectedPodcastChannel(null)
    }
  }

  // Toggle selection mode
  const handleToggleSelectionMode = () => {
    setSelectionMode(!selectionMode)
    setSelectedVideoIds(new Set())
  }

  // Toggle video selection
  const handleToggleVideoSelection = (videoId: number) => {
    const newSelection = new Set(selectedVideoIds)
    if (newSelection.has(videoId)) {
      newSelection.delete(videoId)
    } else {
      newSelection.add(videoId)
    }
    setSelectedVideoIds(newSelection)
  }

  // Select all videos
  const handleSelectAll = () => {
    if (selectedVideoIds.size === videos.length) {
      setSelectedVideoIds(new Set())
    } else {
      setSelectedVideoIds(new Set(videos.map(v => v.id)))
    }
  }

  // Select all videos (separate handler for clarity)
  const handleSelectAllVideos = () => {
    setSelectedVideoIds(new Set(videos.map(v => v.id)))
  }

  // Deselect all videos
  const handleDeselectAllVideos = () => {
    setSelectedVideoIds(new Set())
  }

  // Bulk action handlers
  const handleBulkReview = async () => {
    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'review'
    })
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
  }

  const handleBulkDiscard = async () => {
    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'discard'
    })
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
  }

  const handleBulkCreateEpisode = () => {
    setBulkCreateEpisodeDialogOpen(true)
  }

  const handleBulkCreateEpisodeSubmit = async () => {
    if (!selectedPodcastChannel) return

    await bulkActionMutation.mutateAsync({
      video_ids: Array.from(selectedVideoIds),
      action: 'create_episode',
      channel_id: selectedPodcastChannel
    })
    setBulkCreateEpisodeDialogOpen(false)
    setSelectedVideoIds(new Set())
    setSelectionMode(false)
    setSelectedPodcastChannel(null)
  }

  // Generate year options (current year back to 2020)
  const currentYear = new Date().getFullYear()
  const yearOptions = Array.from(
    { length: currentYear - 2020 + 1 },
    (_, i) => currentYear - i
  )

  // Calculate counts for all videos regardless of current filter
  // We need to fetch all videos to get accurate counts, but for now we'll use the current filtered list
  const pendingVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.PENDING_REVIEW
  )
  const reviewedVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.REVIEWED
  )
  const episodeCreatedVideos = videos.filter(
    (v) => v.state === YouTubeVideoState.EPISODE_CREATED
  )

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search videos..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              // Update URL immediately for search (debounced in URL update effect)
            }}
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={
              selectedChannel === "all"
                ? "all"
                : selectedChannel.toString()
            }
            onValueChange={(value) =>
              setSelectedChannel(value === "all" ? "all" : parseInt(value))
            }
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by channel" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Channels</SelectItem>
              {followedChannels.map((channel) => (
                <SelectItem key={channel.id} value={channel.id.toString()}>
                  {channel.youtube_channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by state" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All States</SelectItem>
              <SelectItem value={YouTubeVideoState.PENDING_REVIEW}>
                Pending Review
              </SelectItem>
              <SelectItem value={YouTubeVideoState.REVIEWED}>
                Reviewed
              </SelectItem>
              <SelectItem value={YouTubeVideoState.EPISODE_CREATED}>
                Episode Created
              </SelectItem>
              <SelectItem value={YouTubeVideoState.DOWNLOADING}>
                Downloading
              </SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={selectedYear === "all" ? "all" : selectedYear.toString()}
            onValueChange={(value) =>
              setSelectedYear(value === "all" ? "all" : parseInt(value))
            }
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Filter by year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {yearOptions.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex gap-2">
            <Button
              variant={selectionMode ? "default" : "outline"}
              size="icon"
              onClick={handleToggleSelectionMode}
              title={selectionMode ? "Exit selection mode" : "Enter selection mode"}
            >
              {selectionMode ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => onViewModeChange?.("grid")}
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="icon"
              onClick={() => onViewModeChange?.("list")}
            >
              <ListIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectionMode && selectedVideoIds.size > 0 && (
        <div className="bg-muted p-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">
              {selectedVideoIds.size} video(s) selected
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
            >
              {selectedVideoIds.size === videos.length ? "Deselect All" : "Select All"}
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkReview}
              disabled={bulkActionMutation.isPending}
            >
              Mark as Reviewed
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkDiscard}
              disabled={bulkActionMutation.isPending}
            >
              Discard
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleBulkCreateEpisode}
              disabled={bulkActionMutation.isPending}
            >
              Create Episodes
            </Button>
          </div>
        </div>
      )}

      {/* Tabs for quick filtering */}
      <div className="flex items-center justify-between gap-4">
        <Tabs
          value={selectedState === "all" ? "all" : selectedState}
          onValueChange={(value) =>
            setSelectedState(value as YouTubeVideoState | "all")
          }
        >
          <TabsList>
            <TabsTrigger value="all">All Videos ({videos.length})</TabsTrigger>
            <TabsTrigger value={YouTubeVideoState.PENDING_REVIEW}>
              Pending ({pendingVideos.length})
            </TabsTrigger>
            <TabsTrigger value={YouTubeVideoState.REVIEWED}>
              Reviewed ({reviewedVideos.length})
            </TabsTrigger>
            <TabsTrigger value={YouTubeVideoState.EPISODE_CREATED}>
              Episodes ({episodeCreatedVideos.length})
            </TabsTrigger>
          </TabsList>
        </Tabs>
        {selectionMode && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAllVideos}
              disabled={selectedVideoIds.size === videos.length}
            >
              Select All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDeselectAllVideos}
              disabled={selectedVideoIds.size === 0}
            >
              Deselect All
            </Button>
          </div>
        )}
      </div>

      {/* Video Grid/List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="text-center py-12 text-destructive">
          Error loading videos:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No videos found. Try adjusting your filters.
        </div>
      ) : (
        <div
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
              : "space-y-4"
          )}
        >
          {videos.map((video) => (
            <YouTubeVideoCard
              key={video.id}
              video={video}
              onReview={handleReview}
              onDiscard={handleDiscard}
              onCreateEpisode={handleCreateEpisode}
              onViewYouTube={handleViewYouTube}
              selectionMode={selectionMode}
              isSelected={selectedVideoIds.has(video.id)}
              onToggleSelection={handleToggleVideoSelection}
            />
          ))}
        </div>
      )}

      {/* Create Episode Dialog */}
      <Dialog open={createEpisodeDialogOpen} onOpenChange={handleDialogClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Episode from Video</DialogTitle>
            <DialogDescription>
              Select a podcast channel where the episode will be created.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Podcast Channel</Label>
              <ChannelSelect
                value={selectedPodcastChannel?.toString()}
                onValueChange={(value) =>
                  setSelectedPodcastChannel(parseInt(value))
                }
              >
                <ChannelSelectTrigger>
                  <ChannelSelectValue placeholder="Select a podcast channel" />
                </ChannelSelectTrigger>
                <ChannelSelectContent>
                  {channels.map((channel: Channel) => (
                    <ChannelSelectItem
                      key={channel.id}
                      value={channel.id.toString()}
                    >
                      {channel.name}
                    </ChannelSelectItem>
                  ))}
                </ChannelSelectContent>
              </ChannelSelect>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setCreateEpisodeDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateEpisodeSubmit}
                disabled={
                  !selectedPodcastChannel || createEpisodeMutation.isPending
                }
              >
                {createEpisodeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Episode"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Bulk Create Episode Dialog */}
      <Dialog open={bulkCreateEpisodeDialogOpen} onOpenChange={setBulkCreateEpisodeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Episodes from Videos</DialogTitle>
            <DialogDescription>
              Select a podcast channel where {selectedVideoIds.size} episode(s) will be created.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Podcast Channel</Label>
              <ChannelSelect
                value={selectedPodcastChannel?.toString()}
                onValueChange={(value) =>
                  setSelectedPodcastChannel(parseInt(value))
                }
              >
                <ChannelSelectTrigger>
                  <ChannelSelectValue placeholder="Select a podcast channel" />
                </ChannelSelectTrigger>
                <ChannelSelectContent>
                  {channels.map((channel: Channel) => (
                    <ChannelSelectItem
                      key={channel.id}
                      value={channel.id.toString()}
                    >
                      {channel.name}
                    </ChannelSelectItem>
                  ))}
                </ChannelSelectContent>
              </ChannelSelect>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setBulkCreateEpisodeDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleBulkCreateEpisodeSubmit}
                disabled={
                  !selectedPodcastChannel || bulkActionMutation.isPending
                }
              >
                {bulkActionMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  `Create ${selectedVideoIds.size} Episode(s)`
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Checking for linting errors:

Verifying the implementation by reading the updated section:

## Summary

Added "Select All" and "Deselect All" buttons to the subscriptions/videos page.

### Changes Made:

1. Added two handler functions:

   - `handleSelectAllVideos()`: Selects all videos in the current filtered list
   - `handleDeselectAllVideos()`: Clears all selections

2. Updated the tabs section:

   - Wrapped the `Tabs` component in a flex container with `justify-between`
   - Added a conditional button group that appears only when `selectionMode` is active
   - Placed the buttons on the right side of the tabs row

3. Button behavior:
   - "Select All" is disabled when all videos are already selected
   - "Deselect All" is disabled when no videos are selected
   - Both buttons use `outline` variant and `sm` size to match the existing UI

The buttons appear in the tabs row (next to "All Videos", "Pending", "Reviewed", "Episodes") only when selection mode is active, allowing quick selection/deselection of all videos without going through them individually.

The existing "Select All" toggle button in the Bulk Action Toolbar remains unchanged, so users have both options available.
