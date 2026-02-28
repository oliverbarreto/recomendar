/**
 * React hooks for notification management
 * 
 * Provides hooks for fetching, updating, and managing user notifications
 */
"use client"

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Notification, NotificationListResponse, UnreadCountResponse } from '@/types'
import { useToast } from '@/hooks/use-toast'

/**
 * Hook to fetch notifications for current user
 * 
 * @param skip - Number of notifications to skip (pagination)
 * @param limit - Maximum number of notifications to return
 * @param unreadOnly - Return only unread notifications
 */
export function useNotifications(skip = 0, limit = 20, unreadOnly = false) {
  return useQuery<NotificationListResponse>({
    queryKey: ['notifications', skip, limit, unreadOnly],
    queryFn: () => apiClient.getNotifications(skip, limit, unreadOnly),
    refetchInterval: 5000, // Poll every 5 seconds for real-time updates
    refetchOnWindowFocus: true,
    staleTime: 1000, // Consider data stale after 1 second
  })
}

/**
 * Hook to fetch unread notification count
 * Polls every 5 seconds to keep count updated for real-time task notifications
 */
export function useUnreadNotificationCount() {
  return useQuery<UnreadCountResponse>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => apiClient.getUnreadNotificationCount(),
    refetchInterval: 5000, // Poll every 5 seconds for real-time updates
    refetchOnWindowFocus: true,
    staleTime: 1000, // Consider data stale after 1 second
  })
}

/**
 * Hook to mark a notification as read
 */
export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (notificationId: number) => apiClient.markNotificationAsRead(notificationId),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to mark notification as read',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => apiClient.markAllNotificationsAsRead(),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast({
        title: 'All notifications marked as read',
        variant: 'default',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to mark all notifications as read',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to delete a notification
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (notificationId: number) => apiClient.deleteNotification(notificationId),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast({
        title: 'Notification deleted',
        variant: 'default',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to delete notification',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to delete all notifications
 */
export function useDeleteAllNotifications() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => apiClient.deleteAllNotifications(),
    onSuccess: (data) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast({
        title: 'All notifications deleted',
        description: `${data.deletedCount} notification(s) deleted successfully`,
        variant: 'default',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to delete all notifications',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}


