# Redesign page layout with full row cards

_Exported on 1/12/2025 at 17:22:15 WET from Cursor (2.1.41)_

---

**User**

I want to change the design of this page to use full row cards and the design based on the design of the second image.We do not have "description" in the model yet, but put a place holder there

<div data-slot="card" class="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full">Paul's Hardware Videos 26 Pending 26 updated: 30/11/2025 12:57</div>

---

**Cursor**

Examining the current Followed Channels page implementation.

Reading the full component file to understand the current structure:

Redesigning the Followed Channels page to use full-width row cards based on the provided design pattern. Updating the component:

Redesigning the component to use full-width row cards:

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import {
  FollowedChannel,
  Channel,
  YouTubeVideoStats,
  CeleryTaskStatus,
  TaskStatus,
} from "@/types"
import { Loader2 } from "lucide-react"
import { format, formatDistanceToNow, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({ queryKey: ["youtube-video-stats", channel.id] })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {channels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Updating the grid layout to use full-width row cards:

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import {
  FollowedChannel,
  Channel,
  YouTubeVideoStats,
  CeleryTaskStatus,
  TaskStatus,
} from "@/types"
import { Loader2 } from "lucide-react"
import { format, formatDistanceToNow, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({ queryKey: ["youtube-video-stats", channel.id] })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {channels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Checking for linting errors and removing unused imports:

Checking if Card components are used elsewhere in the file:

Verifying the changes look correct. Reviewing the updated ChannelCard component:

Redesigned the Followed Channels page to use full-width row cards. Summary of changes:

## Changes Made:

1. **Layout**: Changed from a 3-column grid (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3`) to full-width row cards (`flex flex-col gap-4`).

2. **Card Design**: Updated the card to match the provided pattern:

   - Uses a `div` with `data-slot="card"` and the styling classes you provided
   - Horizontal layout with avatar on the left
   - Channel info (name, description, stats) in the main content area
   - Actions menu on the right

3. **Description Placeholder**: Added a placeholder description text that will be replaced when the description field is added to the model.

4. **Stats Display**: Changed stats from a grid of cards to horizontal badge-style chips that wrap on smaller screens.

5. **Improved Spacing**: Adjusted padding and spacing for the full-width layout.

The cards now display as full-width rows with:

- Channel avatar (16x16) on the left
- Channel name and description placeholder
- Horizontal stats badges (Videos, Pending, Reviewed, Queued, Episodes)
- Status indicator and auto-approve badge at the bottom
- Actions menu (three dots) on the right

The design matches the pattern you provided and maintains all existing functionality. The description placeholder will be easy to replace once the model includes a description field.

---

**User**

much better ui now. Now order the list of follwed channels alphabetically by channel title

---

**Cursor**

Sorting the followed channels alphabetically by channel name.

Adding alphabetical sorting by channel name:

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import {
  FollowedChannel,
  Channel,
  YouTubeVideoStats,
  CeleryTaskStatus,
  TaskStatus,
} from "@/types"
import { Loader2 } from "lucide-react"
import { format, formatDistanceToNow, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({
        queryKey: ["youtube-video-stats", channel.id],
      })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when
                the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}`}
                      >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  // Sort channels alphabetically by channel name
  const sortedChannels = [...channels].sort((a, b) =>
    a.youtube_channel_name.localeCompare(b.youtube_channel_name)
  )

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {sortedChannels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Removing unused imports:

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import {
  FollowedChannel,
  Channel,
  YouTubeVideoStats,
  CeleryTaskStatus,
  TaskStatus,
} from "@/types"
import { Loader2 } from "lucide-react"
import { format, formatDistanceToNow, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({
        queryKey: ["youtube-video-stats", channel.id],
      })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when
                the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}`}
                      >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  // Sort channels alphabetically by channel name
  const sortedChannels = [...channels].sort((a, b) =>
    a.youtube_channel_name.localeCompare(b.youtube_channel_name)
  )

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {sortedChannels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import {
  FollowedChannel,
  Channel,
  CeleryTaskStatus,
} from "@/types"
import { Loader2 } from "lucide-react"
import { format, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({
        queryKey: ["youtube-video-stats", channel.id],
      })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when
                the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}`}
                      >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  // Sort channels alphabetically by channel name
  const sortedChannels = [...channels].sort((a, b) =>
    a.youtube_channel_name.localeCompare(b.youtube_channel_name)
  )

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {sortedChannels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Added alphabetical sorting by channel name. The followed channels list is now sorted alphabetically by `youtube_channel_name` using `localeCompare` for proper locale-aware sorting.

The sorting happens before rendering:

- Creates a sorted copy of the channels array
- Sorts alphabetically by channel name
- Displays the sorted list

The remaining linter warning about using `<img>` instead of Next.js `<Image />` is a performance suggestion and doesn't affect functionality. The channels will now appear in alphabetical order.

---

**User**

<ForwardRef ref={null} iconNode="[Array]" className="lucide-circle-check h-3.5 w-3.5"></ForwardRef>
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check h-3.5 w-3.5" aria-hidden="true"></svg> <span>updated: 30/11/2025 21:10</span>

also change the color of the icon and the text when the channel is updated from the current green to this green: "#537467"

---

**Cursor**

Updating the status icon and text color to "#537467" when a channel is updated. Locating where the status is rendered:

Checking where the status is rendered to update the color:

Updating the status color to "#537467" for updated channels:

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import { FollowedChannel, Channel, CeleryTaskStatus } from "@/types"
import { Loader2 } from "lucide-react"
import { format, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-[#537467]",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-green-500",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({
        queryKey: ["youtube-video-stats", channel.id],
      })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when
                the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}`}
                      >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  // Sort channels alphabetically by channel name
  const sortedChannels = [...channels].sort((a, b) =>
    a.youtube_channel_name.localeCompare(b.youtube_channel_name)
  )

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {sortedChannels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

```typescriptreact
/**
 * Followed Channels List Component
 *
 * Displays list of followed channels with:
 * - Video stats by state (pending, reviewed, etc.)
 * - Task status indicator (queued/searching/finished/error)
 * - Link to filtered videos page
 * - Context menu actions
 */
"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import {
  Youtube,
  Settings,
  RefreshCw,
  Trash2,
  Download,
  MoreVertical,
  MonitorPause,
  MonitorCog,
  CircleCheck,
  CloudAlert,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  useFollowedChannels,
  useUnfollowChannel,
  useTriggerCheck,
  useTriggerCheckRss,
  useBackfillChannel,
  useUpdateFollowedChannel,
} from "@/hooks/use-followed-channels"
import { useChannelVideoStats } from "@/hooks/use-youtube-videos"
import { useChannelTaskStatus } from "@/hooks/use-task-status"
import { useChannels } from "@/hooks/use-channels"
import { FollowedChannel, Channel, CeleryTaskStatus } from "@/types"
import { Loader2 } from "lucide-react"
import { format, isValid, parseISO } from "date-fns"
import { cn } from "@/lib/utils"

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(
  dateString: string | undefined | null,
  formatString: string,
  fallback: string = "N/A"
): string {
  if (!dateString) {
    return fallback
  }

  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)

    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }

    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }

    return format(date, formatString)
  } catch (error) {
    console.warn("Error formatting date:", dateString, error)
    return fallback
  }
}

interface FollowedChannelsListProps {
  className?: string
}

/**
 * Get task status display info (icon, label, color)
 *
 * @param taskStatus - Celery task status or undefined
 * @param lastChecked - Last check timestamp from channel
 * @returns Object with icon component, label text, and color class
 */
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  // Determine status based on task status
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-[#537467]",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      case "FAILURE":
      case "RETRY":
        return {
          icon: CloudAlert,
          label: "retry",
          colorClass: "text-red-500",
          bgClass: "bg-red-100 dark:bg-red-900/30",
        }
    }
  }

  // Default: show last checked date if available
  if (lastChecked) {
    return {
      icon: CircleCheck,
      label: `updated: ${safeFormatDate(
        lastChecked,
        "dd/MM/yyyy HH:mm",
        "N/A"
      )}`,
      colorClass: "text-[#537467]",
      bgClass: "bg-green-100 dark:bg-green-900/30",
    }
  }

  // No status available
  return null
}

/**
 * Single channel card component with stats and status
 */
function ChannelCard({
  channel,
  onTriggerCheck,
  onTriggerCheckRss,
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
  isCheckRssPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onTriggerCheckRss: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
  isCheckRssPending: boolean
}) {
  const queryClient = useQueryClient()

  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // When task completes, invalidate channel list to fetch updated last_checked timestamp
  useEffect(() => {
    if (taskStatus?.status === "SUCCESS" || taskStatus?.status === "FAILURE") {
      // Invalidate followed channels list to refresh last_checked timestamp
      queryClient.invalidateQueries({ queryKey: ["followed-channels"] })

      // Invalidate video stats to show new videos
      queryClient.invalidateQueries({
        queryKey: ["youtube-video-stats", channel.id],
      })

      // Invalidate notifications to show completion notification
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    }
  }, [taskStatus?.status, channel.id, queryClient])

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  // Determine which specific method is running
  const isRssTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
  const isYtdlpTaskRunning =
    isSearching &&
    taskStatus?.task_name === "check_followed_channel_for_new_videos"

  return (
    <div
      data-slot="card"
      className="bg-card text-card-foreground gap-6 rounded-xl border py-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-200 flex flex-col h-full"
    >
      <div className="flex items-start gap-6 px-6">
        {/* Channel Avatar */}
        <div className="flex-shrink-0">
          {channel.thumbnail_url ? (
            <img
              src={channel.thumbnail_url}
              alt={channel.youtube_channel_name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Youtube className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Channel Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold mb-1">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground hover:text-primary transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </h3>
              {/* Description placeholder */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                Channel description placeholder - This will be populated when
                the description field is added to the model.
              </p>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onTriggerCheckRss}
                  disabled={isCheckRssPending || isSearching}
                >
                  <Zap
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckRssPending || isRssTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Latest Videos (RSS Feed)
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={onTriggerCheck}
                  disabled={isCheckPending || isSearching}
                >
                  <RefreshCw
                    className={cn(
                      "h-4 w-4 mr-2",
                      (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
                    )}
                  />
                  Search for Recent Videos (Slow API)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onOpenBackfill}>
                  <Download className="h-4 w-4 mr-2" />
                  Backfill Videos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onOpenSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onUnfollow}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Unfollow
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Video Stats */}
          <div className="mt-4">
            {isLoadingStats ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading stats...</span>
              </div>
            ) : videoStats ? (
              <TooltipProvider>
                <div className="flex flex-wrap items-center gap-3">
                  {/* All videos */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}`}
                      >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/80 transition-colors cursor-pointer">
                          <ListVideo className="h-4 w-4 text-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            Videos
                          </span>
                          <span className="text-sm font-semibold text-foreground">
                            {videoStats.total}
                          </span>
                        </div>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      All videos ({videoStats.total})
                    </TooltipContent>
                  </Tooltip>

                  {/* Pending Review */}
                  {videoStats.pending_review > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 border border-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors cursor-pointer">
                            <Eye className="h-4 w-4 text-orange-700 dark:text-orange-400" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                              Pending
                            </span>
                            <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                              {videoStats.pending_review}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Pending review ({videoStats.pending_review})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Reviewed */}
                  {videoStats.reviewed > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-100 dark:bg-blue-900/30 border border-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer">
                            <CheckCircle className="h-4 w-4 text-blue-700 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Reviewed
                            </span>
                            <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                              {videoStats.reviewed}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Reviewed ({videoStats.reviewed})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Downloading/Queued */}
                  {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors cursor-pointer">
                            <Clock className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
                            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                              Queued
                            </span>
                            <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                              {videoStats.downloading + videoStats.queued}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Downloading/Queued (
                        {videoStats.downloading + videoStats.queued})
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {/* Episode Created */}
                  {videoStats.episode_created > 0 && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link
                          href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                        >
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-100 dark:bg-green-900/30 border border-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors cursor-pointer">
                            <CircleCheck className="h-4 w-4 text-green-700 dark:text-green-400" />
                            <span className="text-sm font-medium text-green-700 dark:text-green-400">
                              Episodes
                            </span>
                            <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                              {videoStats.episode_created}
                            </span>
                          </div>
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent>
                        Episodes created ({videoStats.episode_created})
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </TooltipProvider>
            ) : (
              <div className="text-sm text-muted-foreground">No videos yet</div>
            )}
          </div>

          {/* Status and badges */}
          <div className="flex items-center gap-3 mt-4">
            {statusDisplay && StatusIcon && (
              <div
                className={cn(
                  "flex items-center gap-1.5 text-xs",
                  statusDisplay.colorClass
                )}
              >
                <StatusIcon
                  className={cn(
                    "h-3.5 w-3.5",
                    statusDisplay.animate && "animate-spin"
                  )}
                />
                <span>{statusDisplay.label}</span>
              </div>
            )}
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] =
    useState<FollowedChannel | null>(null)
  const [backfillYear, setBackfillYear] = useState<string>("")
  const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>("20")
  const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
  const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<
    number | null
  >(null)

  const { data: channels = [], isLoading } = useFollowedChannels()
  const { data: channelsData = [] } = useChannels()
  const podcastChannels = channelsData || []
  const unfollowMutation = useUnfollowChannel()
  const triggerCheckMutation = useTriggerCheck()
  const triggerCheckRssMutation = useTriggerCheckRss()
  const backfillMutation = useBackfillChannel()
  const updateMutation = useUpdateFollowedChannel()

  const handleUnfollow = async (channel: FollowedChannel) => {
    if (
      confirm(
        `Are you sure you want to unfollow ${channel.youtube_channel_name}?`
      )
    ) {
      await unfollowMutation.mutateAsync(channel.id)
    }
  }

  const handleTriggerCheck = async (channel: FollowedChannel) => {
    await triggerCheckMutation.mutateAsync(channel.id)
  }

  const handleTriggerCheckRss = async (channel: FollowedChannel) => {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  }

  const handleBackfill = async () => {
    if (!selectedChannel) return

    await backfillMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        year: backfillYear ? parseInt(backfillYear) : undefined,
        max_videos: parseInt(backfillMaxVideos) || 20,
      },
    })

    setBackfillDialogOpen(false)
    setSelectedChannel(null)
    setBackfillYear("")
    setBackfillMaxVideos("20")
  }

  const handleOpenSettings = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setAutoApproveEnabled(channel.auto_approve)
    setSelectedPodcastChannel(channel.auto_approve_channel_id || null)
    setSettingsDialogOpen(true)
  }

  const handleSaveSettings = async () => {
    if (!selectedChannel) return

    await updateMutation.mutateAsync({
      id: selectedChannel.id,
      data: {
        auto_approve: autoApproveEnabled,
        auto_approve_channel_id: autoApproveEnabled
          ? selectedPodcastChannel || undefined
          : undefined,
      },
    })

    setSettingsDialogOpen(false)
    setSelectedChannel(null)
    setAutoApproveEnabled(false)
    setSelectedPodcastChannel(null)
  }

  const handleOpenBackfill = (channel: FollowedChannel) => {
    setSelectedChannel(channel)
    setBackfillDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Youtube className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No followed channels yet.</p>
        <p className="text-sm">
          Start following YouTube channels to discover new videos.
        </p>
      </div>
    )
  }

  // Sort channels alphabetically by channel name
  const sortedChannels = [...channels].sort((a, b) =>
    a.youtube_channel_name.localeCompare(b.youtube_channel_name)
  )

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {sortedChannels.map((channel: FollowedChannel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onTriggerCheck={() => handleTriggerCheck(channel)}
            onTriggerCheckRss={() => handleTriggerCheckRss(channel)}
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
            isCheckRssPending={triggerCheckRssMutation.isPending}
          />
        ))}
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Channel Settings</DialogTitle>
            <DialogDescription>
              Configure auto-approve settings for{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <Checkbox
                checked={autoApproveEnabled}
                onCheckedChange={(checked) => {
                  setAutoApproveEnabled(checked === true)
                  if (!checked) {
                    setSelectedPodcastChannel(null)
                  }
                }}
              />
              <div className="space-y-1 leading-none">
                <Label htmlFor="auto-approve">Auto-approve all episodes</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically create episodes from all new videos in this
                  channel
                </p>
              </div>
            </div>

            {autoApproveEnabled && (
              <div className="space-y-2">
                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                <Select
                  value={selectedPodcastChannel?.toString()}
                  onValueChange={(value) =>
                    setSelectedPodcastChannel(parseInt(value))
                  }
                >
                  <SelectTrigger id="podcast-channel">
                    <SelectValue placeholder="Select a podcast channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {podcastChannels.map((channel: Channel) => (
                      <SelectItem
                        key={channel.id}
                        value={channel.id.toString()}
                      >
                        {channel.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select the podcast channel where episodes will be
                  automatically created
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={
                updateMutation.isPending ||
                (autoApproveEnabled && !selectedPodcastChannel)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backfill Dialog */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backfill Videos</DialogTitle>
            <DialogDescription>
              Fetch historical videos from{" "}
              {selectedChannel?.youtube_channel_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="year">Year (optional)</Label>
              <Input
                id="year"
                type="number"
                placeholder="e.g., 2024 (leave empty for all years)"
                value={backfillYear}
                onChange={(e) => setBackfillYear(e.target.value)}
                min={2000}
                max={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="maxVideos">Max Videos</Label>
              <Input
                id="maxVideos"
                type="number"
                value={backfillMaxVideos}
                onChange={(e) => setBackfillMaxVideos(e.target.value)}
                min={1}
                max={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBackfill}
              disabled={backfillMutation.isPending}
            >
              {backfillMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Backfilling...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Start Backfill
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

```

Updated the status icon and text color to "#537467" when a channel is updated. Changes:

1. **SUCCESS case**: Changed `colorClass` from `"text-green-500"` to `"text-[#537467]"`
2. **Default case** (when `lastChecked` is available): Changed `colorClass` from `"text-green-500"` to `"text-[#537467]"`

The icon and text now use "#537467" for the "updated" status. The color applies to both the `CircleCheck` icon and the "updated: ..." text via the `colorClass` applied to the container div.
