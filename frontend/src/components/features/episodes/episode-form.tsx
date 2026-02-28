"use client"

/**
 * Episode Form Component - Multi-step form for creating episodes from YouTube URLs
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2, Play, ExternalLink, Plus, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

import { useCreateEpisode, useAnalyzeVideo } from '@/hooks/use-episodes'
import { VideoMetadata, Episode } from '@/types/episode'

// Form validation schema
const episodeFormSchema = z.object({
  video_url: z
    .string()
    .min(1, 'YouTube URL is required')
    .regex(
      /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/,
      'Please enter a valid YouTube URL'
    ),
  tags: z
    .array(z.string().min(1).max(50))
    .max(10, 'Maximum 10 tags allowed')
    .default([])
})

type EpisodeFormValues = z.infer<typeof episodeFormSchema>

interface EpisodeFormProps {
  channelId: number
  onSuccess?: (episode: Episode) => void
  onCancel?: () => void
}

type FormStep = 'url' | 'preview' | 'processing'

export function EpisodeForm({ channelId, onSuccess, onCancel }: EpisodeFormProps) {
  const [step, setStep] = useState<FormStep>('url')
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null)
  const [currentTag, setCurrentTag] = useState('')

  const form = useForm<EpisodeFormValues>({
    resolver: zodResolver(episodeFormSchema),
    defaultValues: {
      video_url: '',
      tags: []
    }
  })

  const analyzeVideoMutation = useAnalyzeVideo()
  const createEpisodeMutation = useCreateEpisode()

  const handleAnalyzeVideo = async (url: string) => {
    try {
      const result = await analyzeVideoMutation.mutateAsync(url)
      setMetadata(result)
      setStep('preview')
    } catch {
      // Error is handled by the mutation hook
    }
  }

  const handleCreateEpisode = async (values: EpisodeFormValues) => {
    setStep('processing')
    
    try {
      const episode = await createEpisodeMutation.mutateAsync({
        channel_id: channelId,
        video_url: values.video_url,
        tags: values.tags
      })
      
      onSuccess?.(episode)
    } catch {
      // Error is handled by the mutation hook, go back to preview
      setStep('preview')
    }
  }

  const handleAddTag = () => {
    if (currentTag.trim() && !form.getValues('tags').includes(currentTag.trim())) {
      const newTags = [...form.getValues('tags'), currentTag.trim()]
      form.setValue('tags', newTags)
      setCurrentTag('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    const newTags = form.getValues('tags').filter(tag => tag !== tagToRemove)
    form.setValue('tags', newTags)
  }

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'Unknown'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }

  if (step === 'url') {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Add Episode from YouTube</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(values => handleAnalyzeVideo(values.video_url))} className="space-y-4">
              <FormField
                control={form.control}
                name="video_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>YouTube URL</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="https://www.youtube.com/watch?v=..."
                        {...field}
                        disabled={analyzeVideoMutation.isPending}
                      />
                    </FormControl>
                    <FormDescription>
                      Paste a YouTube video URL to extract audio and create a podcast episode
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  disabled={analyzeVideoMutation.isPending}
                  className="flex-1"
                >
                  {analyzeVideoMutation.isPending && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  Analyze Video
                </Button>
                
                {onCancel && (
                  <Button type="button" variant="outline" onClick={onCancel}>
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    )
  }

  if (step === 'preview' && metadata) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Episode Preview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Video Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
              {metadata.thumbnail_url && (
                <div className="aspect-video relative rounded-lg overflow-hidden bg-muted">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img 
                    src={metadata.thumbnail_url} 
                    alt={metadata.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                    <Play className="w-12 h-12 text-white" />
                  </div>
                </div>
              )}
            </div>
            
            <div className="md:col-span-2 space-y-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">{metadata.title}</h3>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  {metadata.uploader && (
                    <span>by {metadata.uploader}</span>
                  )}
                  {metadata.duration_seconds && (
                    <span>Duration: {formatDuration(metadata.duration_seconds)}</span>
                  )}
                  {metadata.view_count > 0 && (
                    <span>{formatNumber(metadata.view_count)} views</span>
                  )}
                </div>
              </div>
              
              {metadata.description && (
                <div>
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {metadata.description}
                  </p>
                </div>
              )}
              
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(metadata.video_url, '_blank')}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View on YouTube
                </Button>
              </div>
            </div>
          </div>

          <Separator />

          {/* Tags Input */}
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleCreateEpisode)} className="space-y-4">
              <div className="space-y-4">
                <div>
                  <FormLabel>Tags (Optional)</FormLabel>
                  <div className="flex gap-2 mt-2">
                    <Input
                      placeholder="Add a tag..."
                      value={currentTag}
                      onChange={(e) => setCurrentTag(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          handleAddTag()
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={handleAddTag}
                      disabled={!currentTag.trim() || form.getValues('tags').length >= 10}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Add tags to help organize and search your episodes
                  </p>
                </div>

                {form.getValues('tags').length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {form.getValues('tags').map((tag) => (
                      <Badge key={tag} variant="secondary" className="gap-1">
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:bg-muted-foreground/20 rounded-sm"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createEpisodeMutation.isPending}
                  className="flex-1"
                >
                  {createEpisodeMutation.isPending && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  Create Episode
                </Button>
                
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setStep('url')
                    setMetadata(null)
                  }}
                  disabled={createEpisodeMutation.isPending}
                >
                  Back
                </Button>
                
                {onCancel && (
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={onCancel}
                    disabled={createEpisodeMutation.isPending}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    )
  }

  if (step === 'processing') {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
            <div>
              <h3 className="text-lg font-semibold">Creating Episode</h3>
              <p className="text-muted-foreground">
                Your episode is being created and the audio download will begin shortly...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return null
}