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
  const followedChannels = followedChannelsData || []

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

