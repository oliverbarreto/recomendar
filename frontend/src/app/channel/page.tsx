"use client"

import { useState, useEffect } from "react"
import { use } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { SearchInterface } from "@/components/features/search/search-interface"
import { Podcast } from "lucide-react"
import { channelApi } from "@/lib/api"
import { toast } from "sonner"
import { UserPreferences } from "@/lib/user-preferences"

interface ChannelData {
  id: number
  name: string
  description: string
  imageUrl?: string
}

interface ChannelPageProps {
  searchParams?: Promise<{
    q?: string
    tags?: string
    favorites?: string
    page?: string
    pageSize?: string
  }>
}

export default function ChannelPage({ searchParams }: ChannelPageProps) {
  const [channelData, setChannelData] = useState<ChannelData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSearchVisible, setIsSearchVisible] = useState(false)

  // Parse URL search parameters
  const urlParams = searchParams ? use(searchParams) : {}
  const initialSearchQuery = urlParams.q || ""
  const initialTagIds = urlParams.tags
    ? urlParams.tags
        .split(",")
        .map((id) => parseInt(id.trim()))
        .filter((id) => !isNaN(id))
    : []
  const initialFavoritesOnly = urlParams.favorites === "true"
  const initialPage = urlParams.page ? parseInt(urlParams.page) || 1 : 1
  // Load page size from URL params first, then fall back to localStorage preference
  // If URL param exists, use it; otherwise, load from localStorage (usePagination hook will handle this)
  const initialPageSize = urlParams.pageSize
    ? parseInt(urlParams.pageSize) || UserPreferences.getPageSize()
    : undefined

  useEffect(() => {
    loadChannelData()
  }, [])

  // Keyboard shortcuts for search toggle
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // CMD+F or Ctrl+F to open search
      if ((event.metaKey || event.ctrlKey) && event.key === "f") {
        event.preventDefault()
        setIsSearchVisible(true)
      }
      // ESC to close search
      if (event.key === "Escape" && isSearchVisible) {
        setIsSearchVisible(false)
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [isSearchVisible])

  // Function to toggle search visibility
  const toggleSearch = () => {
    setIsSearchVisible(!isSearchVisible)
  }

  const loadChannelData = async () => {
    try {
      setIsLoading(true)

      // Get channel data (assuming first channel for now)
      const channels = await channelApi.getAll({ limit: 1 })
      if (channels.length === 0) {
        setChannelData(null)
        return
      }

      const channel = channels[0]
      setChannelData({
        id: channel.id,
        name: channel.name,
        description: channel.description,
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

  return (
    <MainLayout onSearchToggle={toggleSearch} showSearchButton={true}>
      <div className="space-y-6">
        {/* Channel Header */}
        {isLoading ? (
          <div className="animate-pulse flex items-center gap-6">
            <div className="w-20 h-20 bg-muted rounded-lg flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="h-8 bg-muted rounded w-1/3 mb-2" />
              <div className="h-4 bg-muted rounded w-1/2" />
            </div>
          </div>
        ) : channelData ? (
          <div className="flex items-center gap-6">
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
        ) : null}

        {/* Section Header */}
        {/* <div className="mb-6">
          <h2 className="text-2xl font-bold tracking-tight">Search Episodes</h2>
          <p className="text-muted-foreground mt-2">
            Find episodes by title, description, tags, or keywords
          </p>
        </div> */}

        {/* Search Interface - Always show episodes, conditionally show search filters */}
        <SearchInterface
          initialSearchQuery={initialSearchQuery}
          initialTagIds={initialTagIds}
          initialFavoritesOnly={initialFavoritesOnly}
          initialPage={initialPage}
          initialPageSize={initialPageSize}
          onToggleVisibility={toggleSearch}
          isSearchVisible={isSearchVisible}
        />
      </div>
    </MainLayout>
  )
}
