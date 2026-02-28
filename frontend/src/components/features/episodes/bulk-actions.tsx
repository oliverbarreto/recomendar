/**
 * BulkActions component for batch operations on episodes and tags
 */

'use client'

import React, { useState, useCallback } from 'react'
import {
  CheckSquare,
  Square,
  MoreHorizontal,
  Tag as TagIcon,
  Trash2,
  Copy,
  Archive,
  RefreshCw,
  Download,
  ChevronDown,
  X,
  AlertCircle,
  Users
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { TagSelector } from '../tags/tag-selector'
import { SearchResult, Tag } from '@/types'
import { toast } from 'sonner'

interface BulkActionsProps {
  episodes: SearchResult[]
  selectedEpisodes: number[]
  onSelectionChange: (selectedIds: number[]) => void
  onBulkTagAssign?: (episodeIds: number[], tagIds: number[]) => Promise<void>
  onBulkTagRemove?: (episodeIds: number[], tagIds: number[]) => Promise<void>
  onBulkDelete?: (episodeIds: number[]) => Promise<void>
  onBulkStatusChange?: (episodeIds: number[], status: string) => Promise<void>
  channelId: number
  className?: string
  disabled?: boolean
}

interface BulkTagActionProps {
  selectedCount: number
  channelId: number
  onTagAssign: (tagIds: number[]) => void
  onTagRemove: (tagIds: number[]) => void
  onClose: () => void
}

function BulkTagAction({ 
  selectedCount, 
  channelId, 
  onTagAssign, 
  onTagRemove, 
  onClose 
}: BulkTagActionProps) {
  const [selectedTags, setSelectedTags] = useState<Tag[]>([])
  const [action, setAction] = useState<'assign' | 'remove'>('assign')

  const handleApply = useCallback(() => {
    if (selectedTags.length === 0) {
      toast.error('Please select at least one tag')
      return
    }

    const tagIds = selectedTags.map(tag => tag.id)
    
    if (action === 'assign') {
      onTagAssign(tagIds)
    } else {
      onTagRemove(tagIds)
    }
    
    setSelectedTags([])
    onClose()
  }, [selectedTags, action, onTagAssign, onTagRemove, onClose])

  return (
    <Card className="p-4 border-2 border-primary/20 bg-primary/5">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TagIcon className="h-4 w-4" />
            <span className="font-medium">Bulk Tag Action</span>
            <Badge variant="secondary">{selectedCount} episodes</Badge>
          </div>
          
          <Button
            onClick={onClose}
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>

        {/* Action selector */}
        <div className="flex gap-2">
          <Button
            onClick={() => setAction('assign')}
            variant={action === 'assign' ? 'default' : 'outline'}
            size="sm"
          >
            Assign Tags
          </Button>
          <Button
            onClick={() => setAction('remove')}
            variant={action === 'remove' ? 'default' : 'outline'}
            size="sm"
          >
            Remove Tags
          </Button>
        </div>

        {/* Tag selector */}
        <TagSelector
          channelId={channelId}
          selectedTags={selectedTags}
          onTagsChange={setSelectedTags}
          placeholder={`Select tags to ${action}...`}
          allowCreate={action === 'assign'}
          size="sm"
        />

        {/* Actions */}
        <div className="flex gap-2 justify-end">
          <Button
            onClick={onClose}
            variant="outline"
            size="sm"
          >
            Cancel
          </Button>
          <Button
            onClick={handleApply}
            size="sm"
            disabled={selectedTags.length === 0}
          >
            {action === 'assign' ? 'Assign' : 'Remove'} Tags
          </Button>
        </div>
      </div>
    </Card>
  )
}

export function BulkActions({
  episodes,
  selectedEpisodes,
  onSelectionChange,
  onBulkTagAssign,
  onBulkTagRemove,
  onBulkDelete,
  onBulkStatusChange,
  channelId,
  className,
  disabled = false
}: BulkActionsProps) {
  const [showTagAction, setShowTagAction] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const selectedCount = selectedEpisodes.length
  const allSelected = episodes.length > 0 && selectedEpisodes.length === episodes.length
  const someSelected = selectedEpisodes.length > 0 && selectedEpisodes.length < episodes.length

  // Handle select all/none
  const handleSelectAll = useCallback(() => {
    if (disabled) return
    
    if (allSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(episodes.map(ep => ep.id))
    }
  }, [disabled, allSelected, episodes, onSelectionChange])

  // Handle individual episode selection
  const handleEpisodeToggle = useCallback((episodeId: number) => {
    if (disabled) return
    
    if (selectedEpisodes.includes(episodeId)) {
      onSelectionChange(selectedEpisodes.filter(id => id !== episodeId))
    } else {
      onSelectionChange([...selectedEpisodes, episodeId])
    }
  }, [disabled, selectedEpisodes, onSelectionChange])

  // Bulk tag operations
  const handleBulkTagAssign = useCallback(async (tagIds: number[]) => {
    if (!onBulkTagAssign || selectedCount === 0) return
    
    setIsLoading(true)
    try {
      await onBulkTagAssign(selectedEpisodes, tagIds)
      toast.success(`Tags assigned to ${selectedCount} episodes`)
      onSelectionChange([]) // Clear selection
    } catch (error) {
      console.error('Failed to assign tags:', error)
      toast.error('Failed to assign tags')
    } finally {
      setIsLoading(false)
    }
  }, [onBulkTagAssign, selectedCount, selectedEpisodes, onSelectionChange])

  const handleBulkTagRemove = useCallback(async (tagIds: number[]) => {
    if (!onBulkTagRemove || selectedCount === 0) return
    
    setIsLoading(true)
    try {
      await onBulkTagRemove(selectedEpisodes, tagIds)
      toast.success(`Tags removed from ${selectedCount} episodes`)
      onSelectionChange([]) // Clear selection
    } catch (error) {
      console.error('Failed to remove tags:', error)
      toast.error('Failed to remove tags')
    } finally {
      setIsLoading(false)
    }
  }, [onBulkTagRemove, selectedCount, selectedEpisodes, onSelectionChange])

  // Bulk delete
  const handleBulkDelete = useCallback(async () => {
    if (!onBulkDelete || selectedCount === 0) return
    
    if (!confirm(`Are you sure you want to delete ${selectedCount} episode${selectedCount > 1 ? 's' : ''}?`)) {
      return
    }
    
    setIsLoading(true)
    try {
      await onBulkDelete(selectedEpisodes)
      toast.success(`${selectedCount} episodes deleted`)
      onSelectionChange([]) // Clear selection
    } catch (error) {
      console.error('Failed to delete episodes:', error)
      toast.error('Failed to delete episodes')
    } finally {
      setIsLoading(false)
    }
  }, [onBulkDelete, selectedCount, selectedEpisodes, onSelectionChange])

  // Bulk status change
  const handleBulkStatusChange = useCallback(async (status: string) => {
    if (!onBulkStatusChange || selectedCount === 0) return
    
    setIsLoading(true)
    try {
      await onBulkStatusChange(selectedEpisodes, status)
      toast.success(`Status updated for ${selectedCount} episodes`)
      onSelectionChange([]) // Clear selection
    } catch (error) {
      console.error('Failed to update status:', error)
      toast.error('Failed to update status')
    } finally {
      setIsLoading(false)
    }
  }, [onBulkStatusChange, selectedCount, selectedEpisodes, onSelectionChange])

  if (episodes.length === 0) {
    return null
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Selection controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            onClick={handleSelectAll}
            variant="ghost"
            size="sm"
            disabled={disabled}
            className="gap-2"
          >
            {allSelected ? (
              <CheckSquare className="h-4 w-4" />
            ) : someSelected ? (
              <div className="h-4 w-4 border-2 border-primary bg-primary/50 rounded-sm flex items-center justify-center">
                <div className="h-1 w-2 bg-primary-foreground rounded-sm" />
              </div>
            ) : (
              <Square className="h-4 w-4" />
            )}
            {allSelected ? 'Deselect All' : 'Select All'}
          </Button>

          {selectedCount > 0 && (
            <Badge variant="secondary" className="gap-1">
              <Users className="h-3 w-3" />
              {selectedCount} selected
            </Badge>
          )}
        </div>

        {selectedCount > 0 && (
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setShowTagAction(true)}
              variant="outline"
              size="sm"
              disabled={disabled || isLoading}
              className="gap-1"
            >
              <TagIcon className="h-3 w-3" />
              Tags
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={disabled || isLoading}
                  className="gap-1"
                >
                  <MoreHorizontal className="h-3 w-3" />
                  Actions
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onBulkStatusChange && (
                  <DropdownMenuSub>
                    <DropdownMenuSubTrigger>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Change Status
                    </DropdownMenuSubTrigger>
                    <DropdownMenuSubContent>
                      <DropdownMenuItem onClick={() => handleBulkStatusChange('pending')}>
                        Pending
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleBulkStatusChange('processing')}>
                        Processing
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleBulkStatusChange('completed')}>
                        Completed
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleBulkStatusChange('failed')}>
                        Failed
                      </DropdownMenuItem>
                    </DropdownMenuSubContent>
                  </DropdownMenuSub>
                )}
                
                <DropdownMenuSeparator />
                
                {onBulkDelete && (
                  <DropdownMenuItem 
                    onClick={handleBulkDelete}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Episodes
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              onClick={() => onSelectionChange([])}
              variant="ghost"
              size="sm"
              disabled={disabled}
            >
              Clear
            </Button>
          </div>
        )}
      </div>

      {/* Tag action panel */}
      {showTagAction && selectedCount > 0 && (
        <BulkTagAction
          selectedCount={selectedCount}
          channelId={channelId}
          onTagAssign={handleBulkTagAssign}
          onTagRemove={handleBulkTagRemove}
          onClose={() => setShowTagAction(false)}
        />
      )}

      {/* Individual episode checkboxes (can be integrated with episode grid) */}
      <div className="grid gap-2">
        {episodes.map(episode => (
          <div
            key={episode.id}
            className="flex items-center gap-3 p-2 border rounded hover:bg-muted/50 transition-colors"
          >
            <Button
              onClick={() => handleEpisodeToggle(episode.id)}
              variant="ghost"
              size="sm"
              disabled={disabled}
              className="h-8 w-8 p-0"
            >
              {selectedEpisodes.includes(episode.id) ? (
                <CheckSquare className="h-4 w-4" />
              ) : (
                <Square className="h-4 w-4" />
              )}
            </Button>

            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium line-clamp-1">
                {episode.title}
              </h4>
              <p className="text-xs text-muted-foreground line-clamp-1">
                {episode.description}
              </p>
            </div>

            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Badge variant="outline" className="text-xs">
                {episode.status}
              </Badge>
              {episode.tags && episode.tags.length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {episode.tags.length} tags
                </Badge>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50">
          <div className="bg-background border rounded-lg p-6 flex items-center gap-3">
            <RefreshCw className="h-5 w-5 animate-spin" />
            <span>Processing bulk action...</span>
          </div>
        </div>
      )}
    </div>
  )
}