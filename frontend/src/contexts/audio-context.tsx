'use client'

/**
 * Global Audio Context for managing audio playback across all pages
 */

import React, { createContext, useContext, useState, useRef, useCallback, useEffect } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import type { Episode } from '@/types'

interface AudioContextState {
  // Playback state
  playingEpisodeId: number | null
  currentEpisode: Episode | null
  isPlaying: boolean
  isLoading: boolean

  // Audio properties
  currentTime: number
  duration: number
  volume: number

  // Actions
  playEpisode: (episode: Episode) => void
  stopEpisode: () => void
  stopAndReset: () => void
  pauseEpisode: () => void
  resumeEpisode: () => void
  seekTo: (time: number) => void
  setVolume: (volume: number) => void
  skipBackward: (seconds?: number) => void
  skipForward: (seconds?: number) => void
}

const AudioContext = createContext<AudioContextState | null>(null)

interface AudioProviderProps {
  children: React.ReactNode
}

export function AudioProvider({ children }: AudioProviderProps) {
  // Audio state
  const [playingEpisodeId, setPlayingEpisodeId] = useState<number | null>(null)
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolumeState] = useState(1)

  // Audio element and handlers
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioHandlersRef = useRef<{
    handleEnded?: () => void
    handleError?: (e: Event) => void
    handleTimeUpdate?: () => void
    handleLoadedMetadata?: () => void
    handlePlay?: () => void
    handlePause?: () => void
  }>({})

  // Helper function to clean up audio
  const cleanupAudio = useCallback((audio: HTMLAudioElement) => {
    const handlers = audioHandlersRef.current

    // Remove stored event listeners
    if (handlers.handleEnded) {
      audio.removeEventListener('ended', handlers.handleEnded)
    }
    if (handlers.handleError) {
      audio.removeEventListener('error', handlers.handleError)
    }
    if (handlers.handleTimeUpdate) {
      audio.removeEventListener('timeupdate', handlers.handleTimeUpdate)
    }
    if (handlers.handleLoadedMetadata) {
      audio.removeEventListener('loadedmetadata', handlers.handleLoadedMetadata)
    }
    if (handlers.handlePlay) {
      audio.removeEventListener('play', handlers.handlePlay)
    }
    if (handlers.handlePause) {
      audio.removeEventListener('pause', handlers.handlePause)
    }

    // Clear handlers reference
    audioHandlersRef.current = {}

    // Clean up audio
    audio.pause()
    audio.src = ''
    audio.load()
  }, [])

  // Play episode function
  const playEpisode = useCallback(async (episode: Episode) => {
    try {
      // Stop current audio if playing
      if (audioRef.current) {
        cleanupAudio(audioRef.current)
        audioRef.current = null
      }

      setIsLoading(true)
      setCurrentEpisode(episode)
      setPlayingEpisodeId(episode.id)

      // Create new audio element with video_id-based URL for permanent links
      const audioUrl = apiClient.getEpisodeAudioUrl(episode)
      const audio = new Audio(audioUrl)
      audioRef.current = audio

      // Create event handlers
      const handleEnded = () => {
        setIsPlaying(false)
        setPlayingEpisodeId(null)
        setCurrentEpisode(null)
        setCurrentTime(0)
      }

      const handleError = (e: Event) => {
        console.error('Audio playback error:', e)
        toast.error('Failed to play episode audio')
        setIsPlaying(false)
        setPlayingEpisodeId(null)
        setCurrentEpisode(null)
        setIsLoading(false)
      }

      const handleTimeUpdate = () => {
        setCurrentTime(audio.currentTime)
      }

      const handleLoadedMetadata = () => {
        setDuration(audio.duration)
        setIsLoading(false)
      }

      const handlePlay = () => {
        setIsPlaying(true)
      }

      const handlePause = () => {
        setIsPlaying(false)
      }

      // Store handlers for cleanup
      audioHandlersRef.current = {
        handleEnded,
        handleError,
        handleTimeUpdate,
        handleLoadedMetadata,
        handlePlay,
        handlePause
      }

      // Add event listeners
      audio.addEventListener('ended', handleEnded)
      audio.addEventListener('error', handleError)
      audio.addEventListener('timeupdate', handleTimeUpdate)
      audio.addEventListener('loadedmetadata', handleLoadedMetadata)
      audio.addEventListener('play', handlePlay)
      audio.addEventListener('pause', handlePause)

      // Set volume
      audio.volume = volume

      // Start playback
      await audio.play()
      toast.success('Playing episode')
    } catch (error) {
      console.error('Error in playEpisode:', error)
      toast.error('Failed to play episode')
      setIsLoading(false)
      setIsPlaying(false)
    }
  }, [cleanupAudio, volume])

  // Stop episode function (clears everything, hides media player)
  const stopEpisode = useCallback(() => {
    if (audioRef.current) {
      cleanupAudio(audioRef.current)
      audioRef.current = null
    }
    setIsPlaying(false)
    setPlayingEpisodeId(null)
    setCurrentEpisode(null)
    setCurrentTime(0)
    setDuration(0)
    toast.success('Episode stopped')
  }, [cleanupAudio])

  // Stop and reset to start (keeps episode loaded, resets playback position)
  const stopAndReset = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setCurrentTime(0)
      setIsPlaying(false)
      toast.success('Playback stopped and reset')
    }
  }, [])

  // Pause episode function
  const pauseEpisode = useCallback(() => {
    if (audioRef.current && isPlaying) {
      audioRef.current.pause()
    }
  }, [isPlaying])

  // Resume episode function
  const resumeEpisode = useCallback(async () => {
    if (audioRef.current && !isPlaying) {
      try {
        await audioRef.current.play()
      } catch (error) {
        console.error('Error resuming audio:', error)
        toast.error('Failed to resume playback')
      }
    }
  }, [isPlaying])

  // Seek to specific time
  const seekTo = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, duration))
      setCurrentTime(audioRef.current.currentTime)
    }
  }, [duration])

  // Set volume
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, newVolume))
    setVolumeState(clampedVolume)
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume
    }
  }, [])

  // Skip backward
  const skipBackward = useCallback((seconds: number = 10) => {
    if (audioRef.current) {
      const newTime = Math.max(0, currentTime - seconds)
      seekTo(newTime)
    }
  }, [currentTime, seekTo])

  // Skip forward
  const skipForward = useCallback((seconds: number = 30) => {
    if (audioRef.current) {
      const newTime = Math.min(duration, currentTime + seconds)
      seekTo(newTime)
    }
  }, [currentTime, duration, seekTo])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        cleanupAudio(audioRef.current)
      }
    }
  }, [cleanupAudio])

  const contextValue: AudioContextState = {
    playingEpisodeId,
    currentEpisode,
    isPlaying,
    isLoading,
    currentTime,
    duration,
    volume,
    playEpisode,
    stopEpisode,
    stopAndReset,
    pauseEpisode,
    resumeEpisode,
    seekTo,
    setVolume,
    skipBackward,
    skipForward
  }

  return (
    <AudioContext.Provider value={contextValue}>
      {children}
    </AudioContext.Provider>
  )
}

// Hook to use the audio context
export function useAudio(): AudioContextState {
  const context = useContext(AudioContext)
  if (!context) {
    throw new Error('useAudio must be used within an AudioProvider')
  }
  return context
}