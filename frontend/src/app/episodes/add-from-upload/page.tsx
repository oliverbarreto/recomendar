/**
 * Upload Audio Episode Page
 * 
 * Dedicated page for uploading audio files directly to create podcast episodes.
 * Supports MP3, M4A, WAV, OGG, and FLAC formats.
 */
'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { UploadEpisodeForm } from '@/components/features/episodes/upload-episode-form'

export default function AddFromUploadPage() {
    return (
        <MainLayout>
            <div className="max-w-3xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold tracking-tight">Upload Audio Episode</h1>
                    <p className="text-muted-foreground mt-2">
                        Upload your own audio file (MP3, M4A, WAV, OGG, FLAC) to create an episode
                    </p>
                </div>
                <UploadEpisodeForm
                    channelId={1}
                    onSuccess={() => {
                        window.location.href = '/channel'
                    }}
                />
            </div>
        </MainLayout>
    )
}

