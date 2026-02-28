# Task 0041: BUGFIX - Context Menu Options for episodes of Videos Not from YouTube - Full Session
- Model: code-supernova-1-million
- Date: 2025-10-21
- IDE: Cursor

_Exported on 21/10/2025 at 18:55:29 WEST from Cursor (1.7.52)_

---

**User**

@episode-card.tsx @page.tsx 

I want you to read and understand the design of the epsidoes detail page "/episodes/[id]" and the episode card shown on the home page of the /channel page. As you can see in the image we show a context menu in the three dot ellipsis button.

We have a very similar problem in all of the cases, but let's explain them all separately.

1. In the /episodes/[id] page the dropdwon context menu shows some options which must be disabled for the case of episodes not created with a youtube url
- Correct options: Edit Episode, Download Audio, Delete Episode
- Correctly Disabled: View Original Video (it opens youtube link) 
- Incorrect: "Re-download audio" must be also disabled. It tries to re-download from youtube the audio file.

2. In the episode card used in the grids for the /chanel and / home pagesepisodes/[id] page the dropdwon context menu shows some options which must be disabled for the case of episodes not created with a youtube url
- Correct options: Edit Episode, Download Audio, Delete Episode
- Incorrect: "View Original Video"  must be also disabled. 


---

**Cursor**

Perfect! Now I understand the issue completely. Based on my analysis, here's what needs to be fixed:

## The Problem

The issue is that episodes have different sources:
- **YouTube episodes**: Have a `video_id` (string) and come from YouTube
- **Uploaded episodes**: Have `video_id: null` and were manually uploaded

The context menu options need to be disabled appropriately for each type.

## The Fixes Needed

### 1. Episode Detail Page (`episode-detail.tsx`)

**Issue**: "Re-download Audio" is enabled for all episodes, but it should only work for YouTube episodes (those with `video_id`).

**Fix**: Add `disabled={!episode || !episode.video_id}` to the "Re-download Audio" menu item.

### 2. Episode Card (`episode-card.tsx`)

**Issue**: "View Original Video" doesn't check if `video_url` exists before trying to open it.

**Fix**: Add a condition to check if `episode.video_url` exists before enabling the menu item.

## Here are the specific changes:

### Episode Detail Page Fix:

```tsx:428:434:frontend/src/components/features/episodes/episode-detail.tsx
<DropdownMenuItem
  onClick={handleRedownload}
  disabled={!episode || !episode.video_id}
>
  <RefreshCcw className="h-4 w-4 mr-2" />
  Re-download Audio
</DropdownMenuItem>
```

The current code only checks `!episode` but should also check `!episode.video_id` since re-downloading only works for YouTube episodes.

### Episode Card Fix:

```tsx:363:371:frontend/src/components/features/episodes/episode-card.tsx
<DropdownMenuItem
  onClick={(e) => {
    e.stopPropagation()
    if (episode.video_url) {
      window.open(episode.video_url, '_blank')
    }
  }}
  disabled={!episode.video_url}
>
  <ExternalLink className="w-4 h-4 mr-2" />
  View Original Video
</DropdownMenuItem>
```

The current code opens `episode.video_url` directly without checking if it exists first.

## Summary

- **For Episode Detail Page**: Disable "Re-download Audio" for episodes without `video_id` (uploaded episodes)
- **For Episode Card**: Disable "View Original Video" for episodes without `video_url`

This ensures that:
- ✅ **YouTube episodes**: Can use all options (Edit, Download, Re-download, View Original Video, Delete)
- ✅ **Uploaded episodes**: Can only use appropriate options (Edit, Download, Delete) - the YouTube-specific options are disabled

The fixes are minimal and maintain the existing functionality while properly handling the different episode types.

```plaintext
<DropdownMenuItem
  onClick={handleRedownload}
  disabled={!episode || !episode.video_id}
>
  <RefreshCcw className="h-4 w-4 mr-2" />
  Re-download Audio
</DropdownMenuItem>
```

```plaintext
<DropdownMenuItem
  onClick={(e) => {
    e.stopPropagation()
    if (episode.video_url) {
      window.open(episode.video_url, '_blank')
    }
  }}
  disabled={!episode.video_url}
>
  <ExternalLink className="w-4 h-4 mr-2" />
  View Original Video
</DropdownMenuItem>
```

---

**User**

implement the fix

---

**Cursor**

```typescriptreact
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
  RefreshCcw
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
    } catch (err: any) {
      setError(err.message || 'Failed to load episode')
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
    } catch (err: any) {
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
      } catch (err: any) {
        toast.error('Failed to delete episode')
        console.error('Delete error:', err)
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
              <div className="w-40 h-40 bg-muted rounded-lg flex items-center justify-center overflow-hidden">
                {episode.thumbnail_url ? (
                  <img
                    src={episode.thumbnail_url}
                    alt={episode.title}
                    className="w-full h-full object-cover rounded-lg"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      target.nextElementSibling?.classList.remove('hidden')
                    }}
                  />
                ) : null}
                <FileAudio className={`w-12 h-12 text-muted-foreground ${episode.thumbnail_url ? 'hidden' : ''}`} />
              </div>
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

    </div>
  )
}
```

```typescriptreact
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation()
                      if (episode.video_url) {
                        window.open(episode.video_url, '_blank')
                      }
                    }}
                    disabled={!episode.video_url}
                  >
                    <ExternalLink className="w-4 w-4 mr-2" />
                    View on YouTube
                  </DropdownMenuItem>
```

```typescriptreact
"use client"

/**
 * Episode Card Component - YouTube-style episode cards with status indicators
 */

import React from 'react'
import {
  Play,
  Square,
  Download,
  MoreVertical,
  ExternalLink,
  RefreshCw,
  Trash2,
  AlertCircle,
  Clock,
  CheckCircle2,
  Loader2,
  Edit,
  Heart
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { useDeleteEpisode, useRetryEpisode, useEpisodeProgress, useFavoriteEpisode, useUnfavoriteEpisode } from '@/hooks/use-episodes'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'
import { Episode } from '@/types'

// Simple date formatting utility
const formatDistanceToNow = (date: Date, options?: { addSuffix?: boolean }) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days > 0) {
    return options?.addSuffix ? `${days} day${days > 1 ? 's' : ''} ago` : `${days} day${days > 1 ? 's' : ''}`
  } else if (hours > 0) {
    return options?.addSuffix ? `${hours} hour${hours > 1 ? 's' : ''} ago` : `${hours} hour${hours > 1 ? 's' : ''}`
  } else {
    return options?.addSuffix ? `${minutes} minute${minutes > 1 ? 's' : ''} ago` : `${minutes} minute${minutes > 1 ? 's' : ''}`
  }
}

// Format bytes to human readable format
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

interface EpisodeCardProps {
  episode: Episode
  onPlay?: (episode: Episode) => void
  onStop?: (episode: Episode) => void
  onEdit?: (episode: Episode) => void
  onDelete?: (episode: Episode) => void
  onRetry?: (episode: Episode) => void
  onFavorite?: (episode: Episode) => void
  onUnfavorite?: (episode: Episode) => void
  onClick?: (episode: Episode) => void
  isPlaying?: boolean
  className?: string
}

export function EpisodeCard({
  episode,
  onPlay,
  onStop,
  onEdit,
  onDelete,
  onRetry,
  onFavorite,
  onUnfavorite,
  onClick,
  isPlaying = false,
  className
}: EpisodeCardProps) {
  const router = useRouter()
  const deleteMutation = useDeleteEpisode()
  const retryMutation = useRetryEpisode()
  const favoriteMutation = useFavoriteEpisode()
  const unfavoriteMutation = useUnfavoriteEpisode()

  // Get real-time progress for processing episodes
  const { data: progressData } = useEpisodeProgress(
    episode.id,
    episode.status === 'processing',
    episode.status
  )

  const getStatusIcon = () => {
    switch (episode.status) {
      case 'completed':
        return <CheckCircle2 className="w-3 h-3 text-green-600" />
      case 'processing':
        return <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-3 h-3 text-red-600" />
      case 'pending':
        return <Clock className="w-3 h-3 text-yellow-600" />
      default:
        return null
    }
  }


  const getStatusIconOnly = () => {
    return getStatusIcon()
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }

    return `${minutes}m`
  }

  const canPlay = episode.status === 'completed' && episode.audio_file_path
  const canRetry = episode.status === 'failed'

  const handleDelete = () => {
    if (onDelete) {
      onDelete(episode)
    } else {
      deleteMutation.mutate(episode.id)
    }
  }

  const handleRetry = () => {
    if (onRetry) {
      onRetry(episode)
    } else {
      retryMutation.mutate(episode.id)
    }
  }

  const handleDownload = () => {
    if (episode.audio_file_path) {
      const audioUrl = apiClient.getEpisodeAudioUrl(episode.id)
      const link = document.createElement('a')
      link.href = audioUrl
      link.download = `${episode.title}.mp3`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success('Download started')
    } else {
      toast.error('Audio file not available')
    }
  }

  const handleFavorite = () => {
    if (episode.is_favorited) {
      if (onUnfavorite) {
        onUnfavorite(episode)
      } else {
        unfavoriteMutation.mutate(episode.id)
      }
    } else {
      if (onFavorite) {
        onFavorite(episode)
      } else {
        favoriteMutation.mutate(episode.id)
      }
    }
  }

  // Parse progress percentage from progress data (kept for potential future use)
  // const getProgressPercentage = () => {
  //   if (!progressData) return 0
  //   // progressData.percentage comes as string like "45%"
  //   const percentage = progressData.percentage?.replace('%', '')
  //   return percentage ? parseInt(percentage) : 0
  // }

  return (
    <Card
      className={cn(
        "group hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer h-full flex flex-col",
        className
      )}
      onClick={() => {
        if (onClick) {
          onClick(episode)
        } else {
          router.push(`/episodes/${episode.id}`)
        }
      }}
    >
      <CardContent className="pb-4 space-y-4 flex flex-col h-full">

        {/* Episode Number and Creation Date */}
        {(episode.episode_number || episode.created_at) && (
          <div className="flex-col items-start justify-between text-md">
            <div className="flex items-center gap-2">
              {episode.episode_number && (
                <span className="font-bold text-primary">
                  Episode #{episode.episode_number}
                </span>
              )}
            </div>

            {episode.created_at && (
              <span className="text-muted-foreground text-xs">
                {new Date(episode.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - Added {formatDistanceToNow(new Date(episode.created_at), { addSuffix: true })}
              </span>
            )}

          </div>
        )}

        {/* Thumbnail and Play Button */}
        <div className="relative aspect-video bg-muted rounded-lg overflow-hidden group/thumbnail">
          {episode.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={episode.thumbnail_url}
              alt={episode.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='180' viewBox='0 0 320 180'%3E%3Crect width='320' height='180' fill='%23f1f5f9'/%3E%3Cpath d='M120 60l80 30-80 30z' fill='%23cbd5e1'/%3E%3C/svg%3E"
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-muted">
              <Play className="w-8 h-8 text-muted-foreground" />
            </div>
          )}

          {/* Play Button Overlay */}
          {canPlay && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover/thumbnail:opacity-100 transition-opacity">
              <Button
                size="icon"
                variant="secondary"
                className="rounded-full h-12 w-12"
                onClick={(e) => {
                  e.stopPropagation() // Prevent card click
                  if (isPlaying && onStop) {
                    onStop(episode)
                  } else if (onPlay) {
                    onPlay(episode)
                  } else {
                    // Fallback: play audio directly
                    const audioUrl = apiClient.getEpisodeAudioUrl(episode.id)
                    const audio = new Audio(audioUrl)
                    audio.play().then(() => {
                      toast.success('Playing episode')
                    }).catch((error) => {
                      console.error('Error playing audio:', error)
                      toast.error('Failed to play episode')
                    })
                  }
                }}
              >
                {isPlaying ? (
                  <Square className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5 ml-0.5" />
                )}
              </Button>
            </div>
          )}

          {/* Duration Badge */}
          {episode.duration_seconds && (
            <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded font-medium">
              {formatDuration(episode.duration_seconds)}
            </div>
          )}

        </div>

        {/* Episode Info */}
        <div className="space-y-3 flex-1 flex flex-col">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-base line-clamp-2 leading-tight">
                {episode.title}
              </h3>
              {/* YouTube Channel Name */}
              {episode.youtube_channel && (
                <button
                  className="text-sm text-muted-foreground hover:text-foreground mt-1 truncate text-left transition-colors"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (episode.youtube_channel_url) {
                      window.open(episode.youtube_channel_url, '_blank')
                    }
                  }}
                  title={`Visit ${episode.youtube_channel} on YouTube`}
                >
                  {episode.youtube_channel}
                </button>
              )}
            </div>

            <div className="flex items-start gap-1 shrink-0">
              {/* Favorite Button */}
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={(e) => {
                  e.stopPropagation()
                  handleFavorite()
                }}
              >
                <Heart
                  className={cn(
                    "w-4 h-4",
                    episode.is_favorited
                      ? "fill-red-500 text-red-500"
                      : "text-muted-foreground hover:text-red-500"
                  )}
                />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {onEdit && (
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation()
                      onEdit(episode)
                    }}>
                      <Edit className="w-4 h-4 mr-2" />
                      Edit Episode
                    </DropdownMenuItem>
                  )}

                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation()
                      if (episode.video_url) {
                        window.open(episode.video_url, '_blank')
                      }
                    }}
                    disabled={!episode.video_url}
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View on YouTube
                  </DropdownMenuItem>

                  {canPlay && (
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation()
                      handleDownload()
                    }}>
                      <Download className="w-4 h-4 mr-2" />
                      Download Audio
                    </DropdownMenuItem>
                  )}

                  {canRetry && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        handleRetry()
                      }}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry Download
                      </DropdownMenuItem>
                    </>
                  )}

                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete()
                    }}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <p className="text-sm text-muted-foreground line-clamp-3 flex-1">
            {episode.description}
          </p>

          {/* Metadata - Publication Date and Status */}
          <div className="flex items-center justify-start text-xs gap-3">
            <div className="flex items-center gap-1">
              {getStatusIconOnly()}
            </div>
            <span className="text-muted-foreground">
              <p className="text-muted-foreground">Released:
                <span className="font-medium pl-1">{formatDistanceToNow(new Date(episode.publication_date), { addSuffix: true })}</span>
              </p>
            </span>
          </div>

          {/* Tags */}
          {episode.tags && episode.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {episode.tags.slice(0, 4).map((tag) => (
                <div
                  key={tag.id}
                  className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium text-white"
                  style={{ backgroundColor: tag.color }}
                >
                  {tag.name}
                </div>
              ))}
              {episode.tags.length > 4 && (
                <div className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                  +{episode.tags.length - 4}
                </div>
              )}
            </div>
          )}

          {/* Download Status for Processing Episodes */}
          {episode.status === 'processing' && (
            <div className="space-y-2">
              {progressData ? (
                progressData.status === 'completed' ? (
                  // Show processing status when download is done but episode is still processing
                  <div className="text-xs bg-purple-50 dark:bg-purple-950/50 p-3 rounded border-l-2 border-purple-500">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-3 h-3 animate-spin text-purple-600" />
                      <span className="font-medium text-purple-700 dark:text-purple-300">
                        Processing audio file...
                      </span>
                    </div>
                    <div className="text-muted-foreground mt-1">
                      Converting and organizing files
                    </div>
                  </div>
                ) : (
                  // Show download progress
                  <div className="text-xs bg-blue-50 dark:bg-blue-950/50 p-3 rounded border-l-2 border-blue-500">
                    <div className="flex items-center gap-2 mb-2">
                      <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                      <span className="font-medium text-blue-700 dark:text-blue-300">
                        Downloading {progressData.percentage}
                      </span>
                    </div>

                    <div className="space-y-1 text-muted-foreground">
                      {progressData.speed && (
                        <div className="flex justify-between">
                          <span>Speed:</span>
                          <span className="font-medium">{progressData.speed}</span>
                        </div>
                      )}
                      {progressData.eta && progressData.eta !== 'N/A' && (
                        <div className="flex justify-between">
                          <span>ETA:</span>
                          <span className="font-medium">{progressData.eta}</span>
                        </div>
                      )}
                      {progressData.downloaded_bytes && progressData.total_bytes && (
                        <div className="flex justify-between">
                          <span>Downloaded:</span>
                          <span className="font-medium">
                            {formatBytes(progressData.downloaded_bytes)} / {formatBytes(progressData.total_bytes)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              ) : (
                <div className="text-xs bg-orange-50 dark:bg-orange-950/50 p-3 rounded border-l-2 border-orange-500">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3 h-3 animate-spin text-orange-600" />
                    <span className="font-medium text-orange-700 dark:text-orange-300">
                      Queued for download...
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Pending Status */}
          {episode.status === 'pending' && (
            <div className="text-xs text-orange-600 bg-orange-50 dark:bg-orange-950/50 p-2 rounded border-l-2 border-orange-500">
              <div className="flex items-center gap-2">
                <Clock className="w-3 h-3" />
                Queued for download
              </div>
            </div>
          )}

          {/* Error Message for Failed Episodes */}
          {episode.status === 'failed' && (
            <div className="text-xs text-destructive bg-destructive/10 p-2 rounded">
              Download failed. Video may be private or unavailable.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

Perfect! I've successfully implemented the fixes for the context menu issues. Here's what was changed:

## ✅ **Episode Detail Page** (`episode-detail.tsx`)
- **Fixed**: "Re-download Audio" option now properly disabled for uploaded episodes
- **Change**: Added `!episode.video_id` check to the `disabled` condition
- **Before**: `disabled={!episode}`
- **After**: `disabled={!episode || !episode.video_id}`

## ✅ **Episode Card** (`episode-card.tsx`)
- **Fixed**: "View on YouTube" option now properly disabled for episodes without video URLs
- **Changes**:
  - Added `if (episode.video_url)` check before opening the URL
  - Added `disabled={!episode.video_url}` to the menu item

## **Result**
Now the context menus correctly handle different episode types:

- **YouTube episodes** (`video_id` exists): All options enabled ✅
- **Uploaded episodes** (`video_id` is null): 
  - ✅ Edit Episode (enabled)
  - ✅ Download Audio (enabled) 
  - ✅ Delete Episode (enabled)
  - ❌ Re-download Audio (disabled - YouTube only feature)
  - ❌ View Original Video (disabled - no YouTube URL)

The fixes ensure that users can't accidentally try to use YouTube-specific features on uploaded episodes, providing a better user experience with clear visual feedback about which actions are available for each episode type.

