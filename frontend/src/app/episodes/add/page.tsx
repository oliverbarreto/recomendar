/**
 * Add Episode Choice Page
 * 
 * Simple landing page that directs users to either:
 * - Add episode from YouTube URL
 * - Upload audio file directly
 */
'use client'

import { MainLayout } from '@/components/layout/main-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Video, Upload, ArrowRight } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function AddEpisodePage() {
  const router = useRouter()

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">Add New Episode</h1>
          <p className="text-muted-foreground mt-2">
            Choose how you&apos;d like to create your podcast episode
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* YouTube Option */}
          <Card className="hover:border-primary transition-colors cursor-pointer" onClick={() => router.push('/episodes/add-from-youtube')}>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Video className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>From YouTube</CardTitle>
              </div>
              <CardDescription>
                Convert a YouTube video to a podcast episode automatically
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Paste any YouTube video URL</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Automatic audio extraction and conversion</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Metadata automatically populated</span>
                </li>
              </ul>
              <Button className="w-full" onClick={(e) => { e.stopPropagation(); router.push('/episodes/add-from-youtube'); }}>
                Add from YouTube
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </CardContent>
          </Card>

          {/* Upload Option */}
          <Card className="hover:border-primary transition-colors cursor-pointer" onClick={() => router.push('/episodes/add-from-upload')}>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Upload className="w-6 h-6 text-primary" />
                </div>
                <CardTitle>Upload Audio File</CardTitle>
              </div>
              <CardDescription>
                Upload your own audio file directly from your computer
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Drag & drop audio files</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Supports MP3, M4A, WAV, OGG, FLAC</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Full control over episode details</span>
                </li>
              </ul>
              <Button className="w-full" onClick={(e) => { e.stopPropagation(); router.push('/episodes/add-from-upload'); }}>
                Upload Audio File
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  )
}