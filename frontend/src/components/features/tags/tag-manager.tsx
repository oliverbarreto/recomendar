/**
 * TagManager component with inline editing, color picker, and CRUD operations
 */

'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  Tag as TagIcon,
  Plus,
  Edit3,
  Trash2,
  Check,
  X,
  MoreHorizontal,
  Palette,
  Hash,
  Users,
  Calendar,
  Search,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { Tag } from '@/types'

interface TagManagerProps {
  channelId: number
  tags: Tag[]
  onTagCreate?: (tag: Omit<Tag, 'id' | 'createdAt' | 'updatedAt'>) => Promise<Tag>
  onTagUpdate?: (id: number, updates: Partial<Tag>) => Promise<Tag>
  onTagDelete?: (id: number) => Promise<void>
  onRefresh?: () => void
  className?: string
  maxDisplayTags?: number
  showStatistics?: boolean
  isLoading?: boolean
}

interface EditingTag extends Partial<Tag> {
  isNew?: boolean
  originalId?: number
}

// Default color palette for tags
const DEFAULT_COLORS = [
  '#3B82F6', // Blue
  '#EF4444', // Red  
  '#10B981', // Green
  '#F59E0B', // Yellow
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#F97316', // Orange
  '#EC4899', // Pink
  '#6B7280', // Gray
  '#84CC16', // Lime
  '#F43F5E', // Rose
  '#14B8A6', // Teal
  '#A855F7', // Violet
  '#EAB308', // Amber
  '#22C55E', // Emerald
  '#6366F1', // Indigo
]

export function TagManager({
  channelId,
  tags,
  onTagCreate,
  onTagUpdate,
  onTagDelete,
  onRefresh,
  className,
  maxDisplayTags,
  showStatistics = true,
  isLoading = false
}: TagManagerProps) {
  const [editingTag, setEditingTag] = useState<EditingTag | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLORS[0])
  const [showColorPicker, setShowColorPicker] = useState(false)
  
  const inputRef = useRef<HTMLInputElement>(null)
  const colorPickerRef = useRef<HTMLDivElement>(null)

  // Filter tags based on search
  const filteredTags = tags.filter(tag => 
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const displayTags = maxDisplayTags 
    ? filteredTags.slice(0, maxDisplayTags)
    : filteredTags

  // Handle clicking outside color picker
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (colorPickerRef.current && !colorPickerRef.current.contains(event.target as Node)) {
        setShowColorPicker(false)
      }
    }

    if (showColorPicker) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showColorPicker])

  // Focus input when editing starts
  useEffect(() => {
    if (editingTag && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingTag])

  const handleStartEdit = useCallback((tag: Tag) => {
    setEditingTag({ ...tag, originalId: tag.id })
    setSelectedColor(tag.color)
  }, [])

  const handleStartCreate = useCallback(() => {
    setEditingTag({
      isNew: true,
      name: '',
      color: DEFAULT_COLORS[0],
      channelId
    })
    setSelectedColor(DEFAULT_COLORS[0])
  }, [channelId])

  const handleCancelEdit = useCallback(() => {
    setEditingTag(null)
    setSelectedColor(DEFAULT_COLORS[0])
    setShowColorPicker(false)
  }, [])

  const handleSave = useCallback(async () => {
    if (!editingTag || !editingTag.name?.trim()) {
      toast.error('Tag name is required')
      return
    }

    try {
      if (editingTag.isNew) {
        // Create new tag
        if (onTagCreate) {
          await onTagCreate({
            name: editingTag.name.trim(),
            color: selectedColor,
            channelId
          })
          toast.success('Tag created successfully')
        }
      } else if (editingTag.originalId) {
        // Update existing tag
        if (onTagUpdate) {
          await onTagUpdate(editingTag.originalId, {
            name: editingTag.name.trim(),
            color: selectedColor
          })
          toast.success('Tag updated successfully')
        }
      }
      
      handleCancelEdit()
      onRefresh?.()
    } catch (error) {
      console.error('Failed to save tag:', error)
      toast.error(editingTag.isNew ? 'Failed to create tag' : 'Failed to update tag')
    }
  }, [editingTag, selectedColor, channelId, onTagCreate, onTagUpdate, onRefresh, handleCancelEdit])

  const handleDelete = useCallback(async (tagId: number) => {
    if (!onTagDelete) return

    try {
      await onTagDelete(tagId)
      toast.success('Tag deleted successfully')
      onRefresh?.()
    } catch (error) {
      console.error('Failed to delete tag:', error)
      toast.error('Failed to delete tag')
    }
  }, [onTagDelete, onRefresh])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      handleCancelEdit()
    }
  }, [handleSave, handleCancelEdit])

  const getContrastTextColor = (backgroundColor: string) => {
    // Simple contrast calculation
    const hex = backgroundColor.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5 ? '#000000' : '#FFFFFF'
  }

  // Statistics calculation
  const stats = showStatistics ? {
    total: tags.length,
    used: tags.filter(tag => tag.usage_count && tag.usage_count > 0).length,
    unused: tags.filter(tag => !tag.usage_count || tag.usage_count === 0).length,
    mostUsed: tags
      .filter(tag => tag.usage_count && tag.usage_count > 0)
      .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
      .slice(0, 3)
  } : null

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5" />
            Tag Manager
          </CardTitle>

          <div className="flex items-center gap-2">
            <Button
              onClick={onRefresh}
              variant="outline"
              size="sm"
              disabled={isLoading}
              className="gap-1"
            >
              <RefreshCw className={cn('h-3 w-3', isLoading && 'animate-spin')} />
              Refresh
            </Button>

            <Button
              onClick={handleStartCreate}
              size="sm"
              className="gap-1"
              disabled={!!editingTag}
            >
              <Plus className="h-3 w-3" />
              New Tag
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-8 text-sm"
          />
        </div>

        {/* Statistics */}
        {showStatistics && stats && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <div className="font-semibold">{stats.total}</div>
              <div className="text-muted-foreground">Total</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-green-600">{stats.used}</div>
              <div className="text-muted-foreground">Used</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-muted-foreground">{stats.unused}</div>
              <div className="text-muted-foreground">Unused</div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {/* Editing Form */}
        {editingTag && (
          <div className="mb-4 p-3 border rounded-lg bg-muted/30">
            <div className="flex items-center justify-between mb-3">
              <Label className="text-sm font-medium">
                {editingTag.isNew ? 'Create New Tag' : 'Edit Tag'}
              </Label>
              <div className="flex gap-1">
                <Button
                  onClick={handleSave}
                  size="sm"
                  className="h-7 w-7 p-0"
                  disabled={!editingTag.name?.trim()}
                >
                  <Check className="h-3 w-3" />
                </Button>
                <Button
                  onClick={handleCancelEdit}
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              {/* Name Input */}
              <div>
                <Input
                  ref={inputRef}
                  value={editingTag.name || ''}
                  onChange={(e) => setEditingTag(prev => prev ? { ...prev, name: e.target.value } : null)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter tag name..."
                  className="h-8 text-sm"
                  maxLength={50}
                />
              </div>

              {/* Color Picker */}
              <div className="relative">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setShowColorPicker(!showColorPicker)}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0"
                    style={{ backgroundColor: selectedColor }}
                  >
                    <Palette className="h-3 w-3" style={{ color: getContrastTextColor(selectedColor) }} />
                  </Button>
                  <span className="text-sm text-muted-foreground">{selectedColor}</span>
                </div>

                {showColorPicker && (
                  <div
                    ref={colorPickerRef}
                    className="absolute top-full left-0 mt-1 p-2 bg-popover border rounded-md shadow-md z-50 grid grid-cols-4 gap-1"
                  >
                    {DEFAULT_COLORS.map(color => (
                      <button
                        key={color}
                        onClick={() => {
                          setSelectedColor(color)
                          setShowColorPicker(false)
                        }}
                        className={cn(
                          'w-8 h-8 rounded border-2 transition-all',
                          selectedColor === color 
                            ? 'border-foreground scale-110' 
                            : 'border-transparent hover:border-foreground/50'
                        )}
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Preview */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Preview:</span>
                <Badge 
                  style={{ 
                    backgroundColor: selectedColor, 
                    color: getContrastTextColor(selectedColor),
                    borderColor: selectedColor
                  }}
                >
                  {editingTag.name || 'Tag Name'}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Tags List */}
        <div className="space-y-2">
          {displayTags.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchQuery ? (
                <div>
                  <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No tags found matching &quot;{searchQuery}&quot;</p>
                </div>
              ) : (
                <div>
                  <TagIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No tags created yet</p>
                  <p className="text-sm">Create your first tag to get started</p>
                </div>
              )}
            </div>
          ) : (
            displayTags.map(tag => (
              <div
                key={tag.id}
                className="flex items-center justify-between p-2 border rounded hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <Badge 
                    style={{ 
                      backgroundColor: tag.color, 
                      color: getContrastTextColor(tag.color),
                      borderColor: tag.color
                    }}
                    className="shrink-0"
                  >
                    {tag.name}
                  </Badge>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground min-w-0">
                    <div className="flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      <span>{tag.usage_count || 0} episodes</span>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <time>
                        {new Date(tag.updatedAt).toLocaleDateString()}
                      </time>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    onClick={() => handleStartEdit(tag)}
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    disabled={!!editingTag}
                  >
                    <Edit3 className="h-3 w-3" />
                  </Button>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        disabled={!!editingTag}
                      >
                        <MoreHorizontal className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleStartEdit(tag)}>
                        <Edit3 className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={() => handleDelete(tag.id)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Show more indicator */}
        {maxDisplayTags && filteredTags.length > maxDisplayTags && (
          <div className="mt-4 text-center">
            <p className="text-sm text-muted-foreground">
              Showing {maxDisplayTags} of {filteredTags.length} tags
            </p>
          </div>
        )}

        {/* Most used tags */}
        {showStatistics && stats && stats.mostUsed.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium mb-2 flex items-center gap-1">
              <Users className="h-3 w-3" />
              Most Used Tags
            </h4>
            <div className="flex flex-wrap gap-1">
              {stats.mostUsed.map(tag => (
                <Badge 
                  key={tag.id}
                  variant="secondary"
                  className="text-xs"
                >
                  {tag.name} ({tag.usage_count})
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}