/**
 * Notification Item Component
 * 
 * Displays a single notification with icon, title, message, and timestamp
 * Handles click to mark as read and navigate to relevant page
 * 
 * Supports notification types:
 * - VIDEO_DISCOVERED: New videos found from a channel
 * - EPISODE_CREATED: Episode successfully created
 * - CHANNEL_SEARCH_STARTED: Search for new videos started
 * - CHANNEL_SEARCH_COMPLETED: Search finished successfully
 * - CHANNEL_SEARCH_ERROR: Search failed with error
 */
"use client"

import { Notification, NotificationType } from '@/types'
import { formatDistanceToNow, isValid, parseISO } from 'date-fns'
import { 
  Video, 
  CheckCircle, 
  X, 
  Search, 
  CircleCheck, 
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useMarkNotificationAsRead, useDeleteNotification } from '@/hooks/use-notifications'
import { useState } from 'react'

interface NotificationItemProps {
  notification: Notification
  compact?: boolean
  onNavigate?: () => void
}

/**
 * Get icon component and styling based on notification type
 */
function getNotificationIcon(type: NotificationType): {
  icon: typeof Video
  bgClass: string
  textClass: string
} {
  switch (type) {
    case NotificationType.VIDEO_DISCOVERED:
      return {
        icon: Video,
        bgClass: 'bg-blue-100 dark:bg-blue-900/30',
        textClass: 'text-blue-600 dark:text-blue-300',
      }
    case NotificationType.EPISODE_CREATED:
      return {
        icon: CheckCircle,
        bgClass: 'bg-green-100 dark:bg-green-900/30',
        textClass: 'text-green-600 dark:text-green-300',
      }
    case NotificationType.CHANNEL_SEARCH_STARTED:
      return {
        icon: Search,
        bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
        textClass: 'text-yellow-600 dark:text-yellow-300',
      }
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      return {
        icon: CircleCheck,
        bgClass: 'bg-green-100 dark:bg-green-900/30',
        textClass: 'text-green-600 dark:text-green-300',
      }
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return {
        icon: AlertCircle,
        bgClass: 'bg-red-100 dark:bg-red-900/30',
        textClass: 'text-red-600 dark:text-red-300',
      }
    default:
      return {
        icon: CheckCircle,
        bgClass: 'bg-gray-100 dark:bg-gray-900/30',
        textClass: 'text-gray-600 dark:text-gray-300',
      }
  }
}

/**
 * Get navigation URL based on notification type and data
 */
function getNavigationUrl(notification: Notification): string | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
      // Navigate to videos page filtered by channel and pending review state
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
      
    case NotificationType.EPISODE_CREATED:
      // Navigate to channel page (could also be episode detail page)
      if (data.episode_id) {
        return `/channel?episode=${data.episode_id}`
      }
      return '/channel'
    
    case NotificationType.CHANNEL_SEARCH_STARTED:
      // Navigate to the channel's videos page
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}`
      }
      return '/subscriptions/channels'
    
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      // Navigate to videos page filtered by channel and pending review state
      if (data.followed_channel_id) {
        return `/subscriptions/videos?channel=${data.followed_channel_id}&state=pending_review`
      }
      return '/subscriptions/videos?state=pending_review'
    
    case NotificationType.CHANNEL_SEARCH_ERROR:
      // Navigate to the channels page to retry
      return '/subscriptions/channels'
      
    default:
      return null
  }
}

/**
 * Get badge content for notifications with counts
 */
function getBadgeContent(notification: Notification): { count: number; label: string } | null {
  const data = notification.dataJson || {}
  
  switch (notification.type) {
    case NotificationType.VIDEO_DISCOVERED:
      if (data.video_count && data.video_count > 0) {
        return { 
          count: data.video_count, 
          label: data.video_count === 1 ? 'video' : 'videos' 
        }
      }
      return null
    
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      if (data.new_videos_count !== undefined && data.new_videos_count > 0) {
        return { 
          count: data.new_videos_count, 
          label: data.new_videos_count === 1 ? 'new video' : 'new videos' 
        }
      }
      return null
    
    default:
      return null
  }
}

export function NotificationItem({ notification, compact = false, onNavigate }: NotificationItemProps) {
  const router = useRouter()
  const markAsReadMutation = useMarkNotificationAsRead()
  const deleteNotificationMutation = useDeleteNotification()
  const [isNavigating, setIsNavigating] = useState(false)
  
  const { icon: Icon, bgClass, textClass } = getNotificationIcon(notification.type)
  const navigationUrl = getNavigationUrl(notification)
  const badgeContent = getBadgeContent(notification)
  
  // Check if this is an "in progress" notification
  const isInProgress = notification.type === NotificationType.CHANNEL_SEARCH_STARTED
  
  /**
   * Handle notification click - mark as read and navigate
   */
  const handleClick = async () => {
    if (isNavigating) return
    
    try {
      setIsNavigating(true)
      
      // Mark as read if not already read
      if (!notification.read) {
        await markAsReadMutation.mutateAsync(notification.id)
      }
      
      // Navigate to relevant page
      if (navigationUrl) {
        router.push(navigationUrl)
        onNavigate?.()
      }
    } catch (error) {
      console.error('Error handling notification click:', error)
    } finally {
      setIsNavigating(false)
    }
  }
  
  /**
   * Handle delete button click
   */
  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation() // Prevent triggering handleClick
    
    try {
      await deleteNotificationMutation.mutateAsync(notification.id)
    } catch (error) {
      console.error('Error deleting notification:', error)
    }
  }
  
  // Format timestamp safely
  const getTimeAgo = (dateString: string | undefined | null): string => {
    if (!dateString) {
      return 'Unknown time'
    }
    
    try {
      let date = parseISO(dateString)
      if (!isValid(date)) {
        date = new Date(dateString)
      }
      if (!isValid(date)) {
        return 'Invalid date'
      }
      return formatDistanceToNow(date, { addSuffix: true })
    } catch (error) {
      console.warn('Error formatting date:', dateString, error)
      return 'Invalid date'
    }
  }
  
  const timeAgo = getTimeAgo(notification.createdAt)
  
  return (
    <div
      className={cn(
        "group relative flex items-start gap-3 p-3 rounded-lg transition-colors cursor-pointer",
        "hover:bg-accent",
        !notification.read && "bg-muted/50",
        compact && "p-2"
      )}
      onClick={handleClick}
    >
      {/* Unread indicator dot */}
      {!notification.read && (
        <div className="absolute left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full" />
      )}
      
      {/* Icon */}
      <div className={cn(
        "flex-shrink-0 rounded-full p-2",
        bgClass,
        textClass
      )}>
        {isInProgress ? (
          <Loader2 className={cn("h-4 w-4 animate-spin", compact && "h-3 w-3")} />
        ) : (
          <Icon className={cn("h-4 w-4", compact && "h-3 w-3")} />
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={cn(
            "font-medium text-sm",
            !notification.read && "font-semibold"
          )}>
            {notification.title}
          </p>
          {/* Badge with count */}
          {badgeContent && (
            <Badge 
              variant="secondary" 
              className={cn(
                "text-xs px-1.5 py-0",
                notification.type === NotificationType.CHANNEL_SEARCH_COMPLETED && 
                badgeContent.count > 0 && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
              )}
            >
              {badgeContent.count}
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {notification.message}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {timeAgo}
        </p>
      </div>
      
      {/* Delete button */}
      <Button
        variant="ghost"
        size="icon"
        className="flex-shrink-0 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleDelete}
        disabled={deleteNotificationMutation.isPending}
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Delete notification</span>
      </Button>
    </div>
  )
}

