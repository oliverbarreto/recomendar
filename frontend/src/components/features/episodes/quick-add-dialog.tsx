/**
 * Quick Add Episode Dialog Component
 */
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Loader2, Plus, Youtube } from 'lucide-react'
import { toast } from 'sonner'
import { episodeApi, channelApi } from '@/lib/api'
import { AudioOptionsSelector } from './audio-options-selector'

interface QuickAddDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function QuickAddDialog({ open, onOpenChange, onSuccess }: QuickAddDialogProps) {
  const [videoUrl, setVideoUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [audioLanguage, setAudioLanguage] = useState<string | null>(null)
  const [audioQuality, setAudioQuality] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!videoUrl.trim()) {
      toast.error('Please enter a YouTube URL')
      return
    }

    // Basic YouTube URL validation
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)/
    if (!youtubeRegex.test(videoUrl.trim())) {
      toast.error('Please enter a valid YouTube URL')
      return
    }

    try {
      setIsLoading(true)
      
      // Get the first channel (assuming single channel setup for now)
      const channels = await channelApi.getAll({ limit: 1 })
      if (channels.length === 0) {
        toast.error('No channels found. Please create a channel first.')
        return
      }
      
      const channel = channels[0]
      
      // Create episode directly (it will auto-analyze the URL)
      const episode = await episodeApi.create({
        channel_id: channel.id,
        video_url: videoUrl.trim(),
        tags: [],
        audio_language: audioLanguage === "default" ? null : audioLanguage,
        audio_quality: audioQuality,
      })
      
      toast.success(`Episode "${episode.title}" has been added and is being processed!`)
      
      // Reset form and close dialog
      setVideoUrl('')
      setAudioLanguage(null)
      setAudioQuality(null)
      onOpenChange(false)
      
      // Notify parent component if callback provided
      if (onSuccess) {
        onSuccess()
      }
      
    } catch (error: unknown) {
      console.error('Failed to create episode:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to add episode'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    if (!isLoading) {
      setVideoUrl('')
      setAudioLanguage(null)
      setAudioQuality(null)
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-600" />
            Quick Add Episode
          </DialogTitle>
          <DialogDescription>
            Paste a YouTube URL to quickly add a new episode. The video information will be automatically extracted.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="video-url">YouTube URL</Label>
            <Input
              id="video-url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              disabled={isLoading}
              className="w-full"
            />
          </div>

          <AudioOptionsSelector
            showToggle={true}
            audioLanguage={audioLanguage}
            audioQuality={audioQuality}
            onLanguageChange={setAudioLanguage}
            onQualityChange={setAudioQuality}
          />

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Adding Episode...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Add Episode
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}