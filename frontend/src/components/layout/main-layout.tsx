/**
 * Main layout component for the application
 */
'use client'

import { ReactNode, useState, useEffect } from 'react'
import { SidePanel } from './sidepanel'
import { MobileNav } from './mobile-nav'
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: ReactNode
  onSearchToggle?: () => void
  showSearchButton?: boolean
}

export function MainLayout({ children, onSearchToggle, showSearchButton }: MainLayoutProps) {
  // Initialize collapse state from localStorage using lazy initializer to prevent hydration mismatch
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem('sidepanel-collapsed')
      return saved === 'true'
    } catch (e) {
      // localStorage might not be available in some environments
      return false
    }
  })

  const [isMounted, setIsMounted] = useState(false)

  // Mark component as mounted for SSR safety
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Listen for collapse state changes from SidePanel custom events
  useEffect(() => {
    const handleCollapseChange = (event: any) => {
      if (event.detail && typeof event.detail.isCollapsed === 'boolean') {
        setIsCollapsed(event.detail.isCollapsed)
      }
    }

    window.addEventListener('sidepanel-collapse-change', handleCollapseChange)
    return () => window.removeEventListener('sidepanel-collapse-change', handleCollapseChange)
  }, [])

  return (
    <div className="min-h-screen bg-background flex">
      <SidePanel />
      <MobileNav />
      <main
        className={cn(
          'flex-1 transition-all duration-300 py-6 overflow-x-hidden',
          'pt-20 md:pt-6', // Add top padding on mobile for fixed header
          'md:transition-all md:duration-300',
          isMounted && (isCollapsed ? 'md:ml-16' : 'md:ml-64')
        )}
      >
        <div className="max-w-7xl mx-auto px-4 w-full">
          {children}
        </div>
      </main>
    </div>
  )
}