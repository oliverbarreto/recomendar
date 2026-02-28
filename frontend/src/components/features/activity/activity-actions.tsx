/**
 * Activity Actions Component
 * 
 * Provides bulk action buttons for the activity page:
 * - Mark all as read (with confirmation dialog)
 * - Delete all (with confirmation dialog)
 */
"use client"

import { useState } from 'react'
import { CheckCircle, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  useMarkAllNotificationsAsRead,
  useDeleteAllNotifications,
} from '@/hooks/use-notifications'

interface ActivityActionsProps {
  hasNotifications: boolean
  unreadCount: number
}

export function ActivityActions({
  hasNotifications,
  unreadCount,
}: ActivityActionsProps) {
  const [showMarkAllDialog, setShowMarkAllDialog] = useState(false)
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false)

  const markAllAsReadMutation = useMarkAllNotificationsAsRead()
  const deleteAllMutation = useDeleteAllNotifications()

  /**
   * Handle mark all as read confirmation
   */
  const handleMarkAllAsRead = async () => {
    await markAllAsReadMutation.mutateAsync()
    setShowMarkAllDialog(false)
  }

  /**
   * Handle delete all confirmation
   */
  const handleDeleteAll = async () => {
    await deleteAllMutation.mutateAsync()
    setShowDeleteAllDialog(false)
  }

  return (
    <>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <span className="text-sm text-muted-foreground">
              {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Mark All as Read Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowMarkAllDialog(true)}
            disabled={!hasNotifications || unreadCount === 0 || markAllAsReadMutation.isPending}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>

          {/* Delete All Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDeleteAllDialog(true)}
            disabled={!hasNotifications || deleteAllMutation.isPending}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete all
          </Button>
        </div>
      </div>

      {/* Mark All as Read Confirmation Dialog */}
      <AlertDialog open={showMarkAllDialog} onOpenChange={setShowMarkAllDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Mark all notifications as read?</AlertDialogTitle>
            <AlertDialogDescription>
              This will mark {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''} as read.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleMarkAllAsRead}
              disabled={markAllAsReadMutation.isPending}
            >
              {markAllAsReadMutation.isPending ? 'Marking...' : 'Mark all as read'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete All Confirmation Dialog */}
      <AlertDialog open={showDeleteAllDialog} onOpenChange={setShowDeleteAllDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete all notifications?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete all notifications from the database.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAll}
              disabled={deleteAllMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteAllMutation.isPending ? 'Deleting...' : 'Delete all'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

