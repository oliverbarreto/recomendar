'use client'

import { use } from 'react'
import { MainLayout } from '@/components/layout/main-layout'
import { EpisodeDetail } from '@/components/features/episodes/episode-detail'

interface EpisodeDetailPageProps {
  params: Promise<{
    id: string
  }>
}

export default function EpisodeDetailPage({ params }: EpisodeDetailPageProps) {
  const { id } = use(params)

  return (
    <MainLayout>
      <EpisodeDetail episodeId={parseInt(id)} />
    </MainLayout>
  )
}