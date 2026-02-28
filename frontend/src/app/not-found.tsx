'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Home, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 border-2 border-muted-foreground/20 shadow-lg">
        <div className="flex flex-col items-center justify-center space-y-6">
          {/* 404 Display */}
          <div className="text-center">
            <h1 className="text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/50 mb-2">
              404
            </h1>
            <p className="text-lg text-muted-foreground">Page Not Found</p>
          </div>

          {/* Description */}
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-semibold text-foreground">
              Oops! We couldn&apos;t find what you&apos;re looking for
            </h2>
            <p className="text-muted-foreground">
              The page you&apos;re trying to access doesn&apos;t exist or has been moved. Let&apos;s get you back on track!
            </p>
          </div>

          {/* Navigation Buttons */}
          <div className="flex flex-col gap-3 w-full pt-4">
            <Link href="/" className="w-full">
              <Button
                size="lg"
                className="w-full gap-2"
              >
                <Home className="w-4 h-4" />
                Back to Home
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="w-full gap-2"
              onClick={() => window.history.back()}
            >
              <ArrowLeft className="w-4 h-4" />
              Go Back
            </Button>
          </div>

          {/* Fun Message */}
          <div className="text-center pt-4 border-t border-muted-foreground/20">
            <p className="text-sm text-muted-foreground italic">
              🎙️ This page wandered off like an untagged podcast episode&hellip;
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
