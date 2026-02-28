'use client'

/**
 * Global Media Player Component - Shows at bottom of screen when audio is playing
 */

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import {
  Play,
  Pause,
  Square,
  Volume2,
  SkipBack,
  SkipForward,
  Podcast,
  ChevronDown
} from 'lucide-react'
import { useAudio } from '@/contexts/audio-context'
import { cn } from '@/lib/utils'

// Format time helper
const formatTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function GlobalMediaPlayer() {
  const {
    currentEpisode,
    isPlaying,
    isLoading,
    currentTime,
    duration,
    volume,
    stopEpisode,
    stopAndReset,
    pauseEpisode,
    resumeEpisode,
    seekTo,
    setVolume,
    skipBackward,
    skipForward
  } = useAudio()

  // Track sidebar collapse state to adjust media player position
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem('sidepanel-collapsed')
      return saved === 'true'
    } catch (e) {
      return false
    }
  })

  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Listen for sidebar collapse state changes
  useEffect(() => {
    const handleCollapseChange = (event: CustomEvent<{ isCollapsed: boolean }>) => {
      if (event.detail && typeof event.detail.isCollapsed === 'boolean') {
        setIsCollapsed(event.detail.isCollapsed)
      }
    }

    window.addEventListener('sidepanel-collapse-change', handleCollapseChange as EventListener)
    return () => window.removeEventListener('sidepanel-collapse-change', handleCollapseChange as EventListener)
  }, [])

  // Don't render if no episode is loaded
  if (!currentEpisode) {
    return null
  }

  return (
    <div className={cn(
      "fixed bottom-0 right-0 bg-background border-t border-border shadow-lg z-50 transition-all duration-300",
      // On mobile: full width (left-0), on desktop: respect sidebar width
      "left-0",
      isMounted && (isCollapsed ? "md:left-16" : "md:left-64")
    )}>
      <div className="max-w-7xl mx-auto p-4">
        <div className="flex items-center gap-4">
          {/* Episode Info */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="w-12 h-12 bg-muted rounded-md flex items-center justify-center overflow-hidden flex-shrink-0">
              {currentEpisode.thumbnail_url ? (
                <img
                  src={currentEpisode.thumbnail_url}
                  alt={currentEpisode.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Podcast className="w-6 h-6 text-muted-foreground" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-sm truncate">{currentEpisode.title}</p>
              <p className="text-xs text-muted-foreground truncate">
                {formatTime(currentTime)} / {formatTime(duration)}
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            {/* Stop Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={stopAndReset}
              disabled={!currentEpisode || isLoading}
              className="h-10 w-10"
              aria-label="Stop and reset"
            >
              <Square className="w-5 h-5" />
            </Button>

            {/* Play/Pause Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={isPlaying ? pauseEpisode : resumeEpisode}
              disabled={isLoading}
              className="h-10 w-10"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : isPlaying ? (
                <Pause className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5 ml-0.5" />
              )}
            </Button>

            {/* Skip Backward Button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => skipBackward(10)}
              disabled={!isPlaying && !duration}
            >
              <SkipBack className="w-4 h-4" />
            </Button>

            {/* Play/Pause Button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => skipForward(30)}
              disabled={!isPlaying && !duration}
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>

          {/* Progress Bar */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <span className="text-xs text-muted-foreground font-mono tabular-nums">
              {formatTime(currentTime)}
            </span>
            <Slider
              value={[duration > 0 ? (currentTime / duration) * 100 : 0]}
              onValueChange={(value) => {
                if (duration > 0) {
                  const newTime = (value[0] / 100) * duration
                  seekTo(newTime)
                }
              }}
              max={100}
              step={0.1}
              className="flex-1"
              disabled={!duration}
            />
            <span className="text-xs text-muted-foreground font-mono tabular-nums">
              {formatTime(duration)}
            </span>
          </div>

          {/* Volume Control */}
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-muted-foreground" />
            <Slider
              value={[volume * 100]}
              onValueChange={(value) => setVolume(value[0] / 100)}
              max={100}
              step={1}
              className="w-20"
            />
          </div>
          {/* Stop & Close Media Player Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={stopEpisode}
            className="h-8 w-8 hover:text-destructive"
          >
            <ChevronDown className="w-4 h-4" />
          </Button>

        </div>
      </div>
    </div>
  )
}