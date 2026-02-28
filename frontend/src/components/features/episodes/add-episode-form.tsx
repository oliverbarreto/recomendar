/**
 * Multi-step episode creation form with YouTube URL validation and preview
 */
'use client'

import { useState, useCallback } from 'react'
import * as React from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Clipboard,
  Loader2,
  Video
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { episodeApi, channelApi } from '@/lib/api'
import { AudioOptionsSelector } from './audio-options-selector'

// Form validation schema
const addEpisodeSchema = z.object({
  url: z.string().url('Please enter a valid YouTube URL').refine(
    (url) => {
      try {
        const urlObj = new URL(url)
        return (
          urlObj.hostname === 'www.youtube.com' ||
          urlObj.hostname === 'youtube.com' ||
          urlObj.hostname === 'youtu.be' ||
          urlObj.hostname === 'm.youtube.com'
        )
      } catch {
        return false
      }
    },
    { message: 'Please enter a valid YouTube URL' }
  ),
})

type AddEpisodeFormData = z.infer<typeof addEpisodeSchema>


const steps = [
  { id: 1, title: "Enter URL", description: "Provide YouTube video URL" },
  { id: 2, title: "Create Episode", description: "Add episode to your channel" },
  { id: 3, title: "Processing", description: "Download and process" },
]

// Helper functions
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function AddEpisodeForm() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [createdEpisode, setCreatedEpisode] = useState<{
    id: number
    title: string
    video_id: string
    thumbnail_url?: string
    duration?: number
  } | null>(null)
  const [progress, setProgress] = useState(0)
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)
  const [audioLanguage, setAudioLanguage] = useState<string | null>(null)
  const [audioQuality, setAudioQuality] = useState<string | null>(null)

  const form = useForm<AddEpisodeFormData>({
    resolver: zodResolver(addEpisodeSchema),
    defaultValues: {
      url: '',
    },
  })


  const handleCreateEpisode = useCallback(async () => {
    const url = form.getValues('url')
    if (!url) return

    setIsSubmitting(true)
    setCurrentStep(2)

    try {
      // Get the first channel (assuming single channel setup for now)
      const channels = await channelApi.getAll({ limit: 1 })
      if (channels.length === 0) {
        toast.error('No channels found. Please create a channel first.')
        return
      }

      const channel = channels[0]

      // Create episode directly (same as quick add workflow)
      const episode = await episodeApi.create({
        channel_id: channel.id,
        video_url: url.trim(),
        tags: [],
        audio_language: audioLanguage === "default" ? null : audioLanguage,
        audio_quality: audioQuality,
      })

      setCreatedEpisode({
        id: episode.id,
        title: episode.title,
        video_id: episode.video_id,
        thumbnail_url: episode.thumbnail_url,
        duration: episode.duration_seconds
      })

      setCurrentStep(2)
      toast.success(`Episode "${episode.title}" has been added and is being processed!`)

    } catch (error: unknown) {
      console.error('Episode creation failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create episode'
      toast.error(errorMessage)
      setIsSubmitting(false)
      setCurrentStep(1)
    }
  }, [form, audioLanguage, audioQuality])

  const handlePasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text && (text.includes('youtube.com') || text.includes('youtu.be'))) {
        form.setValue('url', text)
        toast.success('URL pasted from clipboard')
      } else {
        toast.error('No YouTube URL found in clipboard')
      }
    } catch {
      toast.error('Failed to access clipboard')
    }
  }

  const startProgressPolling = useCallback(() => {
    if (!createdEpisode) return

    setProgress(0)

    // Start polling for progress
    const interval = setInterval(async () => {
      try {
        const progressData = await episodeApi.getProgress(createdEpisode.id)
        const percentage = parseFloat(progressData.percentage.replace('%', ''))
        setProgress(percentage)

        if (progressData.status === 'completed' || percentage >= 100) {
          clearInterval(interval)
          setProgress(100)
          setTimeout(() => {
            toast.success('Episode download completed!')
            router.push('/')
          }, 1000)
        } else if (progressData.status === 'failed') {
          clearInterval(interval)
          toast.error(progressData.error_message || 'Download failed')
        }
      } catch (error) {
        console.error('Progress check failed:', error)
      }
    }, 1000)

    setPollingInterval(interval)
  }, [createdEpisode, router])

  const renderStepIndicator = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <div
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-medium",
                currentStep >= step.id
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-background text-muted-foreground border-muted-foreground"
              )}
            >
              {currentStep > step.id ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                step.id
              )}
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-4",
                  currentStep > step.id ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between mt-2">
        {steps.map((step) => (
          <div key={step.id} className="text-center flex-1">
            <div className="text-xs font-medium">{step.title}</div>
            <div className="text-xs text-muted-foreground">{step.description}</div>
          </div>
        ))}
      </div>
    </div>
  )

  const renderStep1 = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Video className="w-5 h-5" />
          Enter YouTube URL
        </CardTitle>
        <CardDescription>
          Paste the URL of the YouTube video you want to convert to a podcast episode
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Form {...form}>
          <FormField
            control={form.control}
            name="url"
            render={({ field }) => (
              <FormItem>
                <FormLabel>YouTube URL</FormLabel>
                <div className="flex gap-2">
                  <FormControl>
                    <Input
                      placeholder="https://www.youtube.com/watch?v=..."
                      {...field}
                      className="flex-1"
                    />
                  </FormControl>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handlePasteFromClipboard}
                  >
                    <Clipboard className="w-4 h-4" />
                  </Button>
                </div>
                <FormDescription>
                  Supports youtube.com, youtu.be, and mobile YouTube URLs
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </Form>

        <AudioOptionsSelector
          showToggle={true}
          audioLanguage={audioLanguage}
          audioQuality={audioQuality}
          onLanguageChange={setAudioLanguage}
          onQualityChange={setAudioQuality}
        />

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <AlertCircle className="w-4 h-4" />
          <span>Make sure the video is public and not age-restricted</span>
        </div>
      </CardContent>
      <CardFooter>
        <Button
          onClick={handleCreateEpisode}
          disabled={!form.getValues('url') || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Creating Episode...
            </>
          ) : (
            <>
              <ArrowRight className="w-4 h-4 mr-2" />
              Add Episode
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )

  const renderStep2 = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          Episode Created
        </CardTitle>
        <CardDescription>
          Your episode has been successfully added and is being processed
        </CardDescription>
      </CardHeader>
      <CardContent>
        {createdEpisode && (
          <div className="space-y-4">
            {/* Episode Info */}
            <div className="flex gap-4">
              <div className="relative aspect-video w-64 bg-muted rounded-lg overflow-hidden">
                <img
                  src={createdEpisode.thumbnail_url || `https://img.youtube.com/vi/${createdEpisode.video_id}/maxresdefault.jpg`}
                  alt={createdEpisode.title}
                  className="w-full h-full object-cover"
                />
                {createdEpisode.duration && (
                  <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                    {formatDuration(createdEpisode.duration)}
                  </div>
                )}
              </div>
              <div className="flex-1 space-y-2">
                <h3 className="font-semibold">{createdEpisode.title}</h3>
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span>Episode added successfully</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Your episode is now being downloaded and processed. You can view the progress in the next step.
                </p>
              </div>
            </div>

            <Separator />

            {/* Processing Info */}
            <div className="space-y-2">
              <Label>Processing Status</Label>
              <Badge variant="default" className="cursor-pointer">
                Ready for Download
              </Badge>
              <p className="text-xs text-muted-foreground">
                Video will be converted to high-quality audio format for podcast distribution
              </p>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button variant="outline" onClick={() => setCurrentStep(1)} disabled={isSubmitting}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={() => { setCurrentStep(3); startProgressPolling(); }} className="flex-1">
          View Progress
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </CardFooter>
    </Card>
  )

  const renderStep3 = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          Processing Episode
        </CardTitle>
        <CardDescription>
          Downloading and converting your video to audio format
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">
            {progress < 20 && "Extracting video information..."}
            {progress >= 20 && progress < 50 && "Downloading audio stream..."}
            {progress >= 50 && progress < 80 && "Converting to podcast format..."}
            {progress >= 80 && progress < 100 && "Finalizing episode..."}
            {progress >= 100 && "Episode created successfully!"}
          </div>
        </div>

        {createdEpisode && (
          <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
            <div className="w-16 h-12 bg-background rounded overflow-hidden">
              <img
                src={createdEpisode.thumbnail_url || `https://img.youtube.com/vi/${createdEpisode.video_id}/maxresdefault.jpg`}
                alt={createdEpisode.title}
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <div className="font-medium text-sm">{createdEpisode.title}</div>
              <div className="text-xs text-muted-foreground">
                {createdEpisode.duration ? formatDuration(createdEpisode.duration) : 'Unknown'} • Episode ID: {createdEpisode.id}
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <AlertCircle className="w-4 h-4" />
          <span>This process may take a few minutes depending on video length</span>
        </div>
      </CardContent>
    </Card>
  )


  // Cleanup polling interval on unmount
  React.useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [pollingInterval])

  return (
    <div className="space-y-6">
      {renderStepIndicator()}

      {currentStep === 1 && renderStep1()}
      {currentStep === 2 && renderStep2()}
      {currentStep === 3 && renderStep3()}
    </div>
  )
}