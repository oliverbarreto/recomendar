/**
 * Episode Detail Page with real data fetching and metadata management
 */
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  ArrowLeft,
  Edit3,
  ExternalLink,
  Download,
  Calendar,
  Clock,
  FileAudio,
  Hash,
  Save,
  X,
  Plus,
  Trash2,
  Play,
  Square,
  Settings,
  Loader2,
  MoreVertical,
  Heart,
  RefreshCcw,
  Youtube
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { episodeApi, tagApi } from '@/lib/api'
import { useAudio } from '@/contexts/audio-context'
import { useFavoriteEpisode, useUnfavoriteEpisode } from '@/hooks/use-episodes'
import { getApiBaseUrl } from '@/lib/api-url'
import type { Episode, EpisodeStatus, Tag } from '@/types'
import { generateGradientStyle, getOptimalTextColor, generateEpisodeGradient } from '@/lib/colors'
import { FollowChannelModal } from '@/components/features/subscriptions/follow-channel-modal'

interface EpisodeDetailProps {
  episodeId: number
}

export function EpisodeDetail({ episodeId }: EpisodeDetailProps) {
  const router = useRouter()
  const [episode, setEpisode] = useState<Episode | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    keywords: [] as string[],
    selectedTagIds: [] as number[]
  })
  const [availableTags, setAvailableTags] = useState<Tag[]>([])
  const [newKeyword, setNewKeyword] = useState('')
  const [isLoadingTags, setIsLoadingTags] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [followModalOpen, setFollowModalOpen] = useState(false)

  // Global audio context
  const { playingEpisodeId, playEpisode, stopEpisode } = useAudio()

  // Favorite mutations
  const favoriteMutation = useFavoriteEpisode()
  const unfavoriteMutation = useUnfavoriteEpisode()

  useEffect(() => {
    loadEpisode()
  }, [episodeId])

  const loadEpisode = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const fetchedEpisode = await episodeApi.getById(episodeId)
      setEpisode(fetchedEpisode)

      // Load available tags for the channel
      setIsLoadingTags(true)
      const tagsResponse = await tagApi.getAll(fetchedEpisode.channel_id)
      setAvailableTags(tagsResponse.tags)

      setEditForm({
        title: fetchedEpisode.title,
        description: fetchedEpisode.description,
        keywords: fetchedEpisode.keywords || [],
        selectedTagIds: fetchedEpisode.tags?.map(tag => tag.id) || []
      })
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load episode'
      setError(errorMessage)
      toast.error('Failed to load episode')
    } finally {
      setIsLoading(false)
      setIsLoadingTags(false)
    }
  }

  const handleSave = async () => {
    if (!episode) return

    try {
      setIsSaving(true)
      const updatedEpisode = await episodeApi.update(episode.id, {
        title: editForm.title,
        description: editForm.description,
        keywords: editForm.keywords,
        tags: editForm.selectedTagIds
      })
      setEpisode(updatedEpisode)
      setIsEditing(false)
      toast.success('Episode updated successfully!')
    } catch (err: unknown) {
      console.error('Failed to update episode:', err)
      toast.error('Failed to update episode')
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !editForm.keywords.includes(newKeyword.trim())) {
      setEditForm(prev => ({
        ...prev,
        keywords: [...prev.keywords, newKeyword.trim()]
      }))
      setNewKeyword('')
    }
  }

  const handleRemoveKeyword = (keyword: string) => {
    setEditForm(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }))
  }

  const handleToggleTag = (tagId: number) => {
    setEditForm(prev => ({
      ...prev,
      selectedTagIds: prev.selectedTagIds.includes(tagId)
        ? prev.selectedTagIds.filter(id => id !== tagId)
        : [...prev.selectedTagIds, tagId]
    }))
  }

  const getTagById = (tagId: number) => {
    return availableTags.find(tag => tag.id === tagId)
  }

  const handleDeleteEpisode = async () => {
    if (!episode) return

    if (confirm(`Are you sure you want to delete "${episode.title}"? This action cannot be undone.`)) {
      try {
        await episodeApi.delete(episode.id)
        toast.success('Episode deleted successfully')
        router.back()
      } catch (err: unknown) {
        console.error('Delete error:', err)
        toast.error('Failed to delete episode')
      }
    }
  }

  const handleFavoriteToggle = () => {
    if (!episode) return

    if (episode.is_favorited) {
      unfavoriteMutation.mutate(episode.id, {
        onSuccess: () => {
          // Update local state immediately for better UX
          setEpisode(prev => prev ? { ...prev, is_favorited: false } : null)
        }
      })
    } else {
      favoriteMutation.mutate(episode.id, {
        onSuccess: () => {
          // Update local state immediately for better UX
          setEpisode(prev => prev ? { ...prev, is_favorited: true } : null)
        }
      })
    }
  }

  const handleDownloadAudio = () => {
    if (!episode || !episode.audio_file_path) {
      toast.error('Audio file not available')
      return
    }

    // Use video_id-based URL for YouTube episodes, integer ID for uploaded episodes
    // Audio format is indicated via HTTP Content-Type headers
    const downloadUrl = episode.video_id
      ? `${getApiBaseUrl()}/v1/media/episodes/by-video-id/${episode.video_id}/audio`
      : `${getApiBaseUrl()}/v1/media/episodes/${episode.id}/audio`

    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${episode.title}.mp3`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleViewOriginalVideo = () => {
    if (episode && episode.video_url) {
      window.open(episode.video_url, '_blank', 'noopener,noreferrer')
    } else {
      toast.error('Original video URL not available')
    }
  }

  const handleRedownload = async () => {
    if (!episode) {
      toast.error('Episode not available')
      return
    }

    try {
      toast.info('Re-downloading audio...', {
        description: 'This may take a few minutes'
      })

      const response = await episodeApi.redownload(episode.id)

      toast.success('Re-download started successfully', {
        description: 'The episode will be reprocessed with improved audio quality'
      })

      // Refresh episode data to show updated status
      await fetchEpisode()

    } catch (error) {
      console.error('Failed to re-download episode:', error)
      toast.error('Failed to re-download audio', {
        description: 'Please try again later'
      })
    }
  }

  const getStatusColor = (status: EpisodeStatus) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200'
      case 'processing': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'failed': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Check if episode is from a local upload (not YouTube)
  const isUploadedEpisode = (episode: Episode) => {
    return episode.video_id?.startsWith('up_') &&
      !episode.thumbnail_url &&
      !episode.youtube_channel
  }

  // Check if episode has a valid thumbnail (YouTube episode)
  const hasValidThumbnail = (episode: Episode) => {
    return episode.thumbnail_url && episode.thumbnail_url.trim() !== ''
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </div>

        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-2/3" />
          <div className="h-4 bg-muted rounded w-1/2" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    )
  }

  if (error || !episode) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              <FileAudio className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <h3 className="text-lg font-semibold mb-2">Episode not found</h3>
              <p className="mb-4">{error || 'The episode you\'re looking for doesn\'t exist.'}</p>
              <Button onClick={loadEpisode}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Navigation Header */}
      <div className="flex items-center">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      {/* Episode Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex gap-6">
            {/* Episode Artwork */}
            <div className="flex-shrink-0">
              {hasValidThumbnail(episode) ? (
                // YouTube episode with thumbnail
                <div className="w-40 h-40 rounded-lg overflow-hidden">
                  <img
                    src={episode.thumbnail_url || ''}
                    alt={episode.title}
                    className="w-full h-full object-cover rounded-lg"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      target.nextElementSibling?.classList.remove('hidden')
                    }}
                  />
                  <FileAudio className="w-12 h-12 text-muted-foreground hidden" />
                </div>
              ) : isUploadedEpisode(episode) ? (
                // Uploaded episode - show colorful gradient background
                <div
                  className="w-40 h-40 relative transition-all duration-300 hover:scale-105 rounded-lg overflow-hidden"
                  style={generateGradientStyle(episode.video_id || 'up_default')}
                >
                  {/* Episode title overlay at bottom */}
                  <div className="absolute bottom-3 left-3 right-3 bg-black/60 backdrop-blur-sm px-3 py-2 rounded text-white text-sm font-medium truncate shadow-lg border border-white/20">
                    {episode.title}
                  </div>

                  {/* Play icon in center */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Play className="w-12 h-12 text-white/95 drop-shadow-lg" />
                  </div>
                </div>
              ) : (
                // Fallback for episodes without thumbnails (should be rare)
                <div className="w-40 h-40 bg-muted rounded-lg flex items-center justify-center">
                  <FileAudio className="w-12 h-12 text-muted-foreground" />
                </div>
              )}
            </div>

            {/* Episode Info and Actions */}
            <div className="flex-1 min-w-0 flex flex-col justify-between">
              {/* Title and Description */}
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <h1 className="text-2xl font-bold tracking-tight leading-tight pr-4">
                    {episode.title}
                  </h1>
                  <div className="flex items-center gap-2">
                    {/* Play/Stop Button */}
                    <Button
                      size="icon"
                      onClick={() => {
                        if (playingEpisodeId === episode.id) {
                          stopEpisode()
                        } else {
                          playEpisode(episode)
                        }
                      }}
                      className="h-10 w-10 rounded-full"
                    >
                      {playingEpisodeId === episode.id ? (
                        <Square className="h-5 w-5" />
                      ) : (
                        <Play className="h-5 w-5" />
                      )}
                    </Button>

                    {/* Favorite Button */}
                    <Button
                      variant={episode.is_favorited ? "default" : "outline"}
                      size="icon"
                      className={cn(
                        "h-10 w-10 rounded-full",
                        episode.is_favorited && "bg-red-500 hover:bg-red-600 text-white"
                      )}
                      onClick={handleFavoriteToggle}
                    >
                      <Heart className={cn(
                        "h-5 w-5",
                        episode.is_favorited && "fill-current"
                      )} />
                    </Button>

                    {/* Actions Menu */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon" className="h-10 w-10 rounded-full">
                          <MoreVertical className="h-5 w-5" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setIsEditing(true)}
                          disabled={isEditing}
                        >
                          <Edit3 className="h-4 w-4 mr-2" />
                          Edit Episode
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={handleDownloadAudio}
                          disabled={!episode || !episode.audio_file_path}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download Audio
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={handleRedownload}
                          disabled={!episode || !episode.video_id}
                        >
                          <RefreshCcw className="h-4 w-4 mr-2" />
                          Re-download Audio
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={handleViewOriginalVideo}
                          disabled={!episode || !episode.video_url}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          View Original Video
                        </DropdownMenuItem>
                        {episode?.youtube_channel_url && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => setFollowModalOpen(true)}
                            >
                              <Youtube className="h-4 w-4 mr-2" />
                              Follow Channel
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={handleDeleteEpisode}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Episode
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>

                {/* Episode Meta */}
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(episode.publication_date)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDuration(episode.duration_seconds)}
                  </div>
                  <Badge className={cn("text-xs", getStatusColor(episode.status))}>
                    {episode.status}
                  </Badge>
                  {/* 🤖 Custom Language Badge - Only show if user requested a custom language */}
                  {episode.requested_language && episode.audio_language && (
                    <Badge className="text-xs bg-blue-600 text-white border-blue-700">
                      {episode.audio_language.toUpperCase()}
                    </Badge>
                  )}
                </div>

                {/* YouTube Channel Info */}
                {episode.youtube_channel && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Channel:</span>
                    {episode.youtube_channel_url ? (
                      <a
                        href={episode.youtube_channel_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {episode.youtube_channel}
                      </a>
                    ) : (
                      <span>{episode.youtube_channel}</span>
                    )}
                  </div>
                )}

                {/* Tags */}
                {episode.tags && episode.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2">
                    {episode.tags.map((tag) => (
                      <Badge
                        key={tag.id}
                        className="text-xs px-2 py-1"
                        style={{ backgroundColor: tag.color, color: '#fff' }}
                      >
                        {tag.name}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Description */}
                <p className="text-muted-foreground leading-relaxed">
                  {episode.description}
                </p>

                {/* Keywords from YouTube */}
                {episode.keywords && episode.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2">
                    <span className="text-xs text-muted-foreground font-medium">Keywords:</span>
                    {episode.keywords.map((keyword) => (
                      <Badge
                        key={keyword}
                        variant="outline"
                        className="text-xs px-2 py-1 bg-muted/20"
                      >
                        <Hash className="h-3 w-3 mr-1" />
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Form Modal */}
      {isEditing && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Edit Episode</CardTitle>
                <CardDescription>
                  Update episode title, description and keywords
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsEditing(false)
                    setEditForm({
                      title: episode.title,
                      description: episode.description,
                      keywords: episode.keywords || [],
                      selectedTagIds: episode.tags?.map(tag => tag.id) || []
                    })
                  }}
                  className="gap-2"
                >
                  <X className="h-4 w-4" />
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="gap-2"
                >
                  {isSaving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save Changes
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Episode Title</Label>
              <Input
                id="title"
                value={editForm.title}
                onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Episode title..."
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={editForm.description}
                onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                className="min-h-32"
                placeholder="Episode description..."
              />
            </div>

            {/* Tags */}
            <div className="space-y-3">
              <Label>Tags</Label>
              <div className="space-y-3">
                {/* Selected Tags Display */}
                {editForm.selectedTagIds.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {editForm.selectedTagIds.map((tagId) => {
                      const tag = getTagById(tagId)
                      return tag ? (
                        <Badge
                          key={tag.id}
                          className="gap-1"
                          style={{ backgroundColor: tag.color, color: '#fff' }}
                        >
                          {tag.name}
                          <button
                            onClick={() => handleToggleTag(tag.id)}
                            className="ml-1 hover:opacity-70"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ) : null
                    })}
                  </div>
                )}

                {/* Available Tags */}
                {!isLoadingTags && availableTags.length > 0 && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Available tags (click to toggle):</p>
                    <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                      {availableTags.map((tag) => {
                        const isSelected = editForm.selectedTagIds.includes(tag.id)
                        return (
                          <button
                            key={tag.id}
                            onClick={() => handleToggleTag(tag.id)}
                            className="transition-opacity hover:opacity-80"
                          >
                            <Badge
                              variant={isSelected ? "default" : "outline"}
                              className={cn(
                                "cursor-pointer",
                                isSelected && "opacity-50"
                              )}
                              style={isSelected ? {} : { borderColor: tag.color, color: tag.color }}
                            >
                              {tag.name}
                            </Badge>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {isLoadingTags && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading tags...
                  </div>
                )}
              </div>
            </div>

            {/* Keywords */}
            <div className="space-y-2">
              <Label>Keywords (from YouTube)</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {editForm.keywords.map((keyword) => (
                  <Badge key={keyword} variant="outline" className="gap-1 bg-muted/20">
                    <Hash className="h-3 w-3" />
                    {keyword}
                    <button
                      onClick={() => handleRemoveKeyword(keyword)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddKeyword()
                    }
                  }}
                  placeholder="Add keyword..."
                  className="flex-1"
                />
                <Button onClick={handleAddKeyword} size="icon" variant="outline">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Episode Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Video Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileAudio className="h-5 w-5" />
              Video Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Video ID</p>
                <p className="text-sm font-mono">{episode.video_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Duration</p>
                <p className="text-sm">{formatDuration(episode.duration_seconds)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <Badge className={cn("text-xs", getStatusColor(episode.status))}>
                  {episode.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Publication Date</p>
                <p className="text-sm">{formatDate(episode.publication_date)}</p>
              </div>
            </div>

            {/* View Original Video Button */}
            {/* {episode.video_id && (
              <div className="pt-2">
                <Button variant="outline" size="sm" className="w-full gap-2">
                  <ExternalLink className="h-4 w-4" />
                  View Original Video
                </Button>
              </div>
            )} */}
          </CardContent>
        </Card>

        {/* Download Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Download Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created</p>
                <p className="text-sm">{formatDate(episode.created_at)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Updated</p>
                <p className="text-sm">{formatDate(episode.updated_at)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Retry Count</p>
                <p className="text-sm">{episode.retry_count ?? 0}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Downloaded</p>
                <p className="text-sm">{formatDate(episode.download_date || episode.created_at)}</p>
              </div>
              {/* 🤖 Audio Track Language */}
              <div>
                <p className="text-sm font-medium text-muted-foreground">Audio Track</p>
                <p className="text-sm">
                  {episode.requested_language && episode.audio_language
                    ? episode.audio_language.toUpperCase()
                    : 'Default (Original)'}
                </p>
              </div>
              {/* 🤖 Audio Quality */}
              {episode.audio_quality && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Audio Quality</p>
                  <p className="text-sm capitalize">{episode.audio_quality}</p>
                </div>
              )}
            </div>

            {/* Download Audio Button */}
            {/* {episode.audio_file_path && (
              <div className="pt-2">
                <Button variant="outline" size="sm" className="w-full gap-2">
                  <Download className="h-4 w-4" />
                  Download Audio
                </Button>
              </div>
            )} */}
          </CardContent>
        </Card>
      </div>

      {/* Follow Channel Modal */}
      <FollowChannelModal
        open={followModalOpen}
        onOpenChange={setFollowModalOpen}
        defaultChannelUrl={episode?.youtube_channel_url || ''}
      />
    </div>
  )
}