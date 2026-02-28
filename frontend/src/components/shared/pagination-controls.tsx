/**
 * Pagination Controls with cursor-based pagination for efficient handling of large datasets
 */

'use client'

import React from 'react'
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MoreHorizontal
} from 'lucide-react'
import { Button } from '@/components/ui/button'
// Using native select for now - can be replaced with ShadCN Select when available
import { cn } from '@/lib/utils'
import { UserPreferences } from '@/lib/user-preferences'

interface PaginationControlsProps {
  currentPage: number
  totalCount: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  className?: string
  showPageSizeSelector?: boolean
  pageSizeOptions?: number[]
  maxVisiblePages?: number
  loading?: boolean
  hasNextCursor?: boolean
  hasPrevCursor?: boolean
  // For cursor-based pagination
  cursors?: {
    prev?: string
    next?: string
  }
  onCursorChange?: (cursor: string | null, direction: 'next' | 'prev') => void
}

export function PaginationControls({
  currentPage,
  totalCount,
  pageSize,
  onPageChange,
  onPageSizeChange,
  className,
  showPageSizeSelector = true,
  pageSizeOptions = [10, 20, 50, 100],
  maxVisiblePages = 7,
  loading = false,
  hasNextCursor,
  hasPrevCursor,
  cursors,
  onCursorChange,
}: PaginationControlsProps) {
  const totalPages = Math.ceil(totalCount / pageSize)
  const canGoNext = cursors ? hasNextCursor : currentPage < totalPages
  const canGoPrev = cursors ? hasPrevCursor : currentPage > 1

  const handlePageChange = (page: number) => {
    if (loading) return
    
    if (cursors && onCursorChange) {
      // Cursor-based navigation
      if (page > currentPage) {
        onCursorChange(cursors.next || null, 'next')
      } else if (page < currentPage) {
        onCursorChange(cursors.prev || null, 'prev')
      }
    } else {
      // Traditional page-based navigation
      onPageChange(page)
    }
  }

  const handleNext = () => {
    if (!canGoNext || loading) return
    
    if (cursors && onCursorChange) {
      onCursorChange(cursors.next || null, 'next')
    } else {
      onPageChange(currentPage + 1)
    }
  }

  const handlePrev = () => {
    if (!canGoPrev || loading) return
    
    if (cursors && onCursorChange) {
      onCursorChange(cursors.prev || null, 'prev')
    } else {
      onPageChange(currentPage - 1)
    }
  }

  const handleFirst = () => {
    if (currentPage === 1 || loading) return
    onPageChange(1)
  }

  const handleLast = () => {
    if (currentPage === totalPages || loading) return
    onPageChange(totalPages)
  }

  // Generate visible page numbers
  const getVisiblePages = () => {
    if (cursors) {
      // For cursor-based pagination, just show current page
      return [currentPage]
    }

    const pages: (number | 'ellipsis')[] = []
    const half = Math.floor(maxVisiblePages / 2)
    
    let start = Math.max(1, currentPage - half)
    let end = Math.min(totalPages, currentPage + half)
    
    // Adjust if we're near the beginning or end
    if (currentPage <= half) {
      end = Math.min(maxVisiblePages, totalPages)
    }
    if (currentPage > totalPages - half) {
      start = Math.max(1, totalPages - maxVisiblePages + 1)
    }

    // Add first page and ellipsis if needed
    if (start > 1) {
      pages.push(1)
      if (start > 2) pages.push('ellipsis')
    }

    // Add visible pages
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    // Add ellipsis and last page if needed
    if (end < totalPages) {
      if (end < totalPages - 1) pages.push('ellipsis')
      pages.push(totalPages)
    }

    return pages
  }

  const visiblePages = getVisiblePages()
  const startItem = Math.min((currentPage - 1) * pageSize + 1, totalCount)
  const endItem = Math.min(currentPage * pageSize, totalCount)

  if (totalCount === 0) {
    return null
  }

  return (
    <div className={cn('flex items-center justify-between gap-4', className)}>
      {/* Results info */}
      <div className="text-sm text-muted-foreground">
        {cursors ? (
          // For cursor-based pagination, show simpler info
          <span>
            {totalCount.toLocaleString()} result{totalCount !== 1 ? 's' : ''} 
            {loading && ' (loading...)'}
          </span>
        ) : (
          <span>
            Showing {startItem.toLocaleString()} to {endItem.toLocaleString()} of{' '}
            {totalCount.toLocaleString()} result{totalCount !== 1 ? 's' : ''}
            {loading && ' (loading...)'}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Page size selector */}
        {showPageSizeSelector && onPageSizeChange && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground whitespace-nowrap">Rows per page</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
              disabled={loading}
              className="h-8 w-16 px-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pageSizeOptions.map(size => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Pagination buttons */}
        <div className="flex items-center gap-1">
          {/* First page button (only for traditional pagination) */}
          {!cursors && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleFirst}
              disabled={currentPage === 1 || loading}
              className="h-8 w-8 p-0"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
          )}

          {/* Previous page button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrev}
            disabled={!canGoPrev || loading}
            className="h-8 w-8 p-0"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          {/* Page numbers (only for traditional pagination) */}
          {!cursors && (
            <div className="flex items-center gap-1">
              {visiblePages.map((page, index) => 
                page === 'ellipsis' ? (
                  <div key={`ellipsis-${index}`} className="h-8 w-8 flex items-center justify-center">
                    <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                  </div>
                ) : (
                  <Button
                    key={page}
                    variant={page === currentPage ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handlePageChange(page)}
                    disabled={loading}
                    className="h-8 w-8 p-0"
                  >
                    {page}
                  </Button>
                )
              )}
            </div>
          )}

          {/* Current page indicator for cursor-based pagination */}
          {cursors && (
            <div className="px-3 py-1 text-sm font-medium">
              Page {currentPage}
            </div>
          )}

          {/* Next page button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleNext}
            disabled={!canGoNext || loading}
            className="h-8 w-8 p-0"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* Last page button (only for traditional pagination) */}
          {!cursors && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleLast}
              disabled={currentPage === totalPages || loading}
              className="h-8 w-8 p-0"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// Simpler pagination component for basic use cases
interface SimplePaginationProps {
  hasNext: boolean
  hasPrev: boolean
  onNext: () => void
  onPrev: () => void
  loading?: boolean
  className?: string
}

export function SimplePagination({
  hasNext,
  hasPrev,
  onNext,
  onPrev,
  loading = false,
  className
}: SimplePaginationProps) {
  return (
    <div className={cn('flex items-center justify-center gap-2', className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={onPrev}
        disabled={!hasPrev || loading}
        className="gap-1"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={onNext}
        disabled={!hasNext || loading}
        className="gap-1"
      >
        Next
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}

// Hook for managing pagination state
export function usePagination(initialPage = 1, initialPageSize?: number) {
  // Load page size from localStorage if not provided via URL params
  // Priority: initialPageSize (from URL) > localStorage > default (20)
  const getInitialPageSize = React.useCallback(() => {
    if (initialPageSize !== undefined) {
      return initialPageSize
    }
    return UserPreferences.getPageSize()
  }, [initialPageSize])

  const [currentPage, setCurrentPage] = React.useState(initialPage)
  const [pageSize, setPageSize] = React.useState(getInitialPageSize)

  const handlePageChange = React.useCallback((page: number) => {
    setCurrentPage(page)
  }, [])

  const handlePageSizeChange = React.useCallback((newPageSize: number) => {
    // Save the new page size to localStorage for persistence
    UserPreferences.setPageSize(newPageSize)
    setPageSize(newPageSize)
    setCurrentPage(1) // Reset to first page when changing page size
  }, [])

  const reset = React.useCallback(() => {
    setCurrentPage(1)
  }, [])

  return {
    currentPage,
    pageSize,
    handlePageChange,
    handlePageSizeChange,
    reset,
  }
}

// Hook for cursor-based pagination
export function useCursorPagination() {
  const [currentPage, setCurrentPage] = React.useState(1)
  const [cursors, setCursors] = React.useState<{ prev?: string; next?: string }>({})
  const [cursorHistory, setCursorHistory] = React.useState<Array<{ page: number; cursor?: string }>>([])
  
  const handleCursorChange = React.useCallback((cursor: string | null, direction: 'next' | 'prev') => {
    if (direction === 'next') {
      // Moving forward
      const newPage = currentPage + 1
      setCursorHistory(prev => [...prev, { page: currentPage, cursor: cursors.prev }])
      setCurrentPage(newPage)
    } else {
      // Moving backward
      const prevEntry = cursorHistory[cursorHistory.length - 1]
      if (prevEntry) {
        setCurrentPage(prevEntry.page)
        setCursorHistory(prev => prev.slice(0, -1))
        setCursors({ prev: prevEntry.cursor })
      }
    }
  }, [currentPage, cursors.prev, cursorHistory])
  
  const updateCursors = React.useCallback((newCursors: { prev?: string; next?: string }) => {
    setCursors(newCursors)
  }, [])
  
  const reset = React.useCallback(() => {
    setCurrentPage(1)
    setCursors({})
    setCursorHistory([])
  }, [])
  
  return {
    currentPage,
    cursors,
    hasNext: !!cursors.next,
    hasPrev: cursorHistory.length > 0,
    handleCursorChange,
    updateCursors,
    reset,
  }
}