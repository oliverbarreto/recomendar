/**
 * YouTube Video Card Component
 * 
 * Displays a YouTube video card for the subscriptions page
 */
"use client"

import React from 'react'
import {
    Play,
    ExternalLink,
    CheckCircle2,
    XCircle,
    Loader2,
    Clock,
    Eye,
    MoreVertical,
    Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { YouTubeVideo, YouTubeVideoState } from '@/types'
import { formatDistanceToNow } from 'date-fns'

interface YouTubeVideoCardProps {
    video: YouTubeVideo
    onReview?: (video: YouTubeVideo) => void
    onDiscard?: (video: YouTubeVideo) => void
    onCreateEpisode?: (video: YouTubeVideo) => void
    onViewYouTube?: (video: YouTubeVideo) => void
    selectionMode?: boolean
    isSelected?: boolean
    onToggleSelection?: (videoId: number) => void
    className?: string
}

const getStateBadge = (state: YouTubeVideoState) => {
    switch (state) {
        case YouTubeVideoState.PENDING_REVIEW:
            return (
                <Badge variant="default" className="bg-yellow-500 hover:bg-yellow-600">
                    <Clock className="h-3 w-3 mr-1" />
                    Pending Review
                </Badge>
            )
        case YouTubeVideoState.REVIEWED:
            return (
                <Badge variant="secondary">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Reviewed
                </Badge>
            )
        case YouTubeVideoState.QUEUED:
            return (
                <Badge variant="default" className="bg-blue-500 hover:bg-blue-600">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Queued
                </Badge>
            )
        case YouTubeVideoState.DOWNLOADING:
            return (
                <Badge variant="default" className="bg-blue-500 hover:bg-blue-600">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Downloading
                </Badge>
            )
        case YouTubeVideoState.EPISODE_CREATED:
            return (
                <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Episode Created
                </Badge>
            )
        case YouTubeVideoState.DISCARDED:
            return (
                <Badge variant="outline">
                    <XCircle className="h-3 w-3 mr-1" />
                    Discarded
                </Badge>
            )
        default:
            return null
    }
}

const formatDuration = (seconds?: number): string => {
    if (!seconds) return ''
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export function YouTubeVideoCard({
    video,
    onReview,
    onDiscard,
    onCreateEpisode,
    onViewYouTube,
    selectionMode = false,
    isSelected = false,
    onToggleSelection,
    className,
}: YouTubeVideoCardProps) {
    const canReview = video.state === YouTubeVideoState.PENDING_REVIEW
    const canDiscard = video.state === YouTubeVideoState.PENDING_REVIEW || video.state === YouTubeVideoState.REVIEWED
    const canCreateEpisode = video.state === YouTubeVideoState.PENDING_REVIEW || video.state === YouTubeVideoState.REVIEWED

    const handleCardClick = () => {
        if (selectionMode && onToggleSelection) {
            onToggleSelection(video.id)
        }
    }

    return (
        <Card
            className={cn(
                "group hover:shadow-lg hover:-translate-y-1 transition-all duration-200 h-full flex flex-col relative",
                selectionMode && "cursor-pointer",
                isSelected && "ring-2 ring-primary",
                className
            )}
            onClick={handleCardClick}
        >
            {/* Selection Checkbox Overlay */}
            {selectionMode && (
                <div className="absolute top-2 left-2 z-10">
                    <div
                        className={cn(
                            "w-6 h-6 rounded border-2 flex items-center justify-center transition-colors",
                            isSelected
                                ? "bg-primary border-primary text-primary-foreground"
                                : "bg-background border-muted-foreground/50"
                        )}
                    >
                        {isSelected && <Check className="h-4 w-4" />}
                    </div>
                </div>
            )}
            <CardContent className="pb-4 space-y-4 flex flex-col h-full">
                {/* Thumbnail */}
                <div className="relative aspect-video rounded-lg overflow-hidden group/thumbnail bg-muted">
                    {video.thumbnail_url ? (
                        <img
                            src={video.thumbnail_url}
                            alt={video.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center">
                            <Play className="h-12 w-12 text-muted-foreground" />
                        </div>
                    )}

                    {/* Duration overlay */}
                    {video.duration && (
                        <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                            {formatDuration(video.duration)}
                        </div>
                    )}

                    {/* State badge overlay */}
                    <div className="absolute top-2 left-2">
                        {getStateBadge(video.state)}
                    </div>
                </div>

                {/* Title and Description */}
                <div className="flex-1 space-y-2">
                    <h3 className="font-semibold text-base line-clamp-2 leading-tight">
                        {video.title}
                    </h3>

                    {video.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                            {video.description}
                        </p>
                    )}

                    {/* Metadata */}
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        {video.publish_date && (
                            <span>
                                {formatDistanceToNow(new Date(video.publish_date), { addSuffix: true })}
                            </span>
                        )}
                        {video.view_count && (
                            <span className="flex items-center gap-1">
                                <Eye className="h-3 w-3" />
                                {video.view_count.toLocaleString()}
                            </span>
                        )}
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t">
                    <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => onViewYouTube?.(video)}
                    >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View on YouTube
                    </Button>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            {canReview && (
                                <DropdownMenuItem onClick={() => onReview?.(video)}>
                                    <CheckCircle2 className="h-4 w-4 mr-2" />
                                    Mark as Reviewed
                                </DropdownMenuItem>
                            )}
                            {canCreateEpisode && (
                                <DropdownMenuItem onClick={() => onCreateEpisode?.(video)}>
                                    <Play className="h-4 w-4 mr-2" />
                                    Create Episode
                                </DropdownMenuItem>
                            )}
                            {canDiscard && (
                                <>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        onClick={() => onDiscard?.(video)}
                                        className="text-destructive"
                                    >
                                        <XCircle className="h-4 w-4 mr-2" />
                                        Discard
                                    </DropdownMenuItem>
                                </>
                            )}
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </CardContent>
        </Card>
    )
}







