'use client'

import { useAuth } from '@/contexts/auth-context'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect, ReactNode } from 'react'

interface AuthGuardProps {
  children: ReactNode
}

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login']

// Routes that redirect to home if authenticated (like login page)
const AUTH_REDIRECT_ROUTES = ['/login']

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading, isRefreshing } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (isLoading) return // Wait for auth to initialize

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname)
    const isAuthRedirectRoute = AUTH_REDIRECT_ROUTES.includes(pathname)

    if (!isAuthenticated && !isPublicRoute) {
      // Redirect to login if not authenticated and trying to access protected route
      router.push('/login')
    } else if (isAuthenticated && isAuthRedirectRoute) {
      // Redirect to home if authenticated and trying to access login page
      router.push('/')
    }
  }, [isAuthenticated, isLoading, pathname, router])

  // Show loading state ONLY during initial auth initialization
  // Do NOT block UI during token refresh - let it happen in background
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Allow public routes regardless of auth status
  if (PUBLIC_ROUTES.includes(pathname)) {
    return <>{children}</>
  }

  // Require authentication for all other routes
  if (!isAuthenticated) {
    return null // Will redirect in useEffect
  }

  return <>{children}</>
}

// Higher-order component for protecting specific pages
export function withAuth<T extends object>(Component: React.ComponentType<T>) {
  return function AuthenticatedComponent(props: T) {
    return (
      <AuthGuard>
        <Component {...props} />
      </AuthGuard>
    )
  }
}

// Protected route wrapper component
export function ProtectedRoute({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>
}