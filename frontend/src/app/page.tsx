'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { ChannelDashboard } from '@/components/features/channel-dashboard'

export default function Home() {
  return (
    <MainLayout>
      <ChannelDashboard />
    </MainLayout>
  )
}
