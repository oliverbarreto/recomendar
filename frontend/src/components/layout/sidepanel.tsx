/**
 * Application side panel navigation component with collapsible functionality
 */
"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/shared/theme-toggle"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { NotificationBell } from "@/components/layout/notification-bell"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Home,
  Podcast,
  Bell,
  Zap,
  Video,
  Upload,
  Settings,
  ChevronLeft,
  Mic,
  Rss,
  ListVideo,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { QuickAddDialog } from "@/components/features/episodes/quick-add-dialog"
import { usePendingVideosCount } from "@/hooks/use-youtube-videos"

interface SidePanelProps {}

export function SidePanel({}: SidePanelProps) {
  const pathname = usePathname()
  const [isMounted, setIsMounted] = useState(false)
  const [quickAddOpen, setQuickAddOpen] = useState(false)

  // Initialize collapse state from localStorage immediately to prevent hydration mismatch
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem("sidepanel-collapsed")
      return saved === "true"
    } catch (e) {
      return false
    }
  })

  const pendingCount = usePendingVideosCount()

  useEffect(() => {
    setIsMounted(true)
  }, [])

  useEffect(() => {
    if (!isMounted) return
    try {
      localStorage.setItem("sidepanel-collapsed", String(isCollapsed))
      window.dispatchEvent(
        new CustomEvent("sidepanel-collapse-change", {
          detail: { isCollapsed },
        })
      )
    } catch (e) {}
  }, [isCollapsed, isMounted])

  const toggleCollapse = () => {
    setIsCollapsed((prev) => !prev)
  }

  const primaryNavItems = [
    { name: "Dashboard", href: "/", icon: Home },
    { name: "Channel", href: "/channel", icon: Podcast },
    { name: "Followed Channels", href: "/subscriptions/channels", icon: Rss },
    {
      name: "Subscriptions Videos",
      href: "/subscriptions/videos",
      icon: ListVideo,
    },
    { name: "Activity", href: "/activity", icon: Clock },
  ]

  const quickAddItems = [
    { name: "Quick Add", icon: Zap, type: "dialog" as const },
    {
      name: "Add from YouTube",
      href: "/episodes/add-from-youtube",
      icon: Video,
      type: "link" as const,
    },
    {
      name: "Upload Episode",
      href: "/episodes/add-from-upload",
      icon: Upload,
      type: "link" as const,
    },
  ]

  const utilityItems = [
    { name: "Dark/Light Theme", icon: null, type: "theme" as const },
    { name: "Settings", href: "/settings", icon: Settings },
  ]

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/"
    if (href === "/subscriptions/channels")
      return (
        pathname === "/subscriptions/channels" ||
        pathname.startsWith("/subscriptions/channels")
      )
    if (href === "/subscriptions/videos")
      return (
        pathname === "/subscriptions/videos" ||
        pathname.startsWith("/subscriptions/videos")
      )
    if (href === "/subscriptions") return pathname === "/subscriptions" // Only exact match for original page
    return pathname === href || pathname.startsWith(href)
  }

  // Theme toggle nav item component
  const ThemeNavItem = ({
    name,
    isCollapsed,
  }: {
    name: string
    isCollapsed: boolean
  }) => {
    const { theme, setTheme } = useTheme()
    const handleThemeChange = (e: React.MouseEvent) => {
      e.stopPropagation()
      setTheme(theme === "light" ? "dark" : "light")
    }
    const button = (
      <Button
        variant="ghost"
        className={cn(
          "flex items-center gap-3 w-full h-10 text-muted-foreground hover:text-foreground",
          isCollapsed ? "justify-center px-0" : "justify-start px-3"
        )}
        onClick={handleThemeChange}
      >
        {theme === "light" ? (
          <Sun className="h-6 w-6 flex-shrink-0 transition-all" />
        ) : (
          <Moon className="h-6 w-6 flex-shrink-0 transition-all" />
        )}
        {!isCollapsed && (
          <span className="flex items-center justify-start">{name}</span>
        )}
      </Button>
    )
    if (isCollapsed) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent side="right">
            <p>{name}</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    return button
  }

  const NavItem = ({
    name,
    href,
    icon: Icon,
    onClick,
    isActive: active,
    badge,
    type,
  }: {
    name: string
    href?: string
    icon: typeof Home | null
    onClick?: () => void
    isActive?: boolean
    badge?: number
    type?: "link" | "dialog" | "theme"
  }) => {
    // 🤖 All nav items use the same icon and text classes.
    const buttonContent = (
      <>
        {Icon && <Icon className="h-6 w-6 flex-shrink-0" />}
        {!isCollapsed && (
          <span className="flex items-center justify-start">{name}</span>
        )}
        {badge !== undefined && badge > 0 && (
          <Badge
            variant="destructive"
            className={cn(
              "h-5 min-w-5 flex items-center justify-center p-0 text-xs",
              isCollapsed && "absolute -top-1 -right-1"
            )}
          >
            {badge > 99 ? "99+" : badge}
          </Badge>
        )}
      </>
    )

    const handleClick = (e: React.MouseEvent) => {
      if (onClick) {
        e.stopPropagation()
        onClick()
      }
    }

    if (href && !onClick) {
      const linkElement = (
        <Link
          href={href}
          onClick={handleClick}
          className={cn(
            "flex items-center gap-3 w-full h-10 relative rounded-md transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            isCollapsed ? "justify-center px-0" : "justify-start px-3",
            active
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {buttonContent}
        </Link>
      )
      if (isCollapsed) {
        return (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="w-full">{linkElement}</div>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>{name}</p>
            </TooltipContent>
          </Tooltip>
        )
      }
      return linkElement
    }

    const button = (
      <Button
        variant={active ? "secondary" : "ghost"}
        className={cn(
          "flex items-center gap-3 w-full h-10",
          isCollapsed ? "justify-center px-0" : "justify-start px-3 text-md",
          active
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={handleClick}
      >
        {buttonContent}
      </Button>
    )

    if (isCollapsed) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent side="right">
            <p>{name}</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    return button
  }

  return (
    <>
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300",
          "hidden md:block",
          isCollapsed ? "w-16" : "w-64"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header with logo and collapse button */}
          <div className="flex h-16 items-center px-4 relative">
            {!isCollapsed ? (
              <>
                <Link href="/" className="flex items-center gap-3 flex-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Mic className="h-5 w-5" />
                  </div>
                  <span className="font-bold text-lg">LABCASTARR</span>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleCollapse}
                  className="h-8 w-8 p-0"
                  aria-label="Collapse side panel"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </>
            ) : (
              <button
                onClick={toggleCollapse}
                className="flex items-center justify-center w-full h-full hover:bg-muted/50 transition-colors"
                aria-label="Expand side panel"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-110">
                  <Mic className="h-5 w-5" />
                </div>
              </button>
            )}
          </div>

          {/* Navigation content */}
          <div className="flex-1 overflow-y-auto flex flex-col py-4">
            <div className="space-y-1 px-2 flex-1">
              {/* Primary Navigation */}
              {primaryNavItems.map((item) => {
                const active = isActive(item.href)
                return (
                  <NavItem
                    key={item.href}
                    name={item.name}
                    href={item.href}
                    icon={item.icon}
                    isActive={active}
                    type="link"
                  />
                )
              })}

              {/* Quick Add Section */}
              {quickAddItems.map((item) => {
                if (item.type === "dialog") {
                  return (
                    <NavItem
                      key={item.name}
                      name={item.name}
                      icon={item.icon}
                      onClick={() => setQuickAddOpen(true)}
                      type="dialog"
                    />
                  )
                }
                const active = isActive(item.href!)
                return (
                  <NavItem
                    key={item.href}
                    name={item.name}
                    href={item.href}
                    icon={item.icon}
                    isActive={active}
                    type="link"
                  />
                )
              })}
            </div>

            {/* Utility Section - Pushed to bottom */}
            <div className="space-y-1 px-2 mt-auto pt-4">
              {/* Notification Bell */}
              <NotificationBell collapsed={isCollapsed} />{" "}
              {utilityItems.map((item) => {
                if (item.type === "theme") {
                  return (
                    <ThemeNavItem
                      key={item.name}
                      name={item.name}
                      isCollapsed={isCollapsed}
                    />
                  )
                }
                const active = isActive(item.href!)
                return (
                  <NavItem
                    key={item.href}
                    name={item.name}
                    href={item.href}
                    icon={item.icon}
                    isActive={active}
                    type="link"
                  />
                )
              })}
            </div>
          </div>
        </div>
      </aside>

      {/* Quick Add Dialog */}
      <QuickAddDialog
        open={quickAddOpen}
        onOpenChange={setQuickAddOpen}
        onSuccess={() => {
          window.location.reload()
        }}
      />
    </>
  )
}
