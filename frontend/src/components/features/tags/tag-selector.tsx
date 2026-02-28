/**
 * TagSelector component with multi-select functionality for episode tagging
 */

'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  Tag as TagIcon,
  X,
  Search,
  Check,
  Plus,
  ChevronDown,
  ChevronUp,
  Hash
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { useTagSuggestions } from '@/hooks/use-search'
import { Tag, TagSuggestion } from '@/types'

interface TagSelectorProps {
  channelId: number
  selectedTags: Tag[]
  onTagsChange: (tags: Tag[]) => void
  placeholder?: string
  label?: string
  className?: string
  disabled?: boolean
  maxTags?: number
  allowCreate?: boolean
  onCreateTag?: (tagName: string) => Promise<Tag>
  size?: 'sm' | 'default' | 'lg'
}

const sizeStyles = {
  sm: {
    input: 'h-8 text-sm',
    badge: 'h-5 text-xs',
    dropdown: 'text-sm',
    button: 'h-6 w-6 p-0'
  },
  default: {
    input: 'h-10',
    badge: 'h-6 text-sm',
    dropdown: 'text-sm',
    button: 'h-7 w-7 p-0'
  },
  lg: {
    input: 'h-12 text-base',
    badge: 'h-7',
    dropdown: 'text-base',
    button: 'h-8 w-8 p-0'
  }
}

export function TagSelector({
  channelId,
  selectedTags,
  onTagsChange,
  placeholder = 'Search and select tags...',
  label,
  className,
  disabled = false,
  maxTags,
  allowCreate = false,
  onCreateTag,
  size = 'default'
}: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const styles = sizeStyles[size]

  // Get tag suggestions based on search query
  const { data: tagSuggestions, isLoading } = useTagSuggestions(
    channelId,
    searchQuery,
    20
  )

  // Filter out already selected tags
  const availableTags = (tagSuggestions?.suggestions || []).filter(
    suggestion => !selectedTags.some(selected => selected.id === suggestion.id)
  )

  // Handle clicking outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setHighlightedIndex(-1)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Reset highlighted index when suggestions change
  useEffect(() => {
    setHighlightedIndex(-1)
  }, [availableTags])

  const handleTagSelect = useCallback(async (suggestion: TagSuggestion) => {
    if (maxTags && selectedTags.length >= maxTags) {
      return
    }

    const newTag: Tag = {
      id: suggestion.id,
      channelId,
      name: suggestion.name,
      color: suggestion.color,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      usage_count: suggestion.usage_count
    }

    onTagsChange([...selectedTags, newTag])
    setSearchQuery('')
    setIsOpen(false)
    inputRef.current?.focus()
  }, [channelId, selectedTags, onTagsChange, maxTags])

  const handleTagRemove = useCallback((tagId: number) => {
    onTagsChange(selectedTags.filter(tag => tag.id !== tagId))
  }, [selectedTags, onTagsChange])

  const handleCreateTag = useCallback(async () => {
    if (!allowCreate || !onCreateTag || !searchQuery.trim()) {
      return
    }

    try {
      const newTag = await onCreateTag(searchQuery.trim())
      onTagsChange([...selectedTags, newTag])
      setSearchQuery('')
      setIsOpen(false)
      inputRef.current?.focus()
    } catch (error) {
      console.error('Failed to create tag:', error)
    }
  }, [allowCreate, onCreateTag, searchQuery, selectedTags, onTagsChange])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (disabled) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setIsOpen(true)
        setHighlightedIndex(prev => 
          prev < availableTags.length - 1 ? prev + 1 : 0
        )
        break

      case 'ArrowUp':
        e.preventDefault()
        setIsOpen(true)
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : availableTags.length - 1
        )
        break

      case 'Enter':
        e.preventDefault()
        if (isOpen) {
          if (highlightedIndex >= 0 && highlightedIndex < availableTags.length) {
            handleTagSelect(availableTags[highlightedIndex])
          } else if (allowCreate && searchQuery.trim()) {
            handleCreateTag()
          }
        } else {
          setIsOpen(true)
        }
        break

      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setHighlightedIndex(-1)
        setSearchQuery('')
        break

      case 'Backspace':
        if (searchQuery === '' && selectedTags.length > 0) {
          e.preventDefault()
          handleTagRemove(selectedTags[selectedTags.length - 1].id)
        }
        break
    }
  }, [
    disabled,
    isOpen,
    availableTags,
    highlightedIndex,
    searchQuery,
    selectedTags,
    allowCreate,
    handleTagSelect,
    handleTagRemove,
    handleCreateTag
  ])

  const handleInputFocus = useCallback(() => {
    if (!disabled) {
      setIsOpen(true)
    }
  }, [disabled])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchQuery(value)
    setIsOpen(true)
    setHighlightedIndex(-1)
  }, [])

  const getContrastTextColor = (backgroundColor: string) => {
    const hex = backgroundColor.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5 ? '#000000' : '#FFFFFF'
  }

  const canAddMore = !maxTags || selectedTags.length < maxTags
  const hasCreateOption = allowCreate && searchQuery.trim() && 
    !availableTags.some(tag => tag.name.toLowerCase() === searchQuery.toLowerCase().trim())

  return (
    <div className={cn('w-full', className)}>
      {label && (
        <Label className="text-sm font-medium mb-2 block">
          {label}
          {maxTags && (
            <span className="text-muted-foreground ml-1">
              ({selectedTags.length}/{maxTags})
            </span>
          )}
        </Label>
      )}

      <div ref={containerRef} className="relative">
        {/* Selected Tags Display */}
        <div 
          className={cn(
            'flex flex-wrap gap-1 p-2 min-h-10 border border-input rounded-md bg-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 transition-all',
            disabled && 'opacity-50 cursor-not-allowed',
            !canAddMore && 'cursor-not-allowed'
          )}
          onClick={() => !disabled && canAddMore && inputRef.current?.focus()}
        >
          {selectedTags.map(tag => (
            <Badge
              key={tag.id}
              className={cn(
                'gap-1 pr-1',
                styles.badge
              )}
              style={{
                backgroundColor: tag.color,
                color: getContrastTextColor(tag.color),
                borderColor: tag.color
              }}
            >
              {tag.name}
              {!disabled && (
                <Button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleTagRemove(tag.id)
                  }}
                  className={cn(
                    'hover:bg-background/20 rounded-full',
                    styles.button
                  )}
                  style={{ color: getContrastTextColor(tag.color) }}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </Badge>
          ))}

          {canAddMore && (
            <Input
              ref={inputRef}
              value={searchQuery}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={handleInputFocus}
              placeholder={selectedTags.length === 0 ? placeholder : ''}
              disabled={disabled}
              className={cn(
                'border-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 p-0 h-auto min-w-32 flex-1',
                styles.input,
                selectedTags.length === 0 && 'min-w-full'
              )}
            />
          )}

          <Button
            onClick={() => !disabled && setIsOpen(!isOpen)}
            variant="ghost"
            size="sm"
            disabled={disabled}
            className={cn(
              'shrink-0 self-center',
              styles.button
            )}
          >
            {isOpen ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </Button>
        </div>

        {/* Dropdown */}
        {isOpen && !disabled && (
          <div
            ref={dropdownRef}
            className={cn(
              'absolute top-full left-0 right-0 z-50 mt-1 bg-popover border rounded-md shadow-md max-h-60 overflow-y-auto',
              styles.dropdown
            )}
          >
            {isLoading ? (
              <div className="p-3 text-center text-muted-foreground">
                Loading tags...
              </div>
            ) : (
              <div className="py-1">
                {/* Create new tag option */}
                {hasCreateOption && (
                  <button
                    onClick={handleCreateTag}
                    className={cn(
                      'flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-accent hover:text-accent-foreground',
                      highlightedIndex === -1 && 'bg-accent text-accent-foreground'
                    )}
                  >
                    <Plus className="h-4 w-4 text-primary" />
                    <span>Create &quot;{searchQuery.trim()}&quot;</span>
                  </button>
                )}

                {/* Available tags */}
                {availableTags.length > 0 ? (
                  availableTags.map((suggestion, index) => (
                    <button
                      key={suggestion.id}
                      onClick={() => handleTagSelect(suggestion)}
                      className={cn(
                        'flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-accent hover:text-accent-foreground',
                        highlightedIndex === index && 'bg-accent text-accent-foreground'
                      )}
                    >
                      <div 
                        className="w-3 h-3 rounded-full border"
                        style={{ backgroundColor: suggestion.color }}
                      />
                      <span className="flex-1 truncate">{suggestion.name}</span>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Hash className="h-3 w-3" />
                        <span>{suggestion.usage_count}</span>
                      </div>
                    </button>
                  ))
                ) : !hasCreateOption && searchQuery ? (
                  <div className="p-3 text-center text-muted-foreground">
                    No tags found for &quot;{searchQuery}&quot;
                  </div>
                ) : !searchQuery ? (
                  <div className="p-3 text-center text-muted-foreground">
                    Type to search for tags
                  </div>
                ) : null}

                {availableTags.length === 0 && !hasCreateOption && !searchQuery && (
                  <div className="p-3 text-center text-muted-foreground">
                    No tags available
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Help text */}
      {maxTags && selectedTags.length >= maxTags && (
        <p className="text-xs text-muted-foreground mt-1">
          Maximum of {maxTags} tags allowed
        </p>
      )}
    </div>
  )
}