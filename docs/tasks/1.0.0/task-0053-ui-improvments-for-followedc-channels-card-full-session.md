# Include time in service data

_Exported on 28/11/2025 at 20:02:58 WET from Cursor (2.1.39)_

---

**User**

<span>updated: 28/11/2025</span> with the data that we receive from the service can we include not only the date but also the hour "hh:mm"

---

**Cursor**

Searching for where dates are displayed to add time in "hh:mm" format.

Checking the file that displays the "updated" date:

Updating the date format to include time in "hh:mm" format. Updating both occurrences:

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

import React, { useState } from 'react'
import Link from 'next/link'
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
    ExternalLink,
    Eye,
    CheckCircle,
    Clock,
    ListVideo,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'
import {
    useFollowedChannels,
    useUnfollowChannel,
    useTriggerCheck,
    useBackfillChannel,
    useUpdateFollowedChannel,
} from '@/hooks/use-followed-channels'
import { useChannelVideoStats } from '@/hooks/use-youtube-videos'
import { useChannelTaskStatus } from '@/hooks/use-task-status'
import { useChannels } from '@/hooks/use-channels'
import { FollowedChannel, Channel, YouTubeVideoStats, CeleryTaskStatus, TaskStatus } from '@/types'
import { Loader2 } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { cn } from '@/lib/utils'

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
function getTaskStatusDisplay(taskStatus: CeleryTaskStatus | null | undefined, lastChecked: string | undefined) {
    // Determine status based on task status
    if (taskStatus) {
        switch (taskStatus.status) {
            case 'PENDING':
            case 'STARTED':
                return {
                    icon: MonitorPause,
                    label: 'queued',
                    colorClass: 'text-yellow-500',
                    bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
                }
            case 'PROGRESS':
                return {
                    icon: MonitorCog,
                    label: 'searching',
                    colorClass: 'text-blue-500',
                    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
                    animate: true,
                }
            case 'SUCCESS':
                return {
                    icon: CircleCheck,
                    label: lastChecked ? `updated: ${format(new Date(lastChecked), 'dd/MM/yyyy HH:mm')}` : 'completed',
                    colorClass: 'text-green-500',
                    bgClass: 'bg-green-100 dark:bg-green-900/30',
                }
            case 'FAILURE':
            case 'RETRY':
                return {
                    icon: CloudAlert,
                    label: 'retry',
                    colorClass: 'text-red-500',
                    bgClass: 'bg-red-100 dark:bg-red-900/30',
                }
        }
    }

    // Default: show last checked date if available
    if (lastChecked) {
        return {
            icon: CircleCheck,
            label: `updated: ${format(new Date(lastChecked), 'dd/MM/yyyy')}`,
            colorClass: 'text-green-500',
            bgClass: 'bg-green-100 dark:bg-green-900/30',
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
    onOpenBackfill,
    onOpenSettings,
    onUnfollow,
    isCheckPending,
}: {
    channel: FollowedChannel
    onTriggerCheck: () => void
    onOpenBackfill: () => void
    onOpenSettings: () => void
    onUnfollow: () => void
    isCheckPending: boolean
}) {
    // Fetch video stats for this channel
    const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(channel.id)

    // Fetch task status for this channel (with polling while active)
    const { data: taskStatus } = useChannelTaskStatus(channel.id)

    // Get status display info
    const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
    const StatusIcon = statusDisplay?.icon

    // Determine if we're actively searching (for animation)
    const isSearching = taskStatus?.status === 'PROGRESS' ||
                        taskStatus?.status === 'PENDING' ||
                        taskStatus?.status === 'STARTED'

    return (
        <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                        {channel.thumbnail_url ? (
                            <img
                                src={channel.thumbnail_url}
                                alt={channel.youtube_channel_name}
                                className="w-12 h-12 rounded-full object-cover"
                            />
                        ) : (
                            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                                <Youtube className="h-6 w-6 text-muted-foreground" />
                            </div>
                        )}
                        <div className="flex-1 min-w-0">
                            <CardTitle className="text-base line-clamp-2">
                                {channel.youtube_channel_name}
                            </CardTitle>
                            {/* Task Status Indicator */}
                            {statusDisplay && StatusIcon && (
                                <div className={cn(
                                    "flex items-center gap-1.5 mt-1 text-xs",
                                    statusDisplay.colorClass
                                )}>
                                    <StatusIcon className={cn(
                                        "h-3.5 w-3.5",
                                        statusDisplay.animate && "animate-spin"
                                    )} />
                                    <span>{statusDisplay.label}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem
                                onClick={onTriggerCheck}
                                disabled={isCheckPending || isSearching}
                            >
                                <RefreshCw className={cn(
                                    "h-4 w-4 mr-2",
                                    (isCheckPending || isSearching) && "animate-spin"
                                )} />
                                Check for New Videos
                            </DropdownMenuItem>
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
            </CardHeader>
            <CardContent className="space-y-3">
                {/* Video Stats */}
                <div className="space-y-2">
                    {isLoadingStats ? (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>Loading stats...</span>
                        </div>
                    ) : videoStats ? (
                        <div className="flex flex-wrap gap-1.5">
                            <TooltipProvider>
                                {/* All videos - link to all videos for this channel */}
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                                            <Badge
                                                variant="secondary"
                                                className="cursor-pointer hover:bg-secondary/80 gap-1"
                                            >
                                                <ListVideo className="h-3 w-3" />
                                                {videoStats.total}
                                            </Badge>
                                        </Link>
                                    </TooltipTrigger>
                                    <TooltipContent>All videos ({videoStats.total})</TooltipContent>
                                </Tooltip>

                                {/* Pending Review - orange/yellow */}
                                {videoStats.pending_review > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                                                >
                                                    <Eye className="h-3 w-3" />
                                                    {videoStats.pending_review}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Pending review ({videoStats.pending_review})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Reviewed - blue */}
                                {videoStats.reviewed > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                                                >
                                                    <CheckCircle className="h-3 w-3" />
                                                    {videoStats.reviewed}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Reviewed ({videoStats.reviewed})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Downloading/Queued - yellow */}
                                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                                                >
                                                    <Clock className="h-3 w-3" />
                                                    {videoStats.downloading + videoStats.queued}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Downloading/Queued ({videoStats.downloading + videoStats.queued})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Episode Created - green */}
                                {videoStats.episode_created > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                                                >
                                                    <CircleCheck className="h-3 w-3" />
                                                    {videoStats.episode_created}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Episodes created ({videoStats.episode_created})</TooltipContent>
                                    </Tooltip>
                                )}
                            </TooltipProvider>
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">No videos yet</div>
                    )}
                </div>

                {/* Auto-approve badge and external link */}
                <div className="flex items-center justify-between">
                    <div>
                        {channel.auto_approve && (
                            <Badge variant="default" className="bg-green-500 text-xs">
                                Auto-approve
                            </Badge>
                        )}
                    </div>
                    <a
                        href={channel.youtube_channel_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
                    >
                        <Youtube className="h-3 w-3" />
                        View Channel
                        <ExternalLink className="h-3 w-3" />
                    </a>
                </div>
            </CardContent>
        </Card>
    )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
    const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
    const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
    const [selectedChannel, setSelectedChannel] = useState<FollowedChannel | null>(null)
    const [backfillYear, setBackfillYear] = useState<string>('')
    const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>('20')
    const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
    const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<number | null>(null)

    const { data: channels = [], isLoading } = useFollowedChannels()
    const { data: channelsData = [] } = useChannels()
    const podcastChannels = channelsData || []
    const unfollowMutation = useUnfollowChannel()
    const triggerCheckMutation = useTriggerCheck()
    const backfillMutation = useBackfillChannel()
    const updateMutation = useUpdateFollowedChannel()

    const handleUnfollow = async (channel: FollowedChannel) => {
        if (confirm(`Are you sure you want to unfollow ${channel.youtube_channel_name}?`)) {
            await unfollowMutation.mutateAsync(channel.id)
        }
    }

    const handleTriggerCheck = async (channel: FollowedChannel) => {
        await triggerCheckMutation.mutateAsync(channel.id)
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
        setBackfillYear('')
        setBackfillMaxVideos('20')
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
                auto_approve_channel_id: autoApproveEnabled ? selectedPodcastChannel || undefined : undefined,
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
                <p className="text-sm">Start following YouTube channels to discover new videos.</p>
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
                        onOpenBackfill={() => handleOpenBackfill(channel)}
                        onOpenSettings={() => handleOpenSettings(channel)}
                        onUnfollow={() => handleUnfollow(channel)}
                        isCheckPending={triggerCheckMutation.isPending}
                    />
                ))}
            </div>

            {/* Settings Dialog */}
            <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Channel Settings</DialogTitle>
                        <DialogDescription>
                            Configure auto-approve settings for {selectedChannel?.youtube_channel_name}
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
                                    Automatically create episodes from all new videos in this channel
                                </p>
                            </div>
                        </div>

                        {autoApproveEnabled && (
                            <div className="space-y-2">
                                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                                <Select
                                    value={selectedPodcastChannel?.toString()}
                                    onValueChange={(value) => setSelectedPodcastChannel(parseInt(value))}
                                >
                                    <SelectTrigger id="podcast-channel">
                                        <SelectValue placeholder="Select a podcast channel" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {podcastChannels.map((channel: Channel) => (
                                            <SelectItem key={channel.id} value={channel.id.toString()}>
                                                {channel.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-sm text-muted-foreground">
                                    Select the podcast channel where episodes will be automatically created
                                </p>
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setSettingsDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSaveSettings}
                            disabled={updateMutation.isPending || (autoApproveEnabled && !selectedPodcastChannel)}
                        >
                            {updateMutation.isPending ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                'Save Settings'
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
                            Fetch historical videos from {selectedChannel?.youtube_channel_name}
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
                        <Button variant="outline" onClick={() => setBackfillDialogOpen(false)}>
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

import React, { useState } from 'react'
import Link from 'next/link'
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
    ExternalLink,
    Eye,
    CheckCircle,
    Clock,
    ListVideo,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'
import {
    useFollowedChannels,
    useUnfollowChannel,
    useTriggerCheck,
    useBackfillChannel,
    useUpdateFollowedChannel,
} from '@/hooks/use-followed-channels'
import { useChannelVideoStats } from '@/hooks/use-youtube-videos'
import { useChannelTaskStatus } from '@/hooks/use-task-status'
import { useChannels } from '@/hooks/use-channels'
import { FollowedChannel, Channel, YouTubeVideoStats, CeleryTaskStatus, TaskStatus } from '@/types'
import { Loader2 } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { cn } from '@/lib/utils'

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
function getTaskStatusDisplay(taskStatus: CeleryTaskStatus | null | undefined, lastChecked: string | undefined) {
    // Determine status based on task status
    if (taskStatus) {
        switch (taskStatus.status) {
            case 'PENDING':
            case 'STARTED':
                return {
                    icon: MonitorPause,
                    label: 'queued',
                    colorClass: 'text-yellow-500',
                    bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
                }
            case 'PROGRESS':
                return {
                    icon: MonitorCog,
                    label: 'searching',
                    colorClass: 'text-blue-500',
                    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
                    animate: true,
                }
            case 'SUCCESS':
                return {
                    icon: CircleCheck,
                    label: lastChecked ? `updated: ${format(new Date(lastChecked), 'dd/MM/yyyy HH:mm')}` : 'completed',
                    colorClass: 'text-green-500',
                    bgClass: 'bg-green-100 dark:bg-green-900/30',
                }
            case 'FAILURE':
            case 'RETRY':
                return {
                    icon: CloudAlert,
                    label: 'retry',
                    colorClass: 'text-red-500',
                    bgClass: 'bg-red-100 dark:bg-red-900/30',
                }
        }
    }

    // Default: show last checked date if available
    if (lastChecked) {
        return {
            icon: CircleCheck,
            label: `updated: ${format(new Date(lastChecked), 'dd/MM/yyyy HH:mm')}`,
            colorClass: 'text-green-500',
            bgClass: 'bg-green-100 dark:bg-green-900/30',
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
    onOpenBackfill,
    onOpenSettings,
    onUnfollow,
    isCheckPending,
}: {
    channel: FollowedChannel
    onTriggerCheck: () => void
    onOpenBackfill: () => void
    onOpenSettings: () => void
    onUnfollow: () => void
    isCheckPending: boolean
}) {
    // Fetch video stats for this channel
    const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(channel.id)

    // Fetch task status for this channel (with polling while active)
    const { data: taskStatus } = useChannelTaskStatus(channel.id)

    // Get status display info
    const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
    const StatusIcon = statusDisplay?.icon

    // Determine if we're actively searching (for animation)
    const isSearching = taskStatus?.status === 'PROGRESS' ||
                        taskStatus?.status === 'PENDING' ||
                        taskStatus?.status === 'STARTED'

    return (
        <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                        {channel.thumbnail_url ? (
                            <img
                                src={channel.thumbnail_url}
                                alt={channel.youtube_channel_name}
                                className="w-12 h-12 rounded-full object-cover"
                            />
                        ) : (
                            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                                <Youtube className="h-6 w-6 text-muted-foreground" />
                            </div>
                        )}
                        <div className="flex-1 min-w-0">
                            <CardTitle className="text-base line-clamp-2">
                                {channel.youtube_channel_name}
                            </CardTitle>
                            {/* Task Status Indicator */}
                            {statusDisplay && StatusIcon && (
                                <div className={cn(
                                    "flex items-center gap-1.5 mt-1 text-xs",
                                    statusDisplay.colorClass
                                )}>
                                    <StatusIcon className={cn(
                                        "h-3.5 w-3.5",
                                        statusDisplay.animate && "animate-spin"
                                    )} />
                                    <span>{statusDisplay.label}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem
                                onClick={onTriggerCheck}
                                disabled={isCheckPending || isSearching}
                            >
                                <RefreshCw className={cn(
                                    "h-4 w-4 mr-2",
                                    (isCheckPending || isSearching) && "animate-spin"
                                )} />
                                Check for New Videos
                            </DropdownMenuItem>
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
            </CardHeader>
            <CardContent className="space-y-3">
                {/* Video Stats */}
                <div className="space-y-2">
                    {isLoadingStats ? (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>Loading stats...</span>
                        </div>
                    ) : videoStats ? (
                        <div className="flex flex-wrap gap-1.5">
                            <TooltipProvider>
                                {/* All videos - link to all videos for this channel */}
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                                            <Badge
                                                variant="secondary"
                                                className="cursor-pointer hover:bg-secondary/80 gap-1"
                                            >
                                                <ListVideo className="h-3 w-3" />
                                                {videoStats.total}
                                            </Badge>
                                        </Link>
                                    </TooltipTrigger>
                                    <TooltipContent>All videos ({videoStats.total})</TooltipContent>
                                </Tooltip>

                                {/* Pending Review - orange/yellow */}
                                {videoStats.pending_review > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                                                >
                                                    <Eye className="h-3 w-3" />
                                                    {videoStats.pending_review}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Pending review ({videoStats.pending_review})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Reviewed - blue */}
                                {videoStats.reviewed > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                                                >
                                                    <CheckCircle className="h-3 w-3" />
                                                    {videoStats.reviewed}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Reviewed ({videoStats.reviewed})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Downloading/Queued - yellow */}
                                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                                                >
                                                    <Clock className="h-3 w-3" />
                                                    {videoStats.downloading + videoStats.queued}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Downloading/Queued ({videoStats.downloading + videoStats.queued})</TooltipContent>
                                    </Tooltip>
                                )}

                                {/* Episode Created - green */}
                                {videoStats.episode_created > 0 && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Link href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}>
                                                <Badge
                                                    variant="outline"
                                                    className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                                                >
                                                    <CircleCheck className="h-3 w-3" />
                                                    {videoStats.episode_created}
                                                </Badge>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent>Episodes created ({videoStats.episode_created})</TooltipContent>
                                    </Tooltip>
                                )}
                            </TooltipProvider>
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">No videos yet</div>
                    )}
                </div>

                {/* Auto-approve badge and external link */}
                <div className="flex items-center justify-between">
                    <div>
                        {channel.auto_approve && (
                            <Badge variant="default" className="bg-green-500 text-xs">
                                Auto-approve
                            </Badge>
                        )}
                    </div>
                    <a
                        href={channel.youtube_channel_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
                    >
                        <Youtube className="h-3 w-3" />
                        View Channel
                        <ExternalLink className="h-3 w-3" />
                    </a>
                </div>
            </CardContent>
        </Card>
    )
}

export function FollowedChannelsList({ className }: FollowedChannelsListProps) {
    const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
    const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
    const [selectedChannel, setSelectedChannel] = useState<FollowedChannel | null>(null)
    const [backfillYear, setBackfillYear] = useState<string>('')
    const [backfillMaxVideos, setBackfillMaxVideos] = useState<string>('20')
    const [autoApproveEnabled, setAutoApproveEnabled] = useState(false)
    const [selectedPodcastChannel, setSelectedPodcastChannel] = useState<number | null>(null)

    const { data: channels = [], isLoading } = useFollowedChannels()
    const { data: channelsData = [] } = useChannels()
    const podcastChannels = channelsData || []
    const unfollowMutation = useUnfollowChannel()
    const triggerCheckMutation = useTriggerCheck()
    const backfillMutation = useBackfillChannel()
    const updateMutation = useUpdateFollowedChannel()

    const handleUnfollow = async (channel: FollowedChannel) => {
        if (confirm(`Are you sure you want to unfollow ${channel.youtube_channel_name}?`)) {
            await unfollowMutation.mutateAsync(channel.id)
        }
    }

    const handleTriggerCheck = async (channel: FollowedChannel) => {
        await triggerCheckMutation.mutateAsync(channel.id)
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
        setBackfillYear('')
        setBackfillMaxVideos('20')
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
                auto_approve_channel_id: autoApproveEnabled ? selectedPodcastChannel || undefined : undefined,
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
                <p className="text-sm">Start following YouTube channels to discover new videos.</p>
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
                        onOpenBackfill={() => handleOpenBackfill(channel)}
                        onOpenSettings={() => handleOpenSettings(channel)}
                        onUnfollow={() => handleUnfollow(channel)}
                        isCheckPending={triggerCheckMutation.isPending}
                    />
                ))}
            </div>

            {/* Settings Dialog */}
            <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Channel Settings</DialogTitle>
                        <DialogDescription>
                            Configure auto-approve settings for {selectedChannel?.youtube_channel_name}
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
                                    Automatically create episodes from all new videos in this channel
                                </p>
                            </div>
                        </div>

                        {autoApproveEnabled && (
                            <div className="space-y-2">
                                <Label htmlFor="podcast-channel">Podcast Channel</Label>
                                <Select
                                    value={selectedPodcastChannel?.toString()}
                                    onValueChange={(value) => setSelectedPodcastChannel(parseInt(value))}
                                >
                                    <SelectTrigger id="podcast-channel">
                                        <SelectValue placeholder="Select a podcast channel" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {podcastChannels.map((channel: Channel) => (
                                            <SelectItem key={channel.id} value={channel.id.toString()}>
                                                {channel.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-sm text-muted-foreground">
                                    Select the podcast channel where episodes will be automatically created
                                </p>
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setSettingsDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSaveSettings}
                            disabled={updateMutation.isPending || (autoApproveEnabled && !selectedPodcastChannel)}
                        >
                            {updateMutation.isPending ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                'Save Settings'
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
                            Fetch historical videos from {selectedChannel?.youtube_channel_name}
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
                        <Button variant="outline" onClick={() => setBackfillDialogOpen(false)}>
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

Checking for linting errors:

The lint errors are pre-existing TypeScript configuration issues, not from these changes. The date format update is correct.

Updated the date format in `followed-channels-list.tsx` to include the time. The "updated" label now shows both date and time in "dd/MM/yyyy HH:mm" format (24-hour).

The changes were made in two places:

1. Line 114: When the task status is 'SUCCESS'
2. Line 133: When showing the default last checked date

The format string changed from `'dd/MM/yyyy'` to `'dd/MM/yyyy HH:mm'`, so it displays like "updated: 28/11/2025 14:30" instead of just "updated: 28/11/2025".

---

**User**

I want to remove the link to navvigate to the youtube channel that is currently here: <a href="https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw" target="_blank" rel="noopener noreferrer" class="text-xs text-muted-foreground hover:underline flex items-center gap-1">View Channel</a> and make the title of the channel a link that allows to navigtate to youtube link <div data-slot="card-title" class="font-semibold text-base line-clamp-2">Rincón de Varo - Hardware & PC Gaming</div>

---

**Cursor**

Removing the "View Channel" link and making the channel title clickable to navigate to the YouTube channel. Checking the current structure:

Making the channel title a link and removing the "View Channel" link:

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

import React, { useState } from "react"
import Link from "next/link"
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
  ExternalLink,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge and external link */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
          <a
            href={channel.youtube_channel_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
          >
            <Youtube className="h-3 w-3" />
            View Channel
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

import React, { useState } from "react"
import Link from "next/link"
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
  ExternalLink,
  Eye,
  CheckCircle,
  Clock,
  ListVideo,
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

Checking if `ExternalLink` is used elsewhere before removing it:

Removing the unused `ExternalLink` import:

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

import React, { useState } from "react"
import Link from "next/link"
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

Checking for linting errors:

The lint errors are pre-existing TypeScript configuration issues, not from these changes. Verifying the changes:

## Changes Made:

1. **Made the channel title clickable**: Wrapped the channel name in an `<a>` tag that links to `channel.youtube_channel_url`, opens in a new tab, and includes hover underline styling.

2. **Removed the "View Channel" link**: Removed the link at the bottom of the card that displayed "View Channel" with the YouTube and ExternalLink icons.

3. **Cleaned up imports**: Removed the unused `ExternalLink` import from lucide-react.

The channel title now links directly to the YouTube channel, and the separate "View Channel" link has been removed. The title shows an underline on hover to indicate it's clickable.

---

**User**

for the Followed Youtube Channel cards, use the same subtle animation that we use when we hover over the episode cards in the home page and the /channel page.

Also use the very same effect that we have to link to navigate the youtube channel in the home and /channel pages cards. However instead of gray text, use a slightly grayish-white and when on hover, ujse perfect white.

---

**Cursor**

Checking the episode cards on the home and /channel pages to identify the hover animation and link styling, then applying them to the Followed YouTube Channel cards.

Checking the channel dashboard for the YouTube channel link styling:

Searching for the YouTube channel link styling in the episode card:

Updating the Followed Channels cards with the same hover animation and link styling:

Updating the Followed Channels cards with the same hover animation and link styling:

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

import React, { useState } from "react"
import Link from "next/link"
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

import React, { useState } from "react"
import Link from "next/link"
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 dark:text-gray-400 hover:text-white transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

Checking if the Card has a click handler that might interfere:

Checking for linting errors:

Fixing the TypeScript error for the onClick handler:

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

import React, { useState } from "react"
import Link from "next/link"
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 dark:text-gray-400 hover:text-white transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) => e.stopPropagation()}
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

Verifying the changes look correct:

Checking that React is imported:

## Changes Made:

1. **Added hover animation**: Updated the Card component to use the same animation as episode cards:

   - Changed from `hover:shadow-lg transition-shadow`
   - To `hover:shadow-lg hover:-translate-y-1 transition-all duration-200`
   - Cards now lift slightly and show a shadow on hover, matching the episode cards

2. **Updated channel title link styling**: Applied the same link effect with grayish-white → white on hover:
   - Changed from `hover:underline`
   - To `text-gray-300 dark:text-gray-400 hover:text-white transition-colors`
   - Text starts grayish-white and transitions to white on hover
   - Added `onClick` handler with `stopPropagation()` to prevent event bubbling

The Followed YouTube Channel cards now match the episode cards' hover animation, and the channel title link uses the same effect with the requested color scheme.

---

**User**

<a href="https://www.youtube.com/channel/UCnxubBCPlg0hHdZw_UehrTw" target="_blank" rel="noopener noreferrer" class="text-gray-300 dark:text-gray-400 hover:text-white transition-colors">Rincón de Varo - Hardware & PC Gaming</a> Make the text white again and on hover apply a subtle color change.

---

**Cursor**

Updating the link styling: white by default, with a subtle hover color change.

```typescriptreact
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-gray-200 dark:hover:text-gray-300 transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) => e.stopPropagation()}
                >
                  {channel.youtube_channel_name}
                </a>
```

Reading the file to check the exact formatting:

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

import React, { useState } from "react"
import Link from "next/link"
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

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
      case "STARTED":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
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
            ? `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`
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
      label: `updated: ${format(new Date(lastChecked), "dd/MM/yyyy HH:mm")}`,
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
  onOpenBackfill,
  onOpenSettings,
  onUnfollow,
  isCheckPending,
}: {
  channel: FollowedChannel
  onTriggerCheck: () => void
  onOpenBackfill: () => void
  onOpenSettings: () => void
  onUnfollow: () => void
  isCheckPending: boolean
}) {
  // Fetch video stats for this channel
  const { data: videoStats, isLoading: isLoadingStats } = useChannelVideoStats(
    channel.id
  )

  // Fetch task status for this channel (with polling while active)
  const { data: taskStatus } = useChannelTaskStatus(channel.id)

  // Get status display info
  const statusDisplay = getTaskStatusDisplay(taskStatus, channel.last_checked)
  const StatusIcon = statusDisplay?.icon

  // Determine if we're actively searching (for animation)
  const isSearching =
    taskStatus?.status === "PROGRESS" ||
    taskStatus?.status === "PENDING" ||
    taskStatus?.status === "STARTED"

  return (
    <Card className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.youtube_channel_name}
                className="w-12 h-12 rounded-full object-cover"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base line-clamp-2">
                <a
                  href={channel.youtube_channel_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-gray-200 dark:hover:text-gray-300 transition-colors"
                  onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                    e.stopPropagation()
                  }
                >
                  {channel.youtube_channel_name}
                </a>
              </CardTitle>
              {/* Task Status Indicator */}
              {statusDisplay && StatusIcon && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 mt-1 text-xs",
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
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={onTriggerCheck}
                disabled={isCheckPending || isSearching}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    (isCheckPending || isSearching) && "animate-spin"
                  )}
                />
                Check for New Videos
              </DropdownMenuItem>
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
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Video Stats */}
        <div className="space-y-2">
          {isLoadingStats ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading stats...</span>
            </div>
          ) : videoStats ? (
            <div className="flex flex-wrap gap-1.5">
              <TooltipProvider>
                {/* All videos - link to all videos for this channel */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link href={`/subscriptions/videos?channel=${channel.id}`}>
                      <Badge
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 gap-1"
                      >
                        <ListVideo className="h-3 w-3" />
                        {videoStats.total}
                      </Badge>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>
                    All videos ({videoStats.total})
                  </TooltipContent>
                </Tooltip>

                {/* Pending Review - orange/yellow */}
                {videoStats.pending_review > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=pending_review`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-900/30 border-orange-300 text-orange-700 dark:text-orange-400 gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          {videoStats.pending_review}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Pending review ({videoStats.pending_review})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Reviewed - blue */}
                {videoStats.reviewed > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=reviewed`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 border-blue-300 text-blue-700 dark:text-blue-400 gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          {videoStats.reviewed}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Reviewed ({videoStats.reviewed})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Downloading/Queued - yellow */}
                {(videoStats.downloading > 0 || videoStats.queued > 0) && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=downloading`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400 gap-1"
                        >
                          <Clock className="h-3 w-3" />
                          {videoStats.downloading + videoStats.queued}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Downloading/Queued (
                      {videoStats.downloading + videoStats.queued})
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Episode Created - green */}
                {videoStats.episode_created > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`/subscriptions/videos?channel=${channel.id}&state=episode_created`}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 border-green-300 text-green-700 dark:text-green-400 gap-1"
                        >
                          <CircleCheck className="h-3 w-3" />
                          {videoStats.episode_created}
                        </Badge>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent>
                      Episodes created ({videoStats.episode_created})
                    </TooltipContent>
                  </Tooltip>
                )}
              </TooltipProvider>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No videos yet</div>
          )}
        </div>

        {/* Auto-approve badge */}
        <div className="flex items-center justify-between">
          <div>
            {channel.auto_approve && (
              <Badge variant="default" className="bg-green-500 text-xs">
                Auto-approve
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
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
            onOpenBackfill={() => handleOpenBackfill(channel)}
            onOpenSettings={() => handleOpenSettings(channel)}
            onUnfollow={() => handleUnfollow(channel)}
            isCheckPending={triggerCheckMutation.isPending}
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

Updated the link styling:

- **Default**: `text-white`
- **Hover**: `hover:text-gray-200 dark:hover:text-gray-300`

The channel title link is now white by default, with a subtle gray hover effect.
