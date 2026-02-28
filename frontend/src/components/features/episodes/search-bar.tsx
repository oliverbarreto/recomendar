/**
 * SearchBar component with debounced input and suggestions
 */

'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Search, X, Clock, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useSearchSuggestions, useTrendingSearches } from '@/hooks/use-search'

interface SearchBarProps {
  channelId: number
  value?: string
  onChange?: (value: string) => void
  onSearch?: (query: string) => void
  placeholder?: string
  className?: string
  showSuggestions?: boolean
  disabled?: boolean
}

export function SearchBar({
  channelId,
  value = '',
  onChange,
  onSearch,
  placeholder = 'Search episodes...',
  className,
  showSuggestions = true,
  disabled = false,
}: SearchBarProps) {
  const [inputValue, setInputValue] = useState(value)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Get suggestions when user types
  const { data: suggestions, isLoading: suggestionsLoading } = useSearchSuggestions(
    channelId,
    inputValue,
    5
  )

  // Get trending searches for empty input
  const { data: trendingSearches } = useTrendingSearches(channelId, 8)

  // Handle input changes with debouncing
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setSelectedIndex(-1)
    setShowDropdown(showSuggestions && newValue.length > 0)
    
    onChange?.(newValue)
  }, [onChange, showSuggestions])

  // Handle search execution
  const executeSearch = useCallback((query: string) => {
    setInputValue(query)
    setShowDropdown(false)
    setSelectedIndex(-1)
    onSearch?.(query)
    inputRef.current?.blur()
  }, [onSearch])

  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim()) {
      executeSearch(inputValue.trim())
    }
  }, [inputValue, executeSearch])

  // Handle clear button
  const handleClear = useCallback(() => {
    setInputValue('')
    setShowDropdown(false)
    setSelectedIndex(-1)
    onChange?.('')
    inputRef.current?.focus()
  }, [onChange])

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showDropdown) return

    const items = getSuggestionItems()
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev < items.length - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : items.length - 1))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && items[selectedIndex]) {
          executeSearch(items[selectedIndex].query)
        } else if (inputValue.trim()) {
          executeSearch(inputValue.trim())
        }
        break
      case 'Escape':
        setShowDropdown(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
      case 'Tab':
        setShowDropdown(false)
        setSelectedIndex(-1)
        break
    }
  }, [showDropdown, selectedIndex, inputValue, executeSearch])

  // Handle suggestion click
  const handleSuggestionClick = useCallback((query: string) => {
    executeSearch(query)
  }, [executeSearch])

  // Handle input focus
  const handleFocus = useCallback(() => {
    if (showSuggestions && inputValue.length > 0) {
      setShowDropdown(true)
    }
  }, [showSuggestions, inputValue])

  // Handle input blur with delay to allow clicks
  const handleBlur = useCallback(() => {
    setTimeout(() => setShowDropdown(false), 150)
  }, [])

  // Get combined suggestion items
  const getSuggestionItems = useCallback(() => {
    if (!showSuggestions) return []
    
    if (inputValue.length > 0) {
      return suggestions || []
    } else {
      return trendingSearches || []
    }
  }, [showSuggestions, inputValue, suggestions, trendingSearches])

  // Sync external value changes
  React.useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value)
    }
  }, [value])

  const suggestionItems = getSuggestionItems()

  return (
    <div className={cn('relative w-full', className)}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          
          <Input
            ref={inputRef}
            type="search"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'pl-10 pr-10',
              showDropdown && 'rounded-b-none border-b-0'
            )}
            autoComplete="off"
            spellCheck={false}
          />
          
          {inputValue && !disabled && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleClear}
              className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </form>

      {/* Suggestions Dropdown */}
      {showDropdown && showSuggestions && (
        <div
          ref={dropdownRef}
          className={cn(
            'absolute top-full left-0 right-0 z-50 overflow-hidden rounded-md rounded-t-none border border-t-0 bg-popover text-popover-foreground shadow-md',
            'max-h-80 overflow-y-auto'
          )}
        >
          {suggestionsLoading ? (
            <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
              Loading suggestions...
            </div>
          ) : suggestionItems.length > 0 ? (
            <div className="py-1">
              {inputValue.length === 0 && trendingSearches && trendingSearches.length > 0 && (
                <div className="px-3 py-2 text-xs font-medium text-muted-foreground border-b">
                  <TrendingUp className="inline w-3 h-3 mr-1" />
                  Trending searches
                </div>
              )}
              
              {suggestionItems.map((item, index) => (
                <button
                  key={`${item.type}-${item.query}-${index}`}
                  onClick={() => handleSuggestionClick(item.query)}
                  className={cn(
                    'flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground',
                    selectedIndex === index && 'bg-accent text-accent-foreground'
                  )}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    {item.type === 'recent' ? (
                      <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
                    ) : item.type === 'popular' ? (
                      <TrendingUp className="h-3 w-3 text-muted-foreground shrink-0" />
                    ) : (
                      <Search className="h-3 w-3 text-muted-foreground shrink-0" />
                    )}
                    
                    <span className="truncate">{item.query}</span>
                  </div>
                  
                  {item.count && item.count > 0 && (
                    <span className="text-xs text-muted-foreground shrink-0">
                      {item.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ) : inputValue.length > 0 ? (
            <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
              No suggestions found
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}