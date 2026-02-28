'use client'

import { Suspense } from 'react'
import { MainLayout } from '@/components/layout/main-layout'
import { SearchInterface } from '@/components/features/search/search-interface'

export default function SearchPage() {
  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Search Episodes</h1>
          <p className="text-muted-foreground mt-2">
            Find episodes by title, description, tags, or keywords
          </p>
        </div>
        <Suspense fallback={<div>Loading search...</div>}>
          <SearchInterface />
        </Suspense>
      </div>
    </MainLayout>
  )
}