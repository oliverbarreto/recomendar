'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { SettingsInterface } from '@/components/features/settings/settings-interface'

export default function SettingsPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Configure your channel, RSS feed, and application preferences
          </p>
        </div>
        <SettingsInterface />
      </div>
    </MainLayout>
  )
}