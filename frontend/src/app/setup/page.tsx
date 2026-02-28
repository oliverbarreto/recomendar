'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { CreateChannelForm } from '@/components/features/channels/create-channel-form'

export default function SetupPage() {
  return (
    <MainLayout>
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Create Your Podcast Channel</h1>
            <p className="text-muted-foreground">
              Set up your first podcast channel to start converting YouTube videos to episodes.
            </p>
          </div>
          <CreateChannelForm />
        </div>
      </div>
    </MainLayout>
  )
}