/**
 * Application header component with navigation and theme toggle
 */
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/shared/theme-toggle'
import {
  Settings,
  Podcast,
  Menu,
  X,
  Zap,
  Search,
  Video,
  Upload,
  Bell
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { QuickAddDialog } from '@/components/features/episodes/quick-add-dialog'
import { usePendingVideosCount } from '@/hooks/use-youtube-videos'
import { Badge } from '@/components/ui/badge'

/**
 * Navigation items configuration with unified structure
 * Supports both link navigation and dialog actions
 */
const navigationItems = [
  { name: 'Channel', href: '/channel', icon: Podcast, type: 'link' as const },
  { name: 'Quick Add', icon: Zap, type: 'dialog' as const, action: 'quickAdd' as const },
  { name: 'Add from YouTube', href: '/episodes/add-from-youtube', icon: Video, type: 'link' as const },
  { name: 'Upload Audio', href: '/episodes/add-from-upload', icon: Upload, type: 'link' as const },
  { name: 'Subscriptions', href: '/subscriptions', icon: Bell, type: 'link' as const },
  // { name: 'Search', href: '/search', icon: Search, type: 'link' as const },
]

interface HeaderProps {
  onSearchToggle?: () => void
  showSearchButton?: boolean
}

export function Header({ onSearchToggle, showSearchButton = false }: HeaderProps) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [quickAddOpen, setQuickAddOpen] = useState(false)
  const pendingCount = usePendingVideosCount()

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <span className="text-sm font-bold">LC</span>
            </div>
            <span className="hidden font-bold sm:inline-block">LabCastARR</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navigationItems.map((item) => {
              const Icon = item.icon

              if (item.type === 'dialog') {
                return (
                  <Button
                    key={item.name}
                    variant="ghost"
                    size="sm"
                    onClick={() => setQuickAddOpen(true)}
                    className="flex items-center space-x-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Button>
                )
              }

              const isActive = pathname === item.href || (item.href === '/subscriptions' && pathname.startsWith('/subscriptions'))
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    size="sm"
                    className={cn(
                      "flex items-center space-x-2",
                      isActive && "bg-secondary"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Button>
                </Link>
              )
            })}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-2">
            {/* Search Button - only on channel page */}
            {showSearchButton && onSearchToggle && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onSearchToggle}
                className="h-8 w-8 p-0"
                title="Search Episodes (Cmd+F)"
              >
                <Search className="h-4 w-4" />
              </Button>
            )}

            {/* Notification Bell */}
            <Link href="/subscriptions?filter=pending">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-8 w-8 p-0 relative",
                  pathname === "/subscriptions" && "bg-secondary"
                )}
                title="Subscriptions"
              >
                <Bell className="h-4 w-4" />
                {pendingCount > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                  >
                    {pendingCount > 99 ? '99+' : pendingCount}
                  </Badge>
                )}
              </Button>
            </Link>

            {/* Theme Toggle Button */}
            <ThemeToggle />

            {/* Settings Button */}
            <Link href="/settings">
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-8 w-8 p-0",
                  pathname === "/settings" && "bg-secondary"
                )}
              >
                <Settings className="h-4 w-4" />
              </Button>
            </Link>

            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="border-t md:hidden">
            <nav className="max-w-7xl mx-auto px-4 py-2">
              <div className="grid gap-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon

                  if (item.type === 'dialog') {
                    return (
                      <Button
                        key={item.name}
                        variant="default"
                        size="sm"
                        onClick={() => {
                          setQuickAddOpen(true)
                          setMobileMenuOpen(false)
                        }}
                        className="w-full justify-start space-x-2"
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.name}</span>
                      </Button>
                    )
                  }

                  const isActive = pathname === item.href || (item.href === '/subscriptions' && pathname.startsWith('/subscriptions'))
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Button
                        variant={isActive ? "secondary" : "ghost"}
                        size="sm"
                        className={cn(
                          "w-full justify-start space-x-2",
                          isActive && "bg-secondary"
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.name}</span>
                      </Button>
                    </Link>
                  )
                })}

                {/* Search for Mobile */}
                {showSearchButton && onSearchToggle && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      onSearchToggle()
                      setMobileMenuOpen(false)
                    }}
                    className="w-full justify-start space-x-2"
                  >
                    <Search className="h-4 w-4" />
                    <span>Search Episodes</span>
                  </Button>
                )}

                {/* Settings for Mobile */}
                <Link
                  href="/settings"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Button
                    variant={pathname === "/settings" ? "secondary" : "ghost"}
                    size="sm"
                    className={cn(
                      "w-full justify-start space-x-2",
                      pathname === "/settings" && "bg-secondary"
                    )}
                  >
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </Button>
                </Link>
              </div>
            </nav>
          </div>
        )}
      </header>

      {/* Quick Add Dialog */}
      <QuickAddDialog
        open={quickAddOpen}
        onOpenChange={setQuickAddOpen}
        onSuccess={() => {
          // Optionally trigger a refresh of the current page
          window.location.reload()
        }}
      />
    </>
  )
}