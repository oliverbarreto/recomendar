/**
 * Channel dashboard component displaying channel overview and episodes
 */
"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Plus,
  Podcast,
  Video,
  Clock,
  Play,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { EpisodeCard } from "@/components/features/episodes/episode-card"
import { channelApi } from "@/lib/api"
import { useDeleteEpisode, useEpisodes } from "@/hooks/use-episodes"
import { useAudio } from "@/contexts/audio-context"
import { toast } from "sonner"
import { getApiBaseUrl } from "@/lib/api-url"
import type { Episode, ChannelStatistics } from "@/types"

interface ChannelData {
  id: number
  name: string
  description: string
  episodeCount: number
  totalDuration: string
  feedUrl: string
  lastUpdated: string
  status: "active" | "inactive"
  imageUrl?: string
}

export function ChannelDashboard() {
  const router = useRouter()
  const [channelData, setChannelData] = useState<ChannelData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [totalEpisodes, setTotalEpisodes] = useState(0)
  const [totalDuration, setTotalDuration] = useState("0h 0m")
  const [channelStats, setChannelStats] = useState<ChannelStatistics | null>(
    null
  )

  // Episodes using React Query hook for real-time updates
  const { data: episodesData, isLoading: isLoadingLatest } = useEpisodes({
    channel_id: channelData?.id || 0,
  })

  // Extract episodes and calculate latest episodes
  const allEpisodes = useMemo(
    () => episodesData?.episodes || [],
    [episodesData?.episodes]
  )
  const latestEpisodes = useMemo(
    () =>
      allEpisodes
        .slice() // Create a copy to avoid mutating original
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        .slice(0, 10),
    [allEpisodes]
  )

  // Update totals when episodes data changes
  useEffect(() => {
    if (allEpisodes.length > 0) {
      setTotalEpisodes(allEpisodes.length)

      // Calculate total duration
      const totalDurationSeconds = allEpisodes.reduce((total, episode) => {
        return total + (episode.duration_seconds || 0)
      }, 0)

      setTotalDuration(formatTotalDuration(totalDurationSeconds))
    } else {
      setTotalEpisodes(0)
      setTotalDuration("0h 0m")
    }

    // Check scroll buttons after episodes load
    setTimeout(checkScrollButtons, 100)
  }, [allEpisodes])
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  // Global audio context
  const { playingEpisodeId, playEpisode, stopEpisode } = useAudio()

  // Mutation hooks
  const deleteEpisodeMutation = useDeleteEpisode()

  // Load channel data on component mount
  useEffect(() => {
    loadChannelData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadChannelData = async () => {
    try {
      setIsLoading(true)

      // Get channel data (assuming first channel for now)
      const channels = await channelApi.getAll({ limit: 1 })
      if (channels.length === 0) {
        // No channels exist, show create channel flow
        setChannelData(null)
        return
      }

      const channel = channels[0]

      const feedUrl = `${getApiBaseUrl()}/v1/feeds/${channel.id}/feed.xml`

      // Get channel statistics if available
      let episodeCount = 0
      try {
        const stats = await channelApi.getStatistics(channel.id)
        setChannelStats(stats)
        episodeCount = stats.total_episodes || 0
      } catch (error) {
        console.warn("Could not load channel statistics:", error)
        episodeCount = 0
        setChannelStats(null)
      }

      setChannelData({
        id: channel.id,
        name: channel.name,
        description: channel.description,
        episodeCount,
        totalDuration: totalDuration, // Use calculated total duration
        feedUrl,
        lastUpdated: new Date(channel.updated_at).toLocaleDateString(),
        status: "active",
        imageUrl: channel.image_url
          ? `${channelApi.getImageUrl(channel.id)}?t=${Date.now()}`
          : undefined,
      })
    } catch (error) {
      console.error("Failed to load channel data:", error)
      toast.error("Failed to load channel data")
    } finally {
      setIsLoading(false)
    }
  }

  // Helper function to format duration
  const formatTotalDuration = (totalSeconds: number): string => {
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const checkScrollButtons = () => {
    if (!scrollContainerRef.current) return

    const container = scrollContainerRef.current
    setCanScrollLeft(container.scrollLeft > 0)
    setCanScrollRight(
      container.scrollLeft < container.scrollWidth - container.clientWidth
    )
  }

  const scrollLeft = () => {
    if (!scrollContainerRef.current) return
    const container = scrollContainerRef.current
    const cardWidth = 320 // w-80 = 320px
    container.scrollBy({ left: -cardWidth, behavior: "smooth" })
    setTimeout(checkScrollButtons, 300)
  }

  const scrollRight = () => {
    if (!scrollContainerRef.current) return
    const container = scrollContainerRef.current
    const cardWidth = 320 // w-80 = 320px
    container.scrollBy({ left: cardWidth, behavior: "smooth" })
    setTimeout(checkScrollButtons, 300)
  }

  // Event handlers for episode cards - use direct global audio context calls
  const handlePlayEpisode = (episode: Episode) => {
    // Use global audio context to play episode directly
    playEpisode(episode)
  }

  const handleStopEpisode = () => {
    // Use global audio context to stop episode
    stopEpisode()
  }

  const handleEditEpisode = (episode: { id: number }) => {
    // Navigate to episode detail page for editing
    router.push(`/episodes/${episode.id}`)
  }

  const handleDeleteEpisode = async (episode: { id: number }) => {
    try {
      // Stop audio if this episode is playing
      if (playingEpisodeId === episode.id) {
        stopEpisode()
      }

      // Use the mutation to delete the episode
      await deleteEpisodeMutation.mutateAsync(episode.id)
    } catch (error) {
      console.error("Error deleting episode:", error)
      // Error toast is already handled by the mutation
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-1/3 mb-2" />
          <div className="h-4 bg-muted rounded w-1/2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-24 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!channelData) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-muted-foreground mb-4">
          <Podcast className="w-16 h-16 mx-auto mb-4" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No channel found</h3>
        <p className="text-muted-foreground max-w-sm mb-6">
          Create your first podcast channel to get started with LabCastARR.
        </p>
        <Button onClick={() => router.push("/setup")} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Channel
        </Button>
      </div>
    )
  }

  const stats = [
    { label: "Total Episodes", value: totalEpisodes.toString(), icon: Video },
    { label: "Total Duration", value: totalDuration, icon: Clock },
    {
      label: "YouTube Channels",
      value: channelStats?.unique_youtube_channels?.toString() || "0",
      icon: Play,
    },
    {
      label: "Feed Status",
      value: channelData.status === "active" ? "Active" : "Inactive",
      icon: Podcast,
      isBadge: true,
    },
  ]

  return (
    <div className="space-y-6 min-w-0 w-full overflow-x-hidden">
      {/* Channel Header */}
      <div className="flex items-center gap-6 pb-6">
        <div className="w-20 h-20 bg-muted rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
          {channelData.imageUrl ? (
            <img
              src={channelData.imageUrl}
              alt={`${channelData.name} artwork`}
              className="w-full h-full object-cover rounded-lg"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = "none"
                target.nextElementSibling?.classList.remove("hidden")
              }}
            />
          ) : null}
          <Podcast
            className={`w-8 h-8 text-muted-foreground ${
              channelData.imageUrl ? "hidden" : ""
            }`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold tracking-tight truncate">
            {channelData.name}
          </h1>
          <p className="text-muted-foreground mt-1">
            {channelData.description}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label} className="p-3">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 px-0 pt-0">
                <CardTitle className="text-md md:text-lg font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <Icon className="h-3 w-3 text-muted-foreground" />
              </CardHeader>
              <CardContent className="px-0 pb-0">
                {stat.isBadge ? (
                  <Badge
                    variant="outline"
                    className={`text-md md:text-2xl px-2 py-1 ${
                      channelData.status === "active"
                        ? "text-green-600 border-green-600"
                        : "text-red-600 border-red-600"
                    }`}
                  >
                    {stat.value}
                  </Badge>
                ) : (
                  <div className="text-2xl md:text-3xl font-bold">
                    {stat.value}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Latest Episodes Section */}
      <div className="space-y-4 pt-6">
        <div className="flex items-center justify-between">
          <h2 className="mb-2 text-2xl font-bold tracking-tight">
            Latest Episodes
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={scrollLeft}
              disabled={!canScrollLeft}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={scrollRight}
              disabled={!canScrollRight}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {isLoadingLatest ? (
          <div className="flex gap-4 overflow-x-auto w-full min-w-0">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex-none w-80">
                <div className="animate-pulse">
                  <div className="h-48 bg-muted rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : latestEpisodes.length > 0 ? (
          <div className="relative w-full overflow-hidden min-w-0">
            <div
              ref={scrollContainerRef}
              className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth pt-2 pb-2 min-w-0"
              style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
              onScroll={checkScrollButtons}
            >
              {latestEpisodes.map((episode) => (
                <div key={episode.id} className="flex-none w-80">
                  <EpisodeCard
                    episode={episode}
                    onPlay={handlePlayEpisode}
                    onStop={handleStopEpisode}
                    onEdit={handleEditEpisode}
                    onDelete={handleDeleteEpisode}
                    onRetry={undefined}
                    isPlaying={playingEpisodeId === episode.id}
                  />
                </div>
              ))}
            </div>
            <style jsx>{`
              .scrollbar-hide::-webkit-scrollbar {
                display: none;
              }
            `}</style>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Video className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No episodes available yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
