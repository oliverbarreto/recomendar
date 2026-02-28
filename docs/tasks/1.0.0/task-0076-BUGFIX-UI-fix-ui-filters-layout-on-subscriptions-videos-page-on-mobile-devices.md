# Review all pending videos
_Exported on 7/12/2025 at 8:58:23 WET from Cursor (2.1.49)_

---

**User**

<div class="flex flex-col sm:flex-row gap-4">All Channels All States All Years</div> <div class="flex items-center justify-between gap-4">All Videos (49) Pending (49) Reviewed (0) Episodes (0)</div> 

as you can see in the image, for the "/subscriptions/videos" page in mobile screens we can see the filter textfield and the selectors filters correctly. However, the rest of the buttons to carry out bulk opèrations and to change layout of small cards vs big card, and then the row bellow with the clickable number of videos according to status they are not shown.



explore the code to analyze how to fix it on mobile devices

---

**Cursor**

Exploring the code to identify why bulk operations, layout toggles, and status tabs are hidden on mobile.


Reading the video list component and the videos page to understand the structure:


Checking the Tabs component for mobile responsiveness:


## Issues Identified:

1. **Filters section (lines 376-484)**: The inner flex container with selects and buttons doesn't wrap on mobile, causing overflow. Fixed-width selects (`w-[200px]`, `w-[180px]`, `w-[150px]`) also contribute to overflow.

2. **Tabs section (lines 531-571)**: The `TabsList` uses `w-fit` and tabs have `whitespace-nowrap`, so they overflow horizontally on mobile.

3. **Bulk action toolbar (lines 487-528)**: Uses `justify-between` which can cause button overflow on small screens.

## Proposed Fixes:

```tsx:frontend/src/components/features/subscriptions/video-list.tsx
// ... existing code ...

      {/* Search and Filters */}
      <div className="flex flex-col gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search videos..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
            }}
            className="pl-9"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="w-full sm:w-auto overflow-x-auto">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <TabsList className="w-full sm:w-fit">
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
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0">
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

// ... existing code ...
```

## Changes Summary:

1. Filters section:
   - Changed outer container to `flex flex-col` (always stacks on mobile)
   - Changed inner container to `flex flex-col sm:flex-row gap-2 flex-wrap`
   - Made selects `w-full sm:w-[...]` for mobile
   - Added `ml-auto` to button group to align right on larger screens

2. Bulk action toolbar:
   - Changed to `flex flex-col sm:flex-row` to stack on mobile
   - Added `flex-wrap` to button groups
   - Changed alignment to `items-start sm:items-center`

3. Tabs section:
   - Changed to `flex flex-col sm:flex-row` to stack on mobile
   - Wrapped Tabs in a scrollable container with `overflow-x-auto`
   - Made TabsList `w-full sm:w-fit` for mobile
   - Added `flex-shrink-0` to selection buttons to prevent shrinking

These changes ensure:
- Filters wrap properly on mobile
- Tabs are scrollable horizontally if needed
- Bulk action buttons stack vertically on mobile
- Layout/view toggle buttons remain visible and accessible

Should I apply these changes?

```typescriptreact
// ... existing code ...

      {/* Search and Filters */}
      <div className="flex flex-col gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search videos..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
            }}
            className="pl-9"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="w-full sm:w-auto overflow-x-auto">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <TabsList className="w-full sm:w-fit">
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
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0">
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

// ... existing code ...
```

---

**User**

apply them

---

**Cursor**

Reviewing the current file state, then applying mobile-responsive fixes.


Applying mobile-responsive fixes:


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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="w-full sm:w-auto overflow-x-auto">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <TabsList className="w-full sm:w-fit">
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
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0">
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


Applied mobile-responsive fixes to the video list component. Summary:

## Changes Applied:

### 1. **Filters Section** (lines 390-483)
   - Changed container to `flex flex-col sm:flex-row gap-2 flex-wrap` to wrap on mobile
   - Made selects responsive: `w-full sm:w-[200px]`, `w-full sm:w-[180px]`, `w-full sm:w-[150px]`
   - Added `ml-auto` to the button group to align right on larger screens

### 2. **Bulk Action Toolbar** (lines 487-528)
   - Changed to `flex flex-col sm:flex-row` to stack vertically on mobile
   - Added `items-start sm:items-center` for proper alignment
   - Added `flex-wrap` to both button groups to prevent overflow

### 3. **Tabs Section** (lines 530-571)
   - Changed container to `flex flex-col sm:flex-row` to stack on mobile
   - Wrapped Tabs in a scrollable container with `overflow-x-auto`
   - Made TabsList responsive: `w-full sm:w-fit` for mobile
   - Added `flex-shrink-0` to selection buttons to prevent shrinking

These changes ensure:
- Filters wrap properly on mobile screens
- Tabs are horizontally scrollable if needed on mobile
- Bulk action buttons stack vertically on mobile
- Layout/view toggle buttons remain visible and accessible
- All elements are properly responsive across screen sizes

The page should now display correctly on mobile devices with all controls visible and accessible.

---

**User**

as you can see in the image, in mobile devices the page "/subscriptions/videos" has a weird layout. The text and the button are merely separated. Fix this to properly place the elements in the header section  <div class="flex items-center justify-between">Videos Discover and manage YouTube videos from followed channels Follow Channel</div> 

---

**Cursor**

Checking the page header component and the videos page structure to fix the mobile layout.


The `PageHeader` uses `flex items-center justify-between`, which causes cramped spacing on mobile. Updating it to stack vertically on mobile:


```typescriptreact
/**
 * Page header component for consistent page titles and actions
 */
'use client'

import { ReactNode } from 'react'
import { Separator } from '@/components/ui/separator'

interface PageHeaderProps {
  title: string
  description?: string
  children?: ReactNode
}

export function PageHeader({ title, description, children }: PageHeaderProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
        {children && (
          <div className="flex items-center space-x-2 flex-shrink-0">
            {children}
          </div>
        )}
      </div>
      <Separator />
    </div>
  )
}
```

Fixed the mobile layout issue in the `PageHeader` component.

## Changes Applied:

**PageHeader Component** (`frontend/src/components/layout/page-header.tsx`):
- Changed the flex container from `flex items-center justify-between` to `flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4`
  - Stacks vertically on mobile (`flex-col`)
  - Horizontal layout on larger screens (`sm:flex-row`) with proper alignment
  - Added `gap-4` for consistent spacing
- Added `flex-shrink-0` to the children container to prevent the button from shrinking

On mobile:
- The title and description stack vertically
- The "Follow Channel" button appears below with proper spacing
- Elements are no longer cramped together

On larger screens (sm and above):
- The layout remains horizontal with the title/description on the left and the button on the right

The header should now display correctly on all screen sizes.

---

**User**

<ForwardRef role="tablist" aria-orientation="horizontal" data-slot="tabs-list" className="bg-muted text-muted-foreground inline-flex h-9 items-center justify-center rounded-lg p-[3px] w-full sm:w-fit" children="[Array]" ref="[Function]" tabIndex={0} data-orientation="horizontal" style="[Object]" onMouseDown="[Function]" onFocus="[Function]" onBlur="[Function]">All Videos (49) Pending (49) Reviewed (0) Episodes (0)</ForwardRef>
<div role="tablist" aria-orientation="horizontal" data-slot="tabs-list" class="bg-muted text-muted-foreground inline-flex h-9 items-center justify-center rounded-lg p-[3px] w-full sm:w-fit" tabindex="0" data-orientation="horizontal" style="outline: none;">All Videos (49) Pending (49) Reviewed (0) Episodes (0)</div> Alo in mobile devices, as you can see in the image, the section with the clickable pills for "all videos", "Pending", "Reviewed" and "Episodes", look very stuffed and compacted. Make it look better and give marding/padding left and right of all elements

---

**Cursor**

Reviewing the tabs implementation to improve mobile spacing and readability:


Improving mobile spacing for the tabs. Updating the tabs section and adding padding/margins:


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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 px-1 sm:px-0">
        <div className="w-full sm:w-auto overflow-x-auto -mx-1 sm:mx-0 px-1 sm:px-0">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <TabsList className="w-full sm:w-fit min-w-fit">
              <TabsTrigger value="all" className="px-3 sm:px-2">All Videos ({videos.length})</TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.PENDING_REVIEW} className="px-3 sm:px-2">
                Pending ({pendingVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.REVIEWED} className="px-3 sm:px-2">
                Reviewed ({reviewedVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.EPISODE_CREATED} className="px-3 sm:px-2">
                Episodes ({episodeCreatedVideos.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0 px-1 sm:px-0">
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

Updating the tabs component to prevent tabs from stretching on mobile and improve spacing:


```typescriptreact
"use client"

import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"

import { cn } from "@/lib/utils"

function Tabs({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      className={cn("flex flex-col gap-2", className)}
      {...props}
    />
  )
}

function TabsList({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn(
        "bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]",
        className
      )}
      {...props}
    />
  )
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "data-[state=active]:bg-background dark:data-[state=active]:text-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring dark:data-[state=active]:border-input dark:data-[state=active]:bg-input/30 text-foreground dark:text-muted-foreground inline-flex h-[calc(100%-1px)] sm:flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:ring-[3px] focus-visible:outline-1 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:shadow-sm [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    />
  )
}

function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("flex-1 outline-none", className)}
      {...props}
    />
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent }

```

Refining the approach: making tabs horizontally scrollable on mobile instead of stretching to full width:


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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="w-full sm:w-auto overflow-x-auto pb-2 -mx-4 sm:mx-0 px-4 sm:px-0">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
          >
            <TabsList className="w-fit min-w-full sm:min-w-fit">
              <TabsTrigger value="all" className="px-4 sm:px-2 flex-shrink-0">
                All Videos ({videos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.PENDING_REVIEW} className="px-4 sm:px-2 flex-shrink-0">
                Pending ({pendingVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.REVIEWED} className="px-4 sm:px-2 flex-shrink-0">
                Reviewed ({reviewedVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.EPISODE_CREATED} className="px-4 sm:px-2 flex-shrink-0">
                Episodes ({episodeCreatedVideos.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0">
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

Refining the approach for cleaner mobile spacing:


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

        <div className="flex flex-col sm:flex-row gap-2 flex-wrap">
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
            <SelectTrigger className="w-full sm:w-[200px]">
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
            <SelectTrigger className="w-full sm:w-[180px]">
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
            <SelectTrigger className="w-full sm:w-[150px]">
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

          <div className="flex gap-2 ml-auto">
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
        <div className="bg-muted p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
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
          <div className="flex gap-2 flex-wrap">
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="w-full sm:w-auto overflow-x-auto pb-2">
          <Tabs
            value={selectedState === "all" ? "all" : selectedState}
            onValueChange={(value) =>
              setSelectedState(value as YouTubeVideoState | "all")
            }
            className="w-full sm:w-auto"
          >
            <TabsList className="w-fit sm:w-fit">
              <TabsTrigger value="all" className="px-4 sm:px-2 flex-shrink-0">
                All Videos ({videos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.PENDING_REVIEW} className="px-4 sm:px-2 flex-shrink-0">
                Pending ({pendingVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.REVIEWED} className="px-4 sm:px-2 flex-shrink-0">
                Reviewed ({reviewedVideos.length})
              </TabsTrigger>
              <TabsTrigger value={YouTubeVideoState.EPISODE_CREATED} className="px-4 sm:px-2 flex-shrink-0">
                Episodes ({episodeCreatedVideos.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        {selectionMode && (
          <div className="flex gap-2 flex-shrink-0">
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


## Changes Applied:

### 1. **Video List Component** (`video-list.tsx`):
   - Updated tabs container: removed full-width constraint on mobile, allowing horizontal scrolling
   - Added padding to each tab: `px-4 sm:px-2` (more padding on mobile, less on desktop)
   - Added `flex-shrink-0` to each tab to prevent compression
   - Made TabsList `w-fit` so it doesn't stretch to full width
   - Added `pb-2` for bottom padding to accommodate scrollbar

### 2. **Tabs Component** (`tabs.tsx`):
   - Changed `flex-1` to `sm:flex-1` on TabsTrigger
   - Tabs no longer stretch on mobile; they maintain natural width
   - On larger screens (sm+), tabs still stretch to fill available space

## Results:
- Tabs have proper padding on mobile (`px-4`)
- Tabs don't stretch on mobile, preventing cramped appearance
- Horizontal scrolling is available if tabs exceed screen width
- Tabs maintain proper spacing between elements
- On desktop, tabs behave as before with appropriate sizing

The tabs section should now display correctly on mobile with proper spacing and padding.

