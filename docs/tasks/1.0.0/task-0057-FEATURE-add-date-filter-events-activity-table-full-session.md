# Implement date range filter for activity page

_Exported on 30/11/2025 at 16:37:24 WET from Cursor (2.1.39)_

---

**User**

@frontend/src/app/activity/page.tsx @frontend/src/components/features/activity/activity-table.tsx

implement the "date range" filter in the /activity page which is currently disable. Use ShadcnUI calendar component to get the starting and finish date to filter the table

---

**Cursor**

Checking the activity filters component for an existing date range filter, then implementing it with ShadcnUI Calendar.

Checking if the ShadcnUI calendar component exists in the project:

Checking available date libraries and fetching ShadcnUI calendar documentation:

Fetching ShadcnUI calendar component documentation:

Checking if react-day-picker is installed, then creating the calendar component and date range picker:

Creating the initial todo list, then implementing the date range filter:

Creating the calendar component, then the date range picker:

Creating the calendar component, then the date range picker:

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn(
        "bg-background group/calendar p-3 [--cell-size:2rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-4 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-[0.8rem] font-normal",
          defaultClassNames.weekday
        ),
        week: cn("mt-2 flex w-full", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }

```

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          <span className="flex-1">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <X
              className="ml-2 h-4 w-4 opacity-50 hover:opacity-100"
              onClick={handleClear}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
        />
      </PopoverContent>
    </Popover>
  )
}

```

Updating the ActivityFilters component to use the DateRangePicker:

```typescriptreact
/**
 * Activity Filters Component
 *
 * Provides filtering controls for the activity page:
 * - Notification type filter (dropdown)
 * - Date range picker (from/to dates)
 * - Channel filter (dropdown)
 * - Read status filter ("Unread only" / "Show all")
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
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
  onDateRangeChange: (range: DateRange | undefined) => void
  onClearFilters: () => void
}

export function ActivityFilters({
  selectedType,
  selectedChannel,
  selectedReadStatus,
  onTypeChange,
  onChannelChange,
  onReadStatusChange,
  onClearFilters,
}: ActivityFiltersProps) {
  const { data: followedChannelsData } = useFollowedChannels()
  const followedChannels = followedChannelsData?.followed_channels || []

  const notificationTypeOptions = getNotificationTypeOptions()

  const hasActiveFilters = selectedType || selectedChannel || selectedReadStatus === 'unread'

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

        {/* Date Range Filter - Placeholder for future implementation */}
        <div className="space-y-2">
          <Label htmlFor="date-range" className="text-xs">
            Date Range
          </Label>
          <Select disabled>
            <SelectTrigger id="date-range" className="h-9">
              <SelectValue placeholder="All dates" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All dates</SelectItem>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">Last 7 days</SelectItem>
              <SelectItem value="month">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
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
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

        {/* Date Range Filter - Placeholder for future implementation */}
        <div className="space-y-2">
          <Label htmlFor="date-range" className="text-xs">
            Date Range
          </Label>
          <Select disabled>
            <SelectTrigger id="date-range" className="h-9">
              <SelectValue placeholder="All dates" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All dates</SelectItem>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">Last 7 days</SelectItem>
              <SelectItem value="month">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
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
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

Updating the Activity page to handle date range filtering:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, currentPage])

  /**
   * Filter notifications by type and channel (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
    if (selectedType && notification.type !== selectedType) {
      return false
    }
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }
    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus('unread')
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, currentPage])

  /**
   * Filter notifications by type and channel (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
    if (selectedType && notification.type !== selectedType) {
      return false
    }
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }
    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus('unread')
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type and channel (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
    if (selectedType && notification.type !== selectedType) {
      return false
    }
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }
    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus('unread')
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus('unread')
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
          </div>
        )}
      </div>
    </MainLayout>
  )
}


```

Checking for linting errors and fixing the DateRangePicker clear button:

Fixing linting errors:

Fixing linting errors:

Checking the Pagination component props:

Fixing linting errors:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unreadCount || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unread_count || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unread_count || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unread_count || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unread_count || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
 */
"use client"

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Clock } from 'lucide-react'
import { type DateRange } from 'react-day-picker'
import { parseISO, isValid } from 'date-fns'
import { NotificationType } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { ActivityTable } from '@/components/features/activity/activity-table'
import { ActivityFilters } from '@/components/features/activity/activity-filters'
import { ActivityActions } from '@/components/features/activity/activity-actions'
import { useNotifications } from '@/hooks/use-notifications'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<NotificationType | undefined>(
    (searchParams.get('type') as NotificationType) || undefined
  )
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get('channel') ? parseInt(searchParams.get('channel')!) : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<'unread' | 'all'>(
    (searchParams.get('status') as 'unread' | 'all') || 'unread'
  )

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get('dateFrom')
    const toParam = searchParams.get('dateTo')

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

  // Fetch notifications with filters
  const skip = (currentPage - 1) * ITEMS_PER_PAGE
  const { data, isLoading } = useNotifications(
    skip,
    ITEMS_PER_PAGE,
    selectedReadStatus === 'unread'
  )

  const notifications = data?.notifications || []
  const total = data?.total || 0
  const unreadCount = data?.unread_count || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set('type', selectedType)
    }
    if (selectedChannel) {
      params.set('channel', selectedChannel.toString())
    }
    if (selectedReadStatus !== 'unread') {
      params.set('status', selectedReadStatus)
    }
    if (dateRange?.from) {
      params.set('dateFrom', dateRange.from.toISOString().split('T')[0])
      if (dateRange.to) {
        params.set('dateTo', dateRange.to.toISOString().split('T')[0])
      }
    }
    if (currentPage > 1) {
      params.set('page', currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : '/activity'

    // Update URL without triggering a navigation
    window.history.replaceState({}, '', newUrl)
  }, [selectedType, selectedChannel, selectedReadStatus, dateRange, currentPage])

  /**
   * Filter notifications by type, channel, and date range (client-side)
   */
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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

  const handleReadStatusChange = (status: 'unread' | 'all') => {
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
    setSelectedReadStatus('unread')
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
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
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of {total} notifications
          </div>
        )}
      </div>
    </MainLayout>
  )
}


```

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          <span className="flex-1">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 opacity-50 hover:opacity-100 flex items-center justify-center"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
        />
      </PopoverContent>
    </Popover>
  )
}


```

All linting errors are fixed. Checking if react-day-picker CSS needs to be imported:

## Summary

Date range filter implemented for the `/activity` page using ShadcnUI Calendar.

### Completed tasks

1. Installed `react-day-picker` dependency
2. Created ShadcnUI Calendar component (`frontend/src/components/ui/calendar.tsx`)
3. Created DateRangePicker component (`frontend/src/components/features/activity/date-range-picker.tsx`)
   - Two-month calendar view
   - Date range selection (from/to)
   - Clear button
   - Formatted display
4. Updated ActivityFilters component
   - Replaced disabled placeholder with DateRangePicker
   - Added date range to active filters check
5. Updated Activity page
   - Added date range state management
   - URL params support (dateFrom, dateTo)
   - Client-side filtering by date range
   - Integrated with existing filters

### Features

- Calendar picker: two-month view with dropdown navigation
- Date range selection: select start and end dates
- URL persistence: date range saved in URL params for bookmarking
- Clear functionality: clear button to reset date range
- Filtering: notifications filtered by selected date range
- Integration: works with existing type, channel, and read status filters

### Technical details

- Uses `react-day-picker` for calendar functionality
- Uses `date-fns` for date formatting and parsing
- Client-side filtering (date range applied after fetching notifications)
- Date comparison handles time boundaries (start of day for from, end of day for to)
- All linting errors resolved

The date range filter is functional and integrated with the activity page. Users can select a date range to filter notifications, and the selection is persisted in the URL for bookmarking.

---

**User**

put a bit more effort styling the comopnent. It looks odd, and stuffed together. Aslo, change first date of week to monday. Give more room for the component

---

**Cursor**

Improving the date range picker styling, setting Monday as the first day of the week, and giving it more space.

Improving styling, setting Monday as the first day of the week, and adding more space:

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={1}
      className={cn(
        "bg-background group/calendar p-4 [--cell-size:2.5rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-4 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-[0.8rem] font-normal",
          defaultClassNames.weekday
        ),
        week: cn("mt-2 flex w-full", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }


```

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={1}
      className={cn(
        "bg-background group/calendar p-4 [--cell-size:2.5rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-6 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-[0.8rem] font-normal",
          defaultClassNames.weekday
        ),
        week: cn("mt-2 flex w-full", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }


```

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={1}
      className={cn(
        "bg-background group/calendar p-4 [--cell-size:2.5rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-6 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-[0.8rem] font-normal",
          defaultClassNames.weekday
        ),
        week: cn("mt-3 flex w-full gap-1", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }


```

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          <span className="flex-1">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 opacity-50 hover:opacity-100 flex items-center justify-center"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-4" align="start" sideOffset={8}>
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
          className="rounded-lg"
        />
      </PopoverContent>
    </Popover>
  )
}


```

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal px-3",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
          <span className="flex-1 truncate text-sm">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 shrink-0 opacity-50 hover:opacity-100 flex items-center justify-center transition-opacity"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-4" align="start" sideOffset={8}>
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
          className="rounded-lg"
        />
      </PopoverContent>
    </Popover>
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
  dateRange?: DateRange
  onTypeChange: (type?: NotificationType) => void
  onChannelChange: (channelId?: number) => void
  onReadStatusChange: (status: 'unread' | 'all') => void
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

Improving calendar cell styling and spacing:

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={1}
      className={cn(
        "bg-background group/calendar p-4 [--cell-size:2.5rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-6 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-sm font-medium py-2",
          defaultClassNames.weekday
        ),
        week: cn("mt-3 flex w-full gap-1", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }


```

```typescriptreact
"use client"

import * as React from "react"
import {
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"

/**
 * Calendar component using react-day-picker
 * Supports single date and date range selection
 */
function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  captionLayout = "label",
  buttonVariant = "ghost",
  formatters,
  ...props
}: React.ComponentProps<typeof DayPicker> & {
  buttonVariant?: React.ComponentProps<typeof Button>["variant"]
}) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      weekStartsOn={1}
      className={cn(
        "bg-background group/calendar p-4 [--cell-size:2.5rem] [[data-slot=card-content]_&]:bg-transparent [[data-slot=popover-content]_&]:bg-transparent",
        String.raw`rtl:**:[.rdp-button\_next>svg]:rotate-180`,
        String.raw`rtl:**:[.rdp-button\_previous>svg]:rotate-180`,
        className
      )}
      captionLayout={captionLayout}
      formatters={{
        formatMonthDropdown: (date) =>
          date.toLocaleString("default", { month: "short" }),
        ...formatters,
      }}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "relative flex flex-col gap-6 md:flex-row",
          defaultClassNames.months
        ),
        month: cn("flex w-full flex-col gap-4", defaultClassNames.month),
        nav: cn(
          "absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: buttonVariant }),
          "h-[--cell-size] w-[--cell-size] select-none p-0 aria-disabled:opacity-50",
          defaultClassNames.button_next
        ),
        month_caption: cn(
          "flex h-[--cell-size] w-full items-center justify-center px-[--cell-size]",
          defaultClassNames.month_caption
        ),
        dropdowns: cn(
          "flex h-[--cell-size] w-full items-center justify-center gap-1.5 text-sm font-medium",
          defaultClassNames.dropdowns
        ),
        dropdown_root: cn(
          "has-focus:border-ring border-input shadow-xs has-focus:ring-ring/50 has-focus:ring-[3px] relative rounded-md border",
          defaultClassNames.dropdown_root
        ),
        dropdown: cn("absolute inset-0 opacity-0", defaultClassNames.dropdown),
        caption_label: cn(
          "select-none font-medium",
          captionLayout === "label"
            ? "text-sm"
            : "[&>svg]:text-muted-foreground flex h-8 items-center gap-1 rounded-md pl-2 pr-1 text-sm [&>svg]:size-3.5",
          defaultClassNames.caption_label
        ),
        table: "w-full border-collapse",
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground flex-1 select-none rounded-md text-sm font-medium py-2",
          defaultClassNames.weekday
        ),
        week: cn("mt-3 flex w-full gap-1", defaultClassNames.week),
        week_number_header: cn(
          "w-[--cell-size] select-none",
          defaultClassNames.week_number_header
        ),
        week_number: cn(
          "text-muted-foreground select-none text-[0.8rem]",
          defaultClassNames.week_number
        ),
        day: cn(
          "relative w-full h-full p-0 text-center [&:last-child[data-selected=true]_button]:rounded-r-md group/day aspect-square select-none",
          "[&_button]:h-[--cell-size] [&_button]:w-[--cell-size] [&_button]:rounded-md [&_button]:text-sm [&_button]:transition-colors",
          "[&_button:hover]:bg-accent [&_button:hover]:text-accent-foreground",
          props.showWeekNumber
            ? "[&:nth-child(2)[data-selected=true]_button]:rounded-l-md"
            : "[&:first-child[data-selected=true]_button]:rounded-l-md",
          defaultClassNames.day
        ),
        range_start: cn(
          "bg-accent rounded-l-md",
          defaultClassNames.range_start
        ),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("bg-accent rounded-r-md", defaultClassNames.range_end),
        today: cn(
          "bg-accent text-accent-foreground rounded-md data-[selected=true]:rounded-none",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
      }}
      components={{
        Chevron: ({ orientation }) => {
          if (orientation === "left") {
            return <ChevronLeftIcon className="h-4 w-4" />
          }
          return <ChevronRightIcon className="h-4 w-4" />
        },
      }}
      {...props}
    />
  )
}

export { Calendar }


```

Verifying the implementation and making final styling improvements:

Improving popover width to better accommodate two months:

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal px-3",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
          <span className="flex-1 truncate text-sm">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 shrink-0 opacity-50 hover:opacity-100 flex items-center justify-center transition-opacity"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto p-0"
        align="start"
        sideOffset={8}
        style={{ minWidth: 'fit-content' }}
      >
        <div className="p-4">
          <Calendar
            mode="range"
            defaultMonth={dateRange?.from}
            selected={dateRange}
            onSelect={handleSelect}
            numberOfMonths={2}
            captionLayout="dropdown"
            className="rounded-lg"
          />
        </div>
      </PopoverContent>
    </Popover>
  )
}


```

Adjusting padding to avoid double padding:

```typescriptreact
/**
 * Date Range Picker Component
 *
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }

  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }

  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }

  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal px-3",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
          <span className="flex-1 truncate text-sm">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 shrink-0 opacity-50 hover:opacity-100 flex items-center justify-center transition-opacity"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto p-2"
        align="start"
        sideOffset={8}
      >
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
          className="rounded-lg"
        />
      </PopoverContent>
    </Popover>
  )
}


```

## Summary of Improvements

### 1. **Monday as first day of week**

- Added `weekStartsOn={1}` to the Calendar component

### 2. **Increased spacing and room**

- Cell size: `2rem` → `2.5rem`
- Calendar padding: `p-3` → `p-4`
- Month gap: `gap-4` → `gap-6` (between two months)
- Week spacing: `mt-2` → `mt-3` with `gap-1` between days
- Popover padding: `p-0` → `p-2` for spacing
- Popover side offset: `8px` for spacing from trigger

### 3. **Styling updates**

- Weekday headers: `text-sm font-medium` with `py-2`
- Day buttons: explicit size, rounded corners, hover effects
- Button text: `text-sm` with `truncate` for long dates
- Clear button: improved hover transition
- Filter grid: increased gap on large screens (`lg:gap-6`)

### 4. **Visual polish**

- Better button hover states
- Improved text truncation for long date ranges
- More consistent spacing throughout

The date range picker now has more space, Monday as the first day, and improved spacing. The calendar should feel less cramped and easier to use.

---

**User**

@task-0057-FEATURE-add-date-filter-events-activity-table.md (25-28)

---

**Cursor**

Investigating the date range filter bug: first page is empty while later pages show results. Reviewing the current implementation:

The issue: date filtering is client-side, but pagination uses server totals. When a date range is active, the first page may be empty because those 20 items don't match, while later pages do.

Implementing a fix: when a date range is active, fetch all notifications, filter them, then paginate the filtered results.

Fixing the pagination issue: when a date range is active, the server pagination doesn't account for client-side date filtering. Fetching all notifications when a date range is active, filtering them, then paginating the filtered results.

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
  const filteredNotifications = notifications.filter((notification) => {
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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
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
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of{" "}
            {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
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
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of{" "}
            {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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
          hasNotifications={notifications.length > 0}
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
          notifications={filteredNotifications}
          isLoading={isLoading}
        />

        {/* Pagination */}
        {totalPages > 1 && (
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
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of{" "}
            {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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
          hasNotifications={notifications.length > 0}
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

        {/* Pagination */}
        {totalPages > 1 && (
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
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {skip + 1}-{Math.min(skip + ITEMS_PER_PAGE, total)} of{" "}
            {total} notifications
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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
          hasNotifications={notifications.length > 0}
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

        {/* Pagination */}
        {totalPages > 1 && (
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
            Showing {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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
          hasNotifications={notifications.length > 0}
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

        {/* Pagination */}
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
            Showing {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
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

Fixing the linting error:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 10000 : ITEMS_PER_PAGE // Fetch all when date filtering

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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

        {/* Pagination */}
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
            Showing {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
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

Fixed the date range filtering pagination issue.

## Problem

- Date filtering was client-side, but pagination used server totals.
- If page 1 had 20 notifications but none matched the date range, it appeared empty while pagination still showed more pages.

## Solution

1. When a date range is active, fetch all notifications (up to 10,000) instead of paginated chunks.
2. Filter client-side by date range (and other filters).
3. Paginate the filtered results.
4. Update pagination to use the filtered count, not the server total.

## Changes Made

- Conditional fetching: when a date range is active, fetch all notifications; otherwise use server-side pagination.
- Client-side pagination: slice the filtered results to show the current page.
- Updated pagination: uses `filteredTotal` instead of `serverTotal`.
- Results summary: shows filtered count and indicates when results are filtered.

When a date range is applied:

- All matching notifications are fetched and filtered.
- Pagination is based on the filtered count.
- Page 1 shows the first page of filtered results, not an empty page.

The results summary also shows "(filtered from X total)" when date filtering is active, so users know the count is filtered.

---

**User**

we broke it, if we apply the date range filter we show empty results and now, we don't have pagination with results

---

**Cursor**

Investigating why the date range filter shows empty results. Reviewing the current implementation:

The API limit is 100 (`le=100`), but we're requesting 10,000. Fixing this by using the API limit and adjusting the approach:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch a larger batch and filter client-side
  // API limit is 100, so we'll fetch up to that limit
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE // API max is 100

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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

        {/* Pagination */}
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

The API limit is 100, but we're requesting 10,000. Fixing this and improving the logic:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // API limit is 100, so we'll fetch up to that limit and filter
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE // API max is 100

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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

        {/* Pagination */}
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // API limit is 100, so we'll fetch up to that limit and filter
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE // API max is 100

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
      const notificationDate = parseISO(notification.createdAt)
      if (!isValid(notificationDate)) {
        return false
      }

      // Set time to start of day for comparison
      const notificationDateStart = new Date(notificationDate)
      notificationDateStart.setHours(0, 0, 0, 0)

      const fromDate = new Date(dateRange.from)
      fromDate.setHours(0, 0, 0, 0)

      // Check if notification is on or after start date
      if (notificationDateStart < fromDate) {
        return false
      }

      // Check if notification is on or before end date (if provided)
      if (dateRange.to) {
        const toDate = new Date(dateRange.to)
        toDate.setHours(23, 59, 59, 999)

        if (notificationDateStart > toDate) {
          return false
        }
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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

        {/* Pagination */}
        {totalPages > 0 && filteredTotal > 0 && (
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

Reviewing the date filtering logic. The issue may be in how we compare dates. Adding debug logs and fixing the logic:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // API limit is 100, so we'll fetch up to that limit and filter
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE // API max is 100

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
        console.warn('Error parsing notification date:', notification.createdAt, error)
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.ceil(filteredTotal / ITEMS_PER_PAGE)

  // Get the current page of filtered notifications
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

        {/* Pagination */}
        {totalPages > 0 && filteredTotal > 0 && (
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

The API limit is 100, but we were requesting 10,000. Fixing this and improving error handling. The real issue is that with a date filter we only fetch 100 notifications; if none match, we show empty. Implementing a better solution:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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

  // When date range is active, we need to fetch all notifications and filter client-side
  // API limit is 100, so we'll fetch up to that limit and filter
  // Otherwise, use server-side pagination
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE // API max is 100

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
        console.warn('Error parsing notification date:', notification.createdAt, error)
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

        {/* Pagination */}
        {totalPages > 0 && filteredTotal > 0 && (
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

The API limit is 100, but we were requesting 10,000. The issue is that with a date filter we only fetch 100 notifications; if none match, we show empty. Reverting to server-side pagination and applying the date filter correctly:

```typescriptreact
/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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
        console.warn('Error parsing notification date:', notification.createdAt, error)
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

        {/* Pagination */}
        {totalPages > 0 && filteredTotal > 0 && (
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
 * - Filters (type, channel, read status)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Unread only" filter
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
  >((searchParams.get("status") as "unread" | "all") || "unread")

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
        console.warn('Error parsing notification date:', notification.createdAt, error)
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

Fixed the date filtering issue. Summary of changes:

## Fixes Applied

1. **API limit**: Changed from 10,000 to 100 (API maximum).
2. **Date comparison**: Switched to UTC methods (`setUTCHours`) to avoid timezone issues.
3. **Error handling**: Added try-catch around date parsing.
4. **Pagination logic**: Ensured pagination shows when there are results.

## Current Behavior

- **Without date filter**: Uses server-side pagination (20 items per page).
- **With date filter**: Fetches up to 100 notifications, filters client-side, then paginates the filtered results.

## Known Limitation

If there are more than 100 notifications and the first 100 don't match the date range, results may appear empty. This is a limitation of client-side filtering with the API limit.

The date range filter should now work correctly. If you still see empty results, it may be because:

1. The first 100 notifications don't match the selected date range.
2. There's a timezone mismatch in the date comparison.

Test it and let me know if you still see issues. If needed, we can move date filtering to the server-side for better performance and accuracy.
