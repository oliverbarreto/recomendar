# Expand mobile description column width
_Exported on 7/12/2025 at 9:00:00 WET from Cursor (2.1.49)_

---

**User**

<div class="border rounded-lg overflow-hidden">Type Channel Date Time Executed By Description Search Completed Solo Fonseca 06/12/2025 19:35:58 User Search completed for Solo Fonseca 15 new videos found from Solo Fonseca Actions Search</div> 

In mobile devices the width of hte collumn "description" is too small. Make it a bit bigger. We have to horizontally scroll in a mobile device, and this way we got space. You can see in the image that the width it is too short. Make it bigger to make the collumn take almost the full visible horizontal space so we see on collumn, not three like in the image (time, excuted by and description)

---

**Cursor**

Searching for the activity log table component to adjust mobile column widths.


Reading the activity table component to understand the current structure:


Adjusting column widths for mobile: making the Description column wider and hiding or reducing other columns on small screens.


```typescriptreact
/**
 * Activity Table Component
 * 
 * Displays notifications in a responsive table format with:
 * - Type column (with icon and descriptive text)
 * - Channel column (with link to filtered videos page)
 * - Date column (dd/MM/yyyy format)
 * - Time column (HH:mm:ss format)
 * - Description column
 * - Actions column (context menu with mark as read option)
 */
"use client"

import { Notification, NotificationType } from '@/types'
import { format, isValid, parseISO } from 'date-fns'
import { Ellipsis, CheckCircle, ExternalLink, User, Bot } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  getNotificationTypeLabel,
  getNotificationTypeIcon,
  getNotificationTypeColor,
} from '@/lib/notification-helpers'
import { useMarkNotificationAsRead } from '@/hooks/use-notifications'

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(dateString: string | undefined | null, formatString: string, fallback: string = 'N/A'): string {
  if (!dateString) {
    return fallback
  }
  
  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)
    
    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }
    
    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }
    
    return format(date, formatString)
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return fallback
  }
}

interface ActivityTableProps {
  notifications: Notification[]
  isLoading?: boolean
}

/**
 * Get navigation URL for notification based on type and data
 */
function getNotificationLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
      
    case NotificationType.EPISODE_CREATED:
      if (data.episode_id) {
        return `/channel?episode=${data.episode_id}`
      }
      return '/channel'
    
    case NotificationType.CHANNEL_SEARCH_STARTED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}`
      }
      return '/subscriptions/channels'
    
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return '/subscriptions/channels'
      
    default:
      return null
  }
}

/**
 * Get channel name from notification data
 */
function getChannelName(notification: Notification): string {
  const data = notification.dataJson || {}
  return data.channel_name || 'N/A'
}

/**
 * Get channel link from notification data
 */
function getChannelLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  if (data.followed_channel_id) {
    return `/subscriptions/videos?channel=${data.followed_channel_id}`
  }
  return null
}

export function ActivityTable({ notifications, isLoading }: ActivityTableProps) {
  const router = useRouter()
  const markAsReadMutation = useMarkNotificationAsRead()

  /**
   * Handle row click - mark as read and navigate
   */
  const handleRowClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsReadMutation.mutateAsync(notification.id)
    }
    
    const link = getNotificationLink(notification)
    if (link) {
      router.push(link)
    }
  }

  /**
   * Handle mark as read from context menu
   */
  const handleMarkAsRead = async (
    e: React.MouseEvent,
    notificationId: number
  ) => {
    e.stopPropagation()
    await markAsReadMutation.mutateAsync(notificationId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">Loading activity...</p>
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg">
        <CheckCircle className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-lg font-medium">No activity found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Notifications will appear here when events occur
        </p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="hidden md:table-cell w-[180px]">Type</TableHead>
            <TableHead className="hidden md:table-cell w-[200px]">Channel</TableHead>
            <TableHead className="hidden md:table-cell w-[120px]">Date</TableHead>
            <TableHead className="hidden md:table-cell w-[100px]">Time</TableHead>
            <TableHead className="hidden md:table-cell w-[120px]">Executed By</TableHead>
            <TableHead className="min-w-[300px] md:min-w-0">Description</TableHead>
            <TableHead className="w-[60px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notifications.map((notification) => {
            const Icon = getNotificationTypeIcon(notification.type)
            const { textClass, bgClass } = getNotificationTypeColor(notification.type)
            const channelLink = getChannelLink(notification)
            const channelName = getChannelName(notification)
            
            return (
              <TableRow
                key={notification.id}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-muted/50",
                  !notification.read && "bg-muted/30 font-medium"
                )}
                onClick={() => handleRowClick(notification)}
              >
                {/* Type Column */}
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className={cn("rounded-full p-1.5", bgClass)}>
                      <Icon className={cn("h-4 w-4", textClass)} />
                    </div>
                    <span className="text-sm">
                      {getNotificationTypeLabel(notification.type)}
                    </span>
                  </div>
                </TableCell>

                {/* Channel Column */}
                <TableCell>
                  {channelLink ? (
                    <Link
                      href={channelLink}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {channelName}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {channelName}
                    </span>
                  )}
                </TableCell>

                {/* Date Column */}
                <TableCell>
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'dd/MM/yyyy')}
                  </span>
                </TableCell>

                {/* Time Column */}
                <TableCell>
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'HH:mm:ss')}
                  </span>
                </TableCell>

                {/* Executed By Column */}
                <TableCell>
                  <Badge
                    variant={notification.executedBy === 'system' ? 'secondary' : 'outline'}
                    className="gap-1 text-xs"
                  >
                    {notification.executedBy === 'system' ? (
                      <>
                        <Bot className="h-3 w-3" />
                        System
                      </>
                    ) : (
                      <>
                        <User className="h-3 w-3" />
                        User
                      </>
                    )}
                  </Badge>
                </TableCell>

                {/* Description Column */}
                <TableCell>
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium">
                      {notification.title}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {notification.message}
                    </span>
                  </div>
                </TableCell>

                {/* Actions Column */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Ellipsis className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!notification.read && (
                        <DropdownMenuItem
                          onClick={(e) => handleMarkAsRead(e, notification.id)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Mark as read
                        </DropdownMenuItem>
                      )}
                      {notification.read && (
                        <DropdownMenuItem disabled>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Already read
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}


```

```typescriptreact
/**
 * Activity Table Component
 * 
 * Displays notifications in a responsive table format with:
 * - Type column (with icon and descriptive text)
 * - Channel column (with link to filtered videos page)
 * - Date column (dd/MM/yyyy format)
 * - Time column (HH:mm:ss format)
 * - Description column
 * - Actions column (context menu with mark as read option)
 */
"use client"

import { Notification, NotificationType } from '@/types'
import { format, isValid, parseISO } from 'date-fns'
import { Ellipsis, CheckCircle, ExternalLink, User, Bot } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  getNotificationTypeLabel,
  getNotificationTypeIcon,
  getNotificationTypeColor,
} from '@/lib/notification-helpers'
import { useMarkNotificationAsRead } from '@/hooks/use-notifications'

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(dateString: string | undefined | null, formatString: string, fallback: string = 'N/A'): string {
  if (!dateString) {
    return fallback
  }
  
  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)
    
    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }
    
    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }
    
    return format(date, formatString)
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return fallback
  }
}

interface ActivityTableProps {
  notifications: Notification[]
  isLoading?: boolean
}

/**
 * Get navigation URL for notification based on type and data
 */
function getNotificationLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
      
    case NotificationType.EPISODE_CREATED:
      if (data.episode_id) {
        return `/channel?episode=${data.episode_id}`
      }
      return '/channel'
    
    case NotificationType.CHANNEL_SEARCH_STARTED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}`
      }
      return '/subscriptions/channels'
    
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return '/subscriptions/channels'
      
    default:
      return null
  }
}

/**
 * Get channel name from notification data
 */
function getChannelName(notification: Notification): string {
  const data = notification.dataJson || {}
  return data.channel_name || 'N/A'
}

/**
 * Get channel link from notification data
 */
function getChannelLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  if (data.followed_channel_id) {
    return `/subscriptions/videos?channel=${data.followed_channel_id}`
  }
  return null
}

export function ActivityTable({ notifications, isLoading }: ActivityTableProps) {
  const router = useRouter()
  const markAsReadMutation = useMarkNotificationAsRead()

  /**
   * Handle row click - mark as read and navigate
   */
  const handleRowClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsReadMutation.mutateAsync(notification.id)
    }
    
    const link = getNotificationLink(notification)
    if (link) {
      router.push(link)
    }
  }

  /**
   * Handle mark as read from context menu
   */
  const handleMarkAsRead = async (
    e: React.MouseEvent,
    notificationId: number
  ) => {
    e.stopPropagation()
    await markAsReadMutation.mutateAsync(notificationId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">Loading activity...</p>
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg">
        <CheckCircle className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-lg font-medium">No activity found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Notifications will appear here when events occur
        </p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="hidden md:table-cell w-[180px]">Type</TableHead>
            <TableHead className="hidden md:table-cell w-[200px]">Channel</TableHead>
            <TableHead className="hidden md:table-cell w-[120px]">Date</TableHead>
            <TableHead className="hidden md:table-cell w-[100px]">Time</TableHead>
            <TableHead className="hidden md:table-cell w-[120px]">Executed By</TableHead>
            <TableHead className="min-w-[300px] md:min-w-0">Description</TableHead>
            <TableHead className="w-[60px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notifications.map((notification) => {
            const Icon = getNotificationTypeIcon(notification.type)
            const { textClass, bgClass } = getNotificationTypeColor(notification.type)
            const channelLink = getChannelLink(notification)
            const channelName = getChannelName(notification)
            
            return (
              <TableRow
                key={notification.id}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-muted/50",
                  !notification.read && "bg-muted/30 font-medium"
                )}
                onClick={() => handleRowClick(notification)}
              >
                {/* Type Column */}
                <TableCell className="hidden md:table-cell">
                  <div className="flex items-center gap-2">
                    <div className={cn("rounded-full p-1.5", bgClass)}>
                      <Icon className={cn("h-4 w-4", textClass)} />
                    </div>
                    <span className="text-sm">
                      {getNotificationTypeLabel(notification.type)}
                    </span>
                  </div>
                </TableCell>

                {/* Channel Column */}
                <TableCell className="hidden md:table-cell">
                  {channelLink ? (
                    <Link
                      href={channelLink}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {channelName}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {channelName}
                    </span>
                  )}
                </TableCell>

                {/* Date Column */}
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'dd/MM/yyyy')}
                  </span>
                </TableCell>

                {/* Time Column */}
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'HH:mm:ss')}
                  </span>
                </TableCell>

                {/* Executed By Column */}
                <TableCell className="hidden md:table-cell">
                  <Badge
                    variant={notification.executedBy === 'system' ? 'secondary' : 'outline'}
                    className="gap-1 text-xs"
                  >
                    {notification.executedBy === 'system' ? (
                      <>
                        <Bot className="h-3 w-3" />
                        System
                      </>
                    ) : (
                      <>
                        <User className="h-3 w-3" />
                        User
                      </>
                    )}
                  </Badge>
                </TableCell>

                {/* Description Column */}
                <TableCell className="min-w-[300px] md:min-w-0">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium">
                      {notification.title}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {notification.message}
                    </span>
                  </div>
                </TableCell>

                {/* Actions Column */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Ellipsis className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!notification.read && (
                        <DropdownMenuItem
                          onClick={(e) => handleMarkAsRead(e, notification.id)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Mark as read
                        </DropdownMenuItem>
                      )}
                      {notification.read && (
                        <DropdownMenuItem disabled>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Already read
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}


```

Checking for linting errors:


Updated the activity table for mobile responsiveness.

**Changes made:**

1. **Hidden columns on mobile**: Type, Channel, Date, Time, and Executed By are hidden on mobile (`hidden md:table-cell`) and shown on medium screens and up.

2. **Wider Description column on mobile**: Added `min-w-[300px]` so the Description column takes up most of the visible width on mobile. On larger screens, it uses the default width (`md:min-w-0`).

On mobile, users will see:
- The Description column (wider, ~300px minimum)
- The Actions column (dropdown menu)
- Other columns are hidden

On tablet/desktop (md breakpoint and up), all columns are visible with their original widths.

The table still scrolls horizontally on mobile, but the Description column is now the primary visible column, improving readability.

---

**User**

the width is now perfect with (@activity-table.tsx (190-191) ). however, i did not want to hide the rest of the columns. we should show them

---

**Cursor**

Reverting the hidden columns so all columns are visible on mobile, keeping the Description column wider.


Removing the `hidden` classes so all columns are visible on mobile, keeping the Description column wider:


```typescriptreact
/**
 * Activity Table Component
 * 
 * Displays notifications in a responsive table format with:
 * - Type column (with icon and descriptive text)
 * - Channel column (with link to filtered videos page)
 * - Date column (dd/MM/yyyy format)
 * - Time column (HH:mm:ss format)
 * - Description column
 * - Actions column (context menu with mark as read option)
 */
"use client"

import { Notification, NotificationType } from '@/types'
import { format, isValid, parseISO } from 'date-fns'
import { Ellipsis, CheckCircle, ExternalLink, User, Bot } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  getNotificationTypeLabel,
  getNotificationTypeIcon,
  getNotificationTypeColor,
} from '@/lib/notification-helpers'
import { useMarkNotificationAsRead } from '@/hooks/use-notifications'

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(dateString: string | undefined | null, formatString: string, fallback: string = 'N/A'): string {
  if (!dateString) {
    return fallback
  }
  
  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)
    
    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }
    
    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }
    
    return format(date, formatString)
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return fallback
  }
}

interface ActivityTableProps {
  notifications: Notification[]
  isLoading?: boolean
}

/**
 * Get navigation URL for notification based on type and data
 */
function getNotificationLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
      
    case NotificationType.EPISODE_CREATED:
      if (data.episode_id) {
        return `/channel?episode=${data.episode_id}`
      }
      return '/channel'
    
    case NotificationType.CHANNEL_SEARCH_STARTED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}`
      }
      return '/subscriptions/channels'
    
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return '/subscriptions/channels'
      
    default:
      return null
  }
}

/**
 * Get channel name from notification data
 */
function getChannelName(notification: Notification): string {
  const data = notification.dataJson || {}
  return data.channel_name || 'N/A'
}

/**
 * Get channel link from notification data
 */
function getChannelLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  if (data.followed_channel_id) {
    return `/subscriptions/videos?channel=${data.followed_channel_id}`
  }
  return null
}

export function ActivityTable({ notifications, isLoading }: ActivityTableProps) {
  const router = useRouter()
  const markAsReadMutation = useMarkNotificationAsRead()

  /**
   * Handle row click - mark as read and navigate
   */
  const handleRowClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsReadMutation.mutateAsync(notification.id)
    }
    
    const link = getNotificationLink(notification)
    if (link) {
      router.push(link)
    }
  }

  /**
   * Handle mark as read from context menu
   */
  const handleMarkAsRead = async (
    e: React.MouseEvent,
    notificationId: number
  ) => {
    e.stopPropagation()
    await markAsReadMutation.mutateAsync(notificationId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">Loading activity...</p>
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg">
        <CheckCircle className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-lg font-medium">No activity found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Notifications will appear here when events occur
        </p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[180px]">Type</TableHead>
            <TableHead className="w-[200px]">Channel</TableHead>
            <TableHead className="w-[120px]">Date</TableHead>
            <TableHead className="w-[100px]">Time</TableHead>
            <TableHead className="w-[120px]">Executed By</TableHead>
            <TableHead className="min-w-[300px] md:min-w-0">Description</TableHead>
            <TableHead className="w-[60px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notifications.map((notification) => {
            const Icon = getNotificationTypeIcon(notification.type)
            const { textClass, bgClass } = getNotificationTypeColor(notification.type)
            const channelLink = getChannelLink(notification)
            const channelName = getChannelName(notification)
            
            return (
              <TableRow
                key={notification.id}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-muted/50",
                  !notification.read && "bg-muted/30 font-medium"
                )}
                onClick={() => handleRowClick(notification)}
              >
                {/* Type Column */}
                <TableCell className="hidden md:table-cell">
                  <div className="flex items-center gap-2">
                    <div className={cn("rounded-full p-1.5", bgClass)}>
                      <Icon className={cn("h-4 w-4", textClass)} />
                    </div>
                    <span className="text-sm">
                      {getNotificationTypeLabel(notification.type)}
                    </span>
                  </div>
                </TableCell>

                {/* Channel Column */}
                <TableCell className="hidden md:table-cell">
                  {channelLink ? (
                    <Link
                      href={channelLink}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {channelName}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {channelName}
                    </span>
                  )}
                </TableCell>

                {/* Date Column */}
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'dd/MM/yyyy')}
                  </span>
                </TableCell>

                {/* Time Column */}
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'HH:mm:ss')}
                  </span>
                </TableCell>

                {/* Executed By Column */}
                <TableCell className="hidden md:table-cell">
                  <Badge
                    variant={notification.executedBy === 'system' ? 'secondary' : 'outline'}
                    className="gap-1 text-xs"
                  >
                    {notification.executedBy === 'system' ? (
                      <>
                        <Bot className="h-3 w-3" />
                        System
                      </>
                    ) : (
                      <>
                        <User className="h-3 w-3" />
                        User
                      </>
                    )}
                  </Badge>
                </TableCell>

                {/* Description Column */}
                <TableCell className="min-w-[300px] md:min-w-0">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium">
                      {notification.title}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {notification.message}
                    </span>
                  </div>
                </TableCell>

                {/* Actions Column */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Ellipsis className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!notification.read && (
                        <DropdownMenuItem
                          onClick={(e) => handleMarkAsRead(e, notification.id)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Mark as read
                        </DropdownMenuItem>
                      )}
                      {notification.read && (
                        <DropdownMenuItem disabled>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Already read
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}


```

```typescriptreact
/**
 * Activity Table Component
 * 
 * Displays notifications in a responsive table format with:
 * - Type column (with icon and descriptive text)
 * - Channel column (with link to filtered videos page)
 * - Date column (dd/MM/yyyy format)
 * - Time column (HH:mm:ss format)
 * - Description column
 * - Actions column (context menu with mark as read option)
 */
"use client"

import { Notification, NotificationType } from '@/types'
import { format, isValid, parseISO } from 'date-fns'
import { Ellipsis, CheckCircle, ExternalLink, User, Bot } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  getNotificationTypeLabel,
  getNotificationTypeIcon,
  getNotificationTypeColor,
} from '@/lib/notification-helpers'
import { useMarkNotificationAsRead } from '@/hooks/use-notifications'

/**
 * Safely format a date string
 * Returns formatted date or fallback if date is invalid
 */
function safeFormatDate(dateString: string | undefined | null, formatString: string, fallback: string = 'N/A'): string {
  if (!dateString) {
    return fallback
  }
  
  try {
    // Try parsing as ISO string first
    let date = parseISO(dateString)
    
    // If parseISO fails, try new Date
    if (!isValid(date)) {
      date = new Date(dateString)
    }
    
    // Check if date is valid
    if (!isValid(date)) {
      return fallback
    }
    
    return format(date, formatString)
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return fallback
  }
}

interface ActivityTableProps {
  notifications: Notification[]
  isLoading?: boolean
}

/**
 * Get navigation URL for notification based on type and data
 */
function getNotificationLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
      
    case NotificationType.EPISODE_CREATED:
      if (data.episode_id) {
        return `/channel?episode=${data.episode_id}`
      }
      return '/channel'
    
    case NotificationType.CHANNEL_SEARCH_STARTED:
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}`
      }
      return '/subscriptions/channels'
    
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return '/subscriptions/channels'
      
    default:
      return null
  }
}

/**
 * Get channel name from notification data
 */
function getChannelName(notification: Notification): string {
  const data = notification.dataJson || {}
  return data.channel_name || 'N/A'
}

/**
 * Get channel link from notification data
 */
function getChannelLink(notification: Notification): string | null {
  const data = notification.dataJson || {}
  if (data.followed_channel_id) {
    return `/subscriptions/videos?channel=${data.followed_channel_id}`
  }
  return null
}

export function ActivityTable({ notifications, isLoading }: ActivityTableProps) {
  const router = useRouter()
  const markAsReadMutation = useMarkNotificationAsRead()

  /**
   * Handle row click - mark as read and navigate
   */
  const handleRowClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsReadMutation.mutateAsync(notification.id)
    }
    
    const link = getNotificationLink(notification)
    if (link) {
      router.push(link)
    }
  }

  /**
   * Handle mark as read from context menu
   */
  const handleMarkAsRead = async (
    e: React.MouseEvent,
    notificationId: number
  ) => {
    e.stopPropagation()
    await markAsReadMutation.mutateAsync(notificationId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">Loading activity...</p>
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg">
        <CheckCircle className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-lg font-medium">No activity found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Notifications will appear here when events occur
        </p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[180px]">Type</TableHead>
            <TableHead className="w-[200px]">Channel</TableHead>
            <TableHead className="w-[120px]">Date</TableHead>
            <TableHead className="w-[100px]">Time</TableHead>
            <TableHead className="w-[120px]">Executed By</TableHead>
            <TableHead className="min-w-[300px] md:min-w-0">Description</TableHead>
            <TableHead className="w-[60px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notifications.map((notification) => {
            const Icon = getNotificationTypeIcon(notification.type)
            const { textClass, bgClass } = getNotificationTypeColor(notification.type)
            const channelLink = getChannelLink(notification)
            const channelName = getChannelName(notification)
            
            return (
              <TableRow
                key={notification.id}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-muted/50",
                  !notification.read && "bg-muted/30 font-medium"
                )}
                onClick={() => handleRowClick(notification)}
              >
                {/* Type Column */}
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className={cn("rounded-full p-1.5", bgClass)}>
                      <Icon className={cn("h-4 w-4", textClass)} />
                    </div>
                    <span className="text-sm">
                      {getNotificationTypeLabel(notification.type)}
                    </span>
                  </div>
                </TableCell>

                {/* Channel Column */}
                <TableCell>
                  {channelLink ? (
                    <Link
                      href={channelLink}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {channelName}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {channelName}
                    </span>
                  )}
                </TableCell>

                {/* Date Column */}
                <TableCell>
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'dd/MM/yyyy')}
                  </span>
                </TableCell>

                {/* Time Column */}
                <TableCell>
                  <span className="text-sm">
                    {safeFormatDate(notification.createdAt, 'HH:mm:ss')}
                  </span>
                </TableCell>

                {/* Executed By Column */}
                <TableCell>
                  <Badge
                    variant={notification.executedBy === 'system' ? 'secondary' : 'outline'}
                    className="gap-1 text-xs"
                  >
                    {notification.executedBy === 'system' ? (
                      <>
                        <Bot className="h-3 w-3" />
                        System
                      </>
                    ) : (
                      <>
                        <User className="h-3 w-3" />
                        User
                      </>
                    )}
                  </Badge>
                </TableCell>

                {/* Description Column */}
                <TableCell className="min-w-[300px] md:min-w-0">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium">
                      {notification.title}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {notification.message}
                    </span>
                  </div>
                </TableCell>

                {/* Actions Column */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Ellipsis className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!notification.read && (
                        <DropdownMenuItem
                          onClick={(e) => handleMarkAsRead(e, notification.id)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Mark as read
                        </DropdownMenuItem>
                      )}
                      {notification.read && (
                        <DropdownMenuItem disabled>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Already read
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}


```

Removed the `hidden` classes from all columns. All columns are now visible on mobile, and the Description column keeps `min-w-[300px]` so it takes more horizontal space when scrolling.

On mobile:
- All columns are visible (Type, Channel, Date, Time, Executed By, Description, Actions)
- The Description column has a minimum width of 300px, making it wider
- Users can scroll horizontally to see all columns, with Description taking more space

The table remains horizontally scrollable on mobile, with the Description column wider for better readability.

