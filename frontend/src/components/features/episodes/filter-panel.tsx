/**
 * FilterPanel component with collapsible sidebar for advanced episode filtering
 */

'use client'

import React, { useState, useCallback } from 'react'
import {
  Filter,
  ChevronDown,
  ChevronUp,
  X,
  Calendar,
  Clock,
  Tag as TagIcon,
  CheckCircle2,
  Circle,
  RotateCcw,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useAvailableFilters, useTagSuggestions } from '@/hooks/use-search'
import { SearchFilters, EpisodeStatus, Tag } from '@/types'

interface FilterPanelProps {
  channelId: number
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  isOpen?: boolean
  onToggle?: () => void
  className?: string
  showToggle?: boolean
}

interface FilterSectionProps {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
  icon?: React.ReactNode
}

function FilterSection({ title, children, defaultOpen = false, icon }: FilterSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-3 px-1 text-sm font-medium text-foreground hover:text-primary transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          {title}
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      
      {isOpen && (
        <div className="pb-3 px-1 space-y-3">
          {children}
        </div>
      )}
    </div>
  )
}

interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  count?: number
  disabled?: boolean
}

function Checkbox({ checked, onChange, label, count, disabled = false }: CheckboxProps) {
  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={cn(
        'flex items-center gap-2 w-full text-left text-sm py-1 px-2 rounded hover:bg-accent hover:text-accent-foreground transition-colors',
        disabled && 'opacity-50 cursor-not-allowed hover:bg-transparent hover:text-muted-foreground'
      )}
    >
      {checked ? (
        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
      ) : (
        <Circle className="h-4 w-4 text-muted-foreground shrink-0" />
      )}
      
      <span className="flex-1 truncate">{label}</span>
      
      {count !== undefined && (
        <span className="text-xs text-muted-foreground shrink-0">
          {count}
        </span>
      )}
    </button>
  )
}

export function FilterPanel({
  channelId,
  filters,
  onFiltersChange,
  isOpen = true,
  onToggle,
  className,
  showToggle = true,
}: FilterPanelProps) {
  const [tagQuery, setTagQuery] = useState('')
  
  // Get available filter options
  const { data: availableFilters = {} } = useAvailableFilters(channelId)
  const { data: tagSuggestions } = useTagSuggestions(channelId, tagQuery, 20)

  // Handle filter changes
  const updateFilters = useCallback((updates: Partial<SearchFilters>) => {
    onFiltersChange({ ...filters, ...updates })
  }, [filters, onFiltersChange])

  // Status filter handlers
  const handleStatusChange = useCallback((status: EpisodeStatus, checked: boolean) => {
    const currentStatuses = filters.status ? [filters.status] : []
    if (checked) {
      updateFilters({ status })
    } else {
      updateFilters({ status: undefined })
    }
  }, [filters.status, updateFilters])

  // Tag filter handlers
  const handleTagChange = useCallback((tagId: number, checked: boolean) => {
    const currentTags = filters.tags || []
    if (checked) {
      updateFilters({ tags: [...currentTags, tagId] })
    } else {
      updateFilters({ tags: currentTags.filter(id => id !== tagId) })
    }
  }, [filters.tags, updateFilters])

  const removeTag = useCallback((tagId: number) => {
    const currentTags = filters.tags || []
    updateFilters({ tags: currentTags.filter(id => id !== tagId) })
  }, [filters.tags, updateFilters])

  // Date range handlers
  const handleDateChange = useCallback((field: 'start_date' | 'end_date', value: string) => {
    updateFilters({ [field]: value || undefined })
  }, [updateFilters])

  // Duration range handlers
  const handleDurationChange = useCallback((field: 'min_duration' | 'max_duration', value: string) => {
    const numValue = value ? parseInt(value, 10) * 60 : undefined // Convert minutes to seconds
    updateFilters({ [field]: numValue })
  }, [updateFilters])

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    onFiltersChange({
      channel_id: filters.channel_id, // Keep channel_id
    })
    setTagQuery('')
  }, [filters.channel_id, onFiltersChange])

  // Count active filters
  const activeFiltersCount = Object.keys(filters).filter(key => 
    key !== 'channel_id' && filters[key as keyof SearchFilters] !== undefined && filters[key as keyof SearchFilters] !== ''
  ).length

  const hasActiveFilters = activeFiltersCount > 0

  if (!isOpen) {
    return showToggle ? (
      <Button
        onClick={onToggle}
        variant="outline"
        size="sm"
        className={cn('flex items-center gap-2', className)}
      >
        <Filter className="h-4 w-4" />
        Filters
        {hasActiveFilters && (
          <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 text-xs">
            {activeFiltersCount}
          </Badge>
        )}
      </Button>
    ) : null
  }

  return (
    <Card className={cn('w-80 p-0 h-fit', className)}>
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            <h3 className="font-semibold">Filters</h3>
            {hasActiveFilters && (
              <Badge variant="secondary" className="h-5 w-5 p-0 text-xs">
                {activeFiltersCount}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            {hasActiveFilters && (
              <Button
                onClick={clearAllFilters}
                variant="ghost"
                size="sm"
                className="h-8 px-2"
              >
                <RotateCcw className="h-3 w-3" />
                Clear
              </Button>
            )}
            
            {showToggle && onToggle && (
              <Button
                onClick={onToggle}
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
              >
                {isOpen ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </div>
        
        {/* Active tag filters */}
        {filters.tags && filters.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {filters.tags.map(tagId => {
              // Find tag name from suggestions or show ID
              const tagName = tagSuggestions?.suggestions.find(t => t.id === tagId)?.name || `Tag ${tagId}`
              return (
                <Badge
                  key={tagId}
                  variant="secondary"
                  className="text-xs h-6 pl-2 pr-1 gap-1"
                >
                  {tagName}
                  <Button
                    onClick={() => removeTag(tagId)}
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )
            })}
          </div>
        )}
      </div>

      <div className="overflow-y-auto max-h-96">
        {/* Episode Status */}
        <FilterSection
          title="Status"
          defaultOpen={!!filters.status}
          icon={<CheckCircle2 className="h-4 w-4" />}
        >
          {Object.values(EpisodeStatus).map(status => (
            <Checkbox
              key={status}
              checked={filters.status === status}
              onChange={(checked) => handleStatusChange(status, checked)}
              label={status.charAt(0).toUpperCase() + status.slice(1)}
              count={availableFilters.status?.find(s => s.value === status)?.count}
            />
          ))}
        </FilterSection>

        {/* Tags */}
        <FilterSection
          title="Tags"
          defaultOpen={!!(filters.tags && filters.tags.length > 0)}
          icon={<TagIcon className="h-4 w-4" />}
        >
          <div className="space-y-2">
            <Input
              placeholder="Search tags..."
              value={tagQuery}
              onChange={(e) => setTagQuery(e.target.value)}
              className="h-8 text-sm"
            />
            
            <div className="max-h-32 overflow-y-auto space-y-1">
              {tagSuggestions?.suggestions.map(tag => (
                <Checkbox
                  key={tag.id}
                  checked={filters.tags?.includes(tag.id) || false}
                  onChange={(checked) => handleTagChange(tag.id, checked)}
                  label={tag.name}
                  count={tag.usage_count}
                />
              ))}
            </div>
          </div>
        </FilterSection>

        {/* Date Range */}
        <FilterSection
          title="Date Range"
          defaultOpen={!!(filters.start_date || filters.end_date)}
          icon={<Calendar className="h-4 w-4" />}
        >
          <div className="space-y-3">
            <div>
              <Label htmlFor="start-date" className="text-xs text-muted-foreground">
                From
              </Label>
              <Input
                id="start-date"
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => handleDateChange('start_date', e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            
            <div>
              <Label htmlFor="end-date" className="text-xs text-muted-foreground">
                To
              </Label>
              <Input
                id="end-date"
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => handleDateChange('end_date', e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
        </FilterSection>

        {/* Duration Range */}
        <FilterSection
          title="Duration"
          defaultOpen={!!(filters.min_duration || filters.max_duration)}
          icon={<Clock className="h-4 w-4" />}
        >
          <div className="space-y-3">
            <div>
              <Label htmlFor="min-duration" className="text-xs text-muted-foreground">
                Min (minutes)
              </Label>
              <Input
                id="min-duration"
                type="number"
                placeholder="0"
                value={filters.min_duration ? Math.floor(filters.min_duration / 60) : ''}
                onChange={(e) => handleDurationChange('min_duration', e.target.value)}
                className="h-8 text-sm"
                min="0"
              />
            </div>
            
            <div>
              <Label htmlFor="max-duration" className="text-xs text-muted-foreground">
                Max (minutes)
              </Label>
              <Input
                id="max-duration"
                type="number"
                placeholder="∞"
                value={filters.max_duration ? Math.floor(filters.max_duration / 60) : ''}
                onChange={(e) => handleDurationChange('max_duration', e.target.value)}
                className="h-8 text-sm"
                min="0"
              />
            </div>
          </div>
        </FilterSection>
      </div>
    </Card>
  )
}