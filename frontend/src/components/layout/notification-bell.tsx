/**
 * Notification Bell Component
 *
 * Simple bell icon with unread count badge that links to the activity page
 *
 * Features:
 * - Shows unread count badge (polling every 5 seconds)
 * - Direct link to /activity page
 * - Supports collapsed sidebar state
 * - Shows label when sidebar is expanded
 */
"use client"

import { Bell } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useUnreadNotificationCount } from "@/hooks/use-notifications"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { usePathname } from "next/navigation"

interface NotificationBellProps {
  collapsed?: boolean
}

export function NotificationBell({ collapsed = false }: NotificationBellProps) {
  // Fetch unread count with polling
  const { data: unreadCountData } = useUnreadNotificationCount()
  const unreadCount = unreadCountData?.unread_count || 0
  const pathname = usePathname()
  const isActive = pathname === "/activity" || pathname.startsWith("/activity")

  return (
    <Link
      href="/activity"
      className={cn(
        "flex items-center gap-3 w-full h-10 relative rounded-md transition-colors",
        "hover:bg-accent hover:text-accent-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        collapsed ? "justify-center px-0" : "justify-start px-3",
        isActive
          ? "bg-muted text-foreground"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      <Bell className="h-6 w-6 flex-shrink-0" />
      {!collapsed && (
        <span className="flex items-center justify-start">Notifications</span>
      )}
      {unreadCount > 0 && (
        <Badge
          variant="destructive"
          className={cn(
            "h-5 min-w-5 flex items-center justify-center p-0 text-xs",
            collapsed ? "absolute -top-1 -right-1" : "ml-auto"
          )}
        >
          {unreadCount > 99 ? "99+" : unreadCount}
        </Badge>
      )}
    </Link>
  )
}
