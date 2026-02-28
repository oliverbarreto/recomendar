/**
 * Mobile navigation component with hamburger menu and drawer
 */
"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { Moon, Sun, Menu, X, Mic } from "lucide-react"
import { NotificationBell } from "@/components/layout/notification-bell"
import {
  Home,
  Podcast,
  Zap,
  Video,
  Upload,
  Settings,
  Rss,
  ListVideo,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { QuickAddDialog } from "@/components/features/episodes/quick-add-dialog"

export function MobileNav() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const [quickAddOpen, setQuickAddOpen] = useState(false)

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
    return pathname === href || pathname.startsWith(href)
  }

  const handleLinkClick = () => {
    setIsOpen(false)
  }

  const handleQuickAddClick = () => {
    setQuickAddOpen(true)
    setIsOpen(false)
  }

  const handleThemeToggle = () => {
    setTheme(theme === "light" ? "dark" : "light")
  }

  return (
    <>
      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2" onClick={handleLinkClick}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Mic className="h-4 w-4" />
            </div>
            <span className="font-bold text-lg">LABCASTARR</span>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
            className="h-8 w-8 p-0"
            aria-label="Toggle mobile menu"
          >
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      <div
        className={cn(
          "fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity duration-300",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsOpen(false)}
      />
      <div
        className={cn(
          "fixed left-0 top-0 bottom-0 z-50 w-64 bg-background border-r shadow-lg transform transition-transform duration-300 ease-in-out md:hidden overflow-y-auto",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex h-14 items-center justify-between px-4 border-b">
                <Link
                  href="/"
                  className="flex items-center gap-2"
                  onClick={handleLinkClick}
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                    <Mic className="h-4 w-4" />
                  </div>
                  <span className="font-bold text-lg">LABCASTARR</span>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Navigation Content */}
              <div className="flex-1 overflow-y-auto flex flex-col py-4">
                <div className="space-y-1 px-2 flex-1">
                  {/* Primary Navigation */}
                  {primaryNavItems.map((item) => {
                    const active = isActive(item.href)
                    const Icon = item.icon
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={handleLinkClick}
                        className={cn(
                          "flex items-center gap-3 w-full h-10 px-3 rounded-md transition-colors",
                          "hover:bg-accent hover:text-accent-foreground",
                          active
                            ? "bg-muted text-foreground"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <Icon className="h-5 w-5 flex-shrink-0" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}

                  {/* Quick Add Section */}
                  {quickAddItems.map((item) => {
                    const Icon = item.icon
                    if (item.type === "dialog") {
                      return (
                        <Button
                          key={item.name}
                          variant="ghost"
                          className={cn(
                            "flex items-center gap-3 w-full h-10 px-3 justify-start",
                            "text-muted-foreground hover:text-foreground"
                          )}
                          onClick={handleQuickAddClick}
                        >
                          <Icon className="h-5 w-5 flex-shrink-0" />
                          <span>{item.name}</span>
                        </Button>
                      )
                    }
                    const active = isActive(item.href!)
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={handleLinkClick}
                        className={cn(
                          "flex items-center gap-3 w-full h-10 px-3 rounded-md transition-colors",
                          "hover:bg-accent hover:text-accent-foreground",
                          active
                            ? "bg-muted text-foreground"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <Icon className="h-5 w-5 flex-shrink-0" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </div>

                {/* Utility Section - Pushed to bottom */}
                <div className="space-y-1 px-2 mt-auto pt-4 border-t">
                  {/* Notification Bell */}
                  <div className="flex items-center justify-start py-1 px-3">
                    <NotificationBell collapsed={false} />
                  </div>

                  {/* Theme Toggle */}
                  <Button
                    variant="ghost"
                    className={cn(
                      "flex items-center gap-3 w-full h-10 px-3 justify-start",
                      "text-muted-foreground hover:text-foreground"
                    )}
                    onClick={handleThemeToggle}
                  >
                    {theme === "light" ? (
                      <Sun className="h-5 w-5 flex-shrink-0" />
                    ) : (
                      <Moon className="h-5 w-5 flex-shrink-0" />
                    )}
                    <span>Dark/Light Theme</span>
                  </Button>

                  {/* Settings */}
                  {utilityItems.map((item) => {
                    const Icon = item.icon
                    const active = isActive(item.href!)
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={handleLinkClick}
                        className={cn(
                          "flex items-center gap-3 w-full h-10 px-3 rounded-md transition-colors",
                          "hover:bg-accent hover:text-accent-foreground",
                          active
                            ? "bg-muted text-foreground"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <Icon className="h-5 w-5 flex-shrink-0" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

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

