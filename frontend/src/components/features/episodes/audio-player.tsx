"use client"

/**
 * Audio Player Component - Handles episode audio playback
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  MoreHorizontal,
  Minimize2,
  Maximize2,
  Download,
  ExternalLink,
  ChevronDown
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

import { Episode } from '@/types/episode'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface AudioPlayerProps {
  episode: Episode | null
  isVisible?: boolean
  onToggleVisibility?: () => void
  onClose?: () => void
  className?: string
}

export function AudioPlayer({
  episode,
  isVisible = true,
  onToggleVisibility,
  onClose,
  className
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)

  // Update audio source when episode changes and set up event listeners
  useEffect(() => {
    if (episode?.audio_file_path && audioRef.current) {
      const audio = audioRef.current
      const audioUrl = apiClient.getEpisodeAudioUrl(episode)

      // Reset state
      setCurrentTime(0)
      setDuration(0)
      setIsPlaying(false)
      setIsLoading(true)

      // Set up event handlers
      const handleTimeUpdate = () => setCurrentTime(audio.currentTime)
      const handleDurationChange = () => setDuration(audio.duration || 0)
      const handleLoadStart = () => setIsLoading(true)
      const handleCanPlay = () => setIsLoading(false)
      const handleLoadedMetadata = () => {
        setDuration(audio.duration || 0)
        setIsLoading(false)
      }
      const handleEnded = () => setIsPlaying(false)
      const handleError = () => {
        setIsLoading(false)
        setIsPlaying(false)
      }

      // Add event listeners
      audio.addEventListener('timeupdate', handleTimeUpdate)
      audio.addEventListener('durationchange', handleDurationChange)
      audio.addEventListener('loadstart', handleLoadStart)
      audio.addEventListener('canplay', handleCanPlay)
      audio.addEventListener('loadedmetadata', handleLoadedMetadata)
      audio.addEventListener('ended', handleEnded)
      audio.addEventListener('error', handleError)

      // Set audio source
      audio.src = audioUrl

      // Auto-play when episode is loaded
      const autoPlay = async () => {
        try {
          await audio.play()
          setIsPlaying(true)
        } catch (error) {
          console.error('Auto-play failed:', error)
          // Auto-play might be blocked by browser, user will need to click play manually
          setIsPlaying(false)
        }
      }

      // Small delay to ensure audio is ready
      setTimeout(autoPlay, 100)

      // Cleanup function
      return () => {
        audio.removeEventListener('timeupdate', handleTimeUpdate)
        audio.removeEventListener('durationchange', handleDurationChange)
        audio.removeEventListener('loadstart', handleLoadStart)
        audio.removeEventListener('canplay', handleCanPlay)
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
        audio.removeEventListener('ended', handleEnded)
        audio.removeEventListener('error', handleError)
      }
    }
  }, [episode])

  // Audio control functions
  const togglePlayPause = useCallback(async () => {
    if (!audioRef.current || !episode) return

    try {
      if (isPlaying) {
        audioRef.current.pause()
        setIsPlaying(false)
      } else {
        await audioRef.current.play()
        setIsPlaying(true)
      }
    } catch (error) {
      console.error('Error toggling playback:', error)
      setIsPlaying(false)
    }
  }, [audioRef, episode, isPlaying])

  const skipForward = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.min(
        audioRef.current.currentTime + 15,
        duration
      )
    }
  }, [duration])

  const skipBackward = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(
        audioRef.current.currentTime - 15,
        0
      )
    }
  }, [])

  const toggleMute = useCallback(() => {
    if (audioRef.current) {
      const newMuted = !isMuted
      setIsMuted(newMuted)
      audioRef.current.volume = newMuted ? 0 : volume
    }
  }, [isMuted, volume])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!episode || !isVisible) return

      switch (e.key) {
        case ' ':
          e.preventDefault()
          togglePlayPause()
          break
        case 'ArrowLeft':
          e.preventDefault()
          skipBackward()
          break
        case 'ArrowRight':
          e.preventDefault()
          skipForward()
          break
        case 'm':
          e.preventDefault()
          toggleMute()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [episode, isVisible, togglePlayPause, skipBackward, skipForward, toggleMute])


  const handleSeek = (value: number[]) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value[0]
      setCurrentTime(value[0])
    }
  }

  const handleVolumeChange = (value: number[]) => {
    const newVolume = value[0]
    setVolume(newVolume)
    if (audioRef.current) {
      audioRef.current.volume = newVolume
    }
    if (newVolume > 0 && isMuted) {
      setIsMuted(false)
    }
  }


  const changePlaybackRate = (rate: number) => {
    setPlaybackRate(rate)
    if (audioRef.current) {
      audioRef.current.playbackRate = rate
    }
  }

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '0:00'

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  if (!episode) return null

  return (
    <>
      <audio ref={audioRef} preload="metadata" />

      <Card className={cn(
        "fixed bottom-0 left-0 right-0 z-50 border-t shadow-lg transition-transform duration-300",
        !isVisible && "translate-y-full",
        className
      )}>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            {/* Episode Info */}
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {episode.thumbnail_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={episode.thumbnail_url}
                  alt={episode.title}
                  className="w-12 h-12 rounded object-cover"
                />
              )}
              <div className="min-w-0 flex-1">
                <h3 className="font-medium truncate text-sm">
                  {episode.title}
                </h3>
                <p className="text-xs text-muted-foreground">
                  Episode
                </p>
              </div>
            </div>

            {/* Main Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={skipBackward}
                disabled={!episode.audio_file_path}
              >
                <SkipBack className="w-4 h-4" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={togglePlayPause}
                disabled={!episode.audio_file_path || isLoading}
                className="h-10 w-10"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : isPlaying ? (
                  <Pause className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={skipForward}
                disabled={!episode.audio_file_path}
              >
                <SkipForward className="w-4 h-4" />
              </Button>
            </div>

            {/* Progress Bar */}
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="text-xs text-muted-foreground w-12 text-right">
                {formatTime(currentTime)}
              </span>
              <Slider
                value={[currentTime]}
                onValueChange={handleSeek}
                max={duration || 100}
                step={1}
                className="flex-1"
                disabled={!episode.audio_file_path}
              />
              <span className="text-xs text-muted-foreground w-12">
                {formatTime(duration)}
              </span>
            </div>

            {/* Volume Control */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleMute}
                className="h-8 w-8"
              >
                {isMuted || volume === 0 ? (
                  <VolumeX className="w-4 h-4" />
                ) : (
                  <Volume2 className="w-4 h-4" />
                )}
              </Button>
              <Slider
                value={[isMuted ? 0 : volume]}
                onValueChange={handleVolumeChange}
                max={1}
                step={0.01}
                className="w-20"
              />
            </div>

            {/* More Options */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => changePlaybackRate(0.5)}>
                  Speed: 0.5x {playbackRate === 0.5 && '✓'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => changePlaybackRate(0.75)}>
                  Speed: 0.75x {playbackRate === 0.75 && '✓'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => changePlaybackRate(1)}>
                  Speed: 1x {playbackRate === 1 && '✓'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => changePlaybackRate(1.25)}>
                  Speed: 1.25x {playbackRate === 1.25 && '✓'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => changePlaybackRate(1.5)}>
                  Speed: 1.5x {playbackRate === 1.5 && '✓'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => changePlaybackRate(2)}>
                  Speed: 2x {playbackRate === 2 && '✓'}
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem onClick={() => window.open(episode.video_url, '_blank')}>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View on YouTube
                </DropdownMenuItem>

                <DropdownMenuItem
                  onClick={() => window.open(apiClient.getEpisodeAudioUrl(episode.id), '_blank')}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Audio
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                {onToggleVisibility && (
                  <DropdownMenuItem onClick={onToggleVisibility}>
                    {isVisible ? (
                      <>
                        <Minimize2 className="w-4 h-4 mr-2" />
                        Minimize Player
                      </>
                    ) : (
                      <>
                        <Maximize2 className="w-4 h-4 mr-2" />
                        Show Player
                      </>
                    )}
                  </DropdownMenuItem>
                )}

                {onClose && (
                  <DropdownMenuItem onClick={onClose} className="text-destructive">
                    Close Player
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Close Button */}
            {onClose && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-8 w-8"
                title="Close Player"
              >
                <ChevronDown className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </>
  )
}