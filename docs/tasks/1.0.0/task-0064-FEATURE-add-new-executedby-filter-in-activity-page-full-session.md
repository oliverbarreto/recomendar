# Add new filter and change default status

_Exported on 2/12/2025 at 12:10:04 WET from Cursor (2.1.42)_

---

**User**

<div class="flex flex-col gap-4 p-4 border rounded-lg bg-muted/30">Filters Clear all Status Unread only Type All types Channel All channels Date Range All dates</div>

Ok we need to add a new filter in the activity page to filter the events by the executed by field.

Also, we need to make the default status "ALL" instead of "UNREAD" when we load the activity page. Right now when we navigate to "/activity" we are filtering by "UNREAD" events by default. We need to change it to "ALL" events by default.

---

**Cursor**

Reviewing the activity page implementation to understand the current filter structure.

Reading the activity page and related components to understand the structure:

Checking the Notification type definition:

Implementing both changes:

1. Adding an "Executed By" filter
2. Changing the default status from "unread" to "all"

Updating ActivityFilters to add the "Executed By" filter:

```typescriptreact
/**
 * Activity Filters Component
 *
 * Provides filtering controls for the activity page:
 * - Notification type filter (dropdown)
 * - Date range picker (from/to dates)
 * - Channel filter (dropdown)
 * - Read status filter ("Unread only" / "Show all")
 * - Executed by filter ("All" / "User" / "System")
 */
"use client"

import { NotificationType } from '@/types'
import { Filter, X } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { getNotificationTypeOptions } from '@/lib/notification-helpers'
import { useFollowedChannels } from '@/hooks/use-followed-channels'
import { DateRangePicker } from './date-range-picker'

interface ActivityFiltersProps {
  selectedType?: NotificationType
  selectedChannel?: number
  selectedReadStatus: 'unread' | 'all'
  selectedExecutedBy?: 'user' | 'system'
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
  onExecutedByChange: (executedBy?: 'user' | 'system') => void
  onDateRangeChange: (range: DateRange | undefined) => void
  onClearFilters: () => void
}

export function ActivityFilters({
  selectedType,
  selectedChannel,
  selectedReadStatus,
  dateRange,
  onTypeChange,
  onChannelChange,
  onReadStatusChange,
  onDateRangeChange,
  onClearFilters,
}: ActivityFiltersProps) {
  const { data: followedChannelsData } = useFollowedChannels()
  const followedChannels = followedChannelsData?.followed_channels || []

  const notificationTypeOptions = getNotificationTypeOptions()

  const hasActiveFilters = selectedType || selectedChannel || selectedReadStatus === 'unread' || dateRange?.from

  return (
    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-muted/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-8"
          >
            <X className="h-4 w-4 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {/* Read Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="read-status" className="text-xs">
            Status
          </Label>
          <Select
            value={selectedReadStatus}
            onValueChange={(value) =>
              onReadStatusChange(value as 'unread' | 'all')
            }
          >
            <SelectTrigger id="read-status" className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="unread">Unread only</SelectItem>
              <SelectItem value="all">Show all</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Notification Type Filter */}
        <div className="space-y-2">
          <Label htmlFor="notification-type" className="text-xs">
            Type
          </Label>
          <Select
            value={selectedType || 'all'}
            onValueChange={(value) =>
              onTypeChange(value === 'all' ? undefined : (value as NotificationType))
            }
          >
            <SelectTrigger id="notification-type" className="h-9">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {notificationTypeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channel Filter */}
        <div className="space-y-2">
          <Label htmlFor="channel" className="text-xs">
            Channel
          </Label>
          <Select
            value={selectedChannel?.toString() || 'all'}
            onValueChange={(value) =>
              onChannelChange(value === 'all' ? undefined : parseInt(value))
            }
          >
            <SelectTrigger id="channel" className="h-9">
              <SelectValue placeholder="All channels" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All channels</SelectItem>
              {followedChannels.map((channel) => (
                <SelectItem key={channel.id} value={channel.id.toString()}>
                  {channel.youtube_channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Date Range Filter */}
        <div className="space-y-2">
          <Label htmlFor="date-range" className="text-xs">
            Date Range
          </Label>
          <DateRangePicker
            dateRange={dateRange}
            onDateRangeChange={onDateRangeChange}
          />
        </div>
      </div>
    </div>
  )
}


```

```typescriptreact
/**
 * Activity Filters Component
 *
 * Provides filtering controls for the activity page:
 * - Notification type filter (dropdown)
 * - Date range picker (from/to dates)
 * - Channel filter (dropdown)
 * - Read status filter ("Unread only" / "Show all")
 * - Executed by filter ("All" / "User" / "System")
 */
"use client"

import { NotificationType } from '@/types'
import { Filter, X } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { getNotificationTypeOptions } from '@/lib/notification-helpers'
import { useFollowedChannels } from '@/hooks/use-followed-channels'
import { DateRangePicker } from './date-range-picker'

interface ActivityFiltersProps {
  selectedType?: NotificationType
  selectedChannel?: number
  selectedReadStatus: 'unread' | 'all'
  selectedExecutedBy?: 'user' | 'system'
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
  onExecutedByChange: (executedBy?: 'user' | 'system') => void
  onDateRangeChange: (range: DateRange | undefined) => void
  onClearFilters: () => void
}

export function ActivityFilters({
  selectedType,
  selectedChannel,
  selectedReadStatus,
  selectedExecutedBy,
  dateRange,
  onTypeChange,
  onChannelChange,
  onReadStatusChange,
  onExecutedByChange,
  onDateRangeChange,
  onClearFilters,
}: ActivityFiltersProps) {
  const { data: followedChannelsData } = useFollowedChannels()
  const followedChannels = followedChannelsData?.followed_channels || []

  const notificationTypeOptions = getNotificationTypeOptions()

  const hasActiveFilters = selectedType || selectedChannel || selectedReadStatus === 'unread' || selectedExecutedBy || dateRange?.from

  return (
    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-muted/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-8"
          >
            <X className="h-4 w-4 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {/* Read Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="read-status" className="text-xs">
            Status
          </Label>
          <Select
            value={selectedReadStatus}
            onValueChange={(value) =>
              onReadStatusChange(value as 'unread' | 'all')
            }
          >
            <SelectTrigger id="read-status" className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="unread">Unread only</SelectItem>
              <SelectItem value="all">Show all</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Notification Type Filter */}
        <div className="space-y-2">
          <Label htmlFor="notification-type" className="text-xs">
            Type
          </Label>
          <Select
            value={selectedType || 'all'}
            onValueChange={(value) =>
              onTypeChange(value === 'all' ? undefined : (value as NotificationType))
            }
          >
            <SelectTrigger id="notification-type" className="h-9">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {notificationTypeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channel Filter */}
        <div className="space-y-2">
          <Label htmlFor="channel" className="text-xs">
            Channel
          </Label>
          <Select
            value={selectedChannel?.toString() || 'all'}
            onValueChange={(value) =>
              onChannelChange(value === 'all' ? undefined : parseInt(value))
            }
          >
            <SelectTrigger id="channel" className="h-9">
              <SelectValue placeholder="All channels" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All channels</SelectItem>
              {followedChannels.map((channel) => (
                <SelectItem key={channel.id} value={channel.id.toString()}>
                  {channel.youtube_channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Date Range Filter */}
        <div className="space-y-2">
          <Label htmlFor="date-range" className="text-xs">
            Date Range
          </Label>
          <DateRangePicker
            dateRange={dateRange}
            onDateRangeChange={onDateRangeChange}
          />
        </div>
      </div>
    </div>
  )
}


```

```typescriptreact
/**
 * Activity Filters Component
 *
 * Provides filtering controls for the activity page:
 * - Notification type filter (dropdown)
 * - Date range picker (from/to dates)
 * - Channel filter (dropdown)
 * - Read status filter ("Unread only" / "Show all")
 * - Executed by filter ("All" / "User" / "System")
 */
"use client"

import { NotificationType } from '@/types'
import { Filter, X } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { getNotificationTypeOptions } from '@/lib/notification-helpers'
import { useFollowedChannels } from '@/hooks/use-followed-channels'
import { DateRangePicker } from './date-range-picker'

interface ActivityFiltersProps {
  selectedType?: NotificationType
  selectedChannel?: number
  selectedReadStatus: 'unread' | 'all'
  selectedExecutedBy?: 'user' | 'system'
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
  onExecutedByChange: (executedBy?: 'user' | 'system') => void
  onDateRangeChange: (range: DateRange | undefined) => void
  onClearFilters: () => void
}

export function ActivityFilters({
  selectedType,
  selectedChannel,
  selectedReadStatus,
  selectedExecutedBy,
  dateRange,
  onTypeChange,
  onChannelChange,
  onReadStatusChange,
  onExecutedByChange,
  onDateRangeChange,
  onClearFilters,
}: ActivityFiltersProps) {
  const { data: followedChannelsData } = useFollowedChannels()
  const followedChannels = followedChannelsData?.followed_channels || []

  const notificationTypeOptions = getNotificationTypeOptions()

  const hasActiveFilters = selectedType || selectedChannel || selectedReadStatus === 'unread' || selectedExecutedBy || dateRange?.from

  return (
    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-muted/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-8"
          >
            <X className="h-4 w-4 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-6">
        {/* Read Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="read-status" className="text-xs">
            Status
          </Label>
          <Select
            value={selectedReadStatus}
            onValueChange={(value) =>
              onReadStatusChange(value as 'unread' | 'all')
            }
          >
            <SelectTrigger id="read-status" className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="unread">Unread only</SelectItem>
              <SelectItem value="all">Show all</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Notification Type Filter */}
        <div className="space-y-2">
          <Label htmlFor="notification-type" className="text-xs">
            Type
          </Label>
          <Select
            value={selectedType || 'all'}
            onValueChange={(value) =>
              onTypeChange(value === 'all' ? undefined : (value as NotificationType))
            }
          >
            <SelectTrigger id="notification-type" className="h-9">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {notificationTypeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channel Filter */}
        <div className="space-y-2">
          <Label htmlFor="channel" className="text-xs">
            Channel
          </Label>
          <Select
            value={selectedChannel?.toString() || 'all'}
            onValueChange={(value) =>
              onChannelChange(value === 'all' ? undefined : parseInt(value))
            }
          >
            <SelectTrigger id="channel" className="h-9">
              <SelectValue placeholder="All channels" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All channels</SelectItem>
              {followedChannels.map((channel) => (
                <SelectItem key={channel.id} value={channel.id.toString()}>
                  {channel.youtube_channel_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Executed By Filter */}
        <div className="space-y-2">
          <Label htmlFor="executed-by" className="text-xs">
            Executed By
          </Label>
          <Select
            value={selectedExecutedBy || 'all'}
            onValueChange={(value) =>
              onExecutedByChange(value === 'all' ? undefined : (value as 'user' | 'system'))
            }
          >
            <SelectTrigger id="executed-by" className="h-9">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="user">User</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Date Range Filter */}
        <div className="space-y-2">
          <Label htmlFor="date-range" className="text-xs">
            Date Range
          </Label>
          <DateRangePicker
            dateRange={dateRange}
            onDateRangeChange={onDateRangeChange}
          />
        </div>
      </div>
    </div>
  )
}


```

Updating ActivityPage to handle the new filter and change the default status:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >(
    (searchParams.get("executedBy") as "user" | "system") || undefined
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "unread") {
      params.set("status", selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("unread")
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

```

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >(
    (searchParams.get("executedBy") as "user" | "system") || undefined
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "all") {
      params.set("status", selectedReadStatus)
    }
    if (selectedExecutedBy) {
      params.set("executedBy", selectedExecutedBy)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    selectedExecutedBy,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("unread")
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

```

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >(
    (searchParams.get("executedBy") as "user" | "system") || undefined
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "all") {
      params.set("status", selectedReadStatus)
    }
    if (selectedExecutedBy) {
      params.set("executedBy", selectedExecutedBy)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    selectedExecutedBy,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, executed by, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by executed by
    if (selectedExecutedBy && notification.executedBy !== selectedExecutedBy) {
      return false
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("unread")
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

```

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >(
    (searchParams.get("executedBy") as "user" | "system") || undefined
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "all") {
      params.set("status", selectedReadStatus)
    }
    if (selectedExecutedBy) {
      params.set("executedBy", selectedExecutedBy)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    selectedExecutedBy,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, executed by, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by executed by
    if (selectedExecutedBy && notification.executedBy !== selectedExecutedBy) {
      return false
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleExecutedByChange = (executedBy?: "user" | "system") => {
    setSelectedExecutedBy(executedBy)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("all")
    setSelectedExecutedBy(undefined)
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

```

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >(
    (searchParams.get("executedBy") as "user" | "system") || undefined
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "all") {
      params.set("status", selectedReadStatus)
    }
    if (selectedExecutedBy) {
      params.set("executedBy", selectedExecutedBy)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    selectedExecutedBy,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, executed by, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by executed by
    if (selectedExecutedBy && notification.executedBy !== selectedExecutedBy) {
      return false
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleExecutedByChange = (executedBy?: "user" | "system") => {
    setSelectedExecutedBy(executedBy)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("all")
    setSelectedExecutedBy(undefined)
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          selectedExecutedBy={selectedExecutedBy}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onExecutedByChange={handleExecutedByChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}

```

Checking for linting errors:

## Changes Made

### 1. Added "Executed By" filter

- Added `selectedExecutedBy` and `onExecutedByChange` props to `ActivityFilters`
- Added a dropdown with options: "All", "User", "System"
- Updated the grid from `lg:grid-cols-4` to `lg:grid-cols-5` to fit the new filter
- Updated `hasActiveFilters` to include the executedBy filter

### 2. Updated ActivityPage

- Added state for `selectedExecutedBy` (reads from URL params)
- Added filtering logic in `filteredNotifications` to filter by `executedBy`
- Added URL param handling for `executedBy` in the `useEffect`
- Added `handleExecutedByChange` handler
- Updated `handleClearFilters` to reset `executedBy` to `undefined`

### 3. Changed default status from "unread" to "all"

- Changed the default value in `useState` from `"unread"` to `"all"`
- Updated URL param logic to only set status if it's not `"all"` (instead of not `"unread"`)
- Updated `handleClearFilters` to set status to `"all"` instead of `"unread"`

All changes are complete and there are no linting errors. The activity page now:

- Shows all notifications by default (instead of unread only)
- Includes a new "Executed By" filter to filter by User or System
- Properly handles URL params for bookmarkable filters

The filter appears in the filters section alongside Status, Type, Channel, and Date Range.
