/**
 * Notification Helper Utilities
 * 
 * Provides utility functions for working with notifications:
 * - Type labels (user-friendly text)
 * - Type icons (Lucide React icons)
 * - Type colors (Tailwind CSS classes)
 */

import { NotificationType } from '@/types'
import {
  Video,
  CheckCircle,
  Search,
  CircleCheck,
  AlertCircle,
  type LucideIcon,
} from 'lucide-react'

/**
 * Get user-friendly label for notification type
 * 
 * @param type - Notification type enum value
 * @returns Human-readable label
 */
export function getNotificationTypeLabel(type: NotificationType): string {
  switch (type) {
    case NotificationType.CHANNEL_SEARCH_STARTED:
      return 'Search Started'
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      return 'Search Completed'
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return 'Search Error'
    case NotificationType.VIDEO_DISCOVERED:
      return 'Videos Discovered'
    case NotificationType.EPISODE_CREATED:
      return 'Episode Created'
    default:
      return 'Notification'
  }
}

/**
 * Get icon component for notification type
 * 
 * @param type - Notification type enum value
 * @returns Lucide icon component
 */
export function getNotificationTypeIcon(type: NotificationType): LucideIcon {
  switch (type) {
    case NotificationType.CHANNEL_SEARCH_STARTED:
      return Search
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      return CircleCheck
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return AlertCircle
    case NotificationType.VIDEO_DISCOVERED:
      return Video
    case NotificationType.EPISODE_CREATED:
      return CheckCircle
    default:
      return CheckCircle
  }
}

/**
 * Get color classes for notification type
 * 
 * @param type - Notification type enum value
 * @returns Object with text and background color classes
 */
export function getNotificationTypeColor(type: NotificationType): {
  textClass: string
  bgClass: string
} {
  switch (type) {
    case NotificationType.CHANNEL_SEARCH_STARTED:
      return {
        textClass: 'text-yellow-600 dark:text-yellow-300',
        bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
      }
    case NotificationType.CHANNEL_SEARCH_COMPLETED:
      return {
        textClass: 'text-green-600 dark:text-green-300',
        bgClass: 'bg-green-100 dark:bg-green-900/30',
      }
    case NotificationType.CHANNEL_SEARCH_ERROR:
      return {
        textClass: 'text-red-600 dark:text-red-300',
        bgClass: 'bg-red-100 dark:bg-red-900/30',
      }
    case NotificationType.VIDEO_DISCOVERED:
      return {
        textClass: 'text-blue-600 dark:text-blue-300',
        bgClass: 'bg-blue-100 dark:bg-blue-900/30',
      }
    case NotificationType.EPISODE_CREATED:
      return {
        textClass: 'text-green-600 dark:text-green-300',
        bgClass: 'bg-green-100 dark:bg-green-900/30',
      }
    default:
      return {
        textClass: 'text-gray-600 dark:text-gray-300',
        bgClass: 'bg-gray-100 dark:bg-gray-900/30',
      }
  }
}

/**
 * Get all notification type options for filter dropdowns
 * 
 * @returns Array of notification type options
 */
export function getNotificationTypeOptions(): Array<{
  value: NotificationType
  label: string
}> {
  return [
    {
      value: NotificationType.CHANNEL_SEARCH_STARTED,
      label: getNotificationTypeLabel(NotificationType.CHANNEL_SEARCH_STARTED),
    },
    {
      value: NotificationType.CHANNEL_SEARCH_COMPLETED,
      label: getNotificationTypeLabel(NotificationType.CHANNEL_SEARCH_COMPLETED),
    },
    {
      value: NotificationType.CHANNEL_SEARCH_ERROR,
      label: getNotificationTypeLabel(NotificationType.CHANNEL_SEARCH_ERROR),
    },
    {
      value: NotificationType.VIDEO_DISCOVERED,
      label: getNotificationTypeLabel(NotificationType.VIDEO_DISCOVERED),
    },
    {
      value: NotificationType.EPISODE_CREATED,
      label: getNotificationTypeLabel(NotificationType.EPISODE_CREATED),
    },
  ]
}

