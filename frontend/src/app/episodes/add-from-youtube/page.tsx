/**
 * Add Episode from YouTube URL Page
 * 
 * Dedicated page for creating podcast episodes from YouTube videos.
 * Users can paste a YouTube URL to automatically download and convert the audio.
 */
'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { AddEpisodeForm } from '@/components/features/episodes/add-episode-form'

export default function AddFromYouTubePage() {
    return (
        <MainLayout>
            <div className="max-w-3xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold tracking-tight">Add Episode from YouTube</h1>
                    <p className="text-muted-foreground mt-2">
                        Provide a YouTube video URL to automatically download and convert to a podcast episode
                    </p>
                </div>
                <AddEpisodeForm />
            </div>
        </MainLayout>
    )
}

