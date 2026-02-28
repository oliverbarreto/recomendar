/**
 * Videos Page
 *
 * Page for managing discovered YouTube videos
 */
"use client"

import React, { useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { PageHeader } from "@/components/layout/page-header"
import { VideoList } from "@/components/features/subscriptions/video-list"
import { FollowChannelModal } from "@/components/features/subscriptions/follow-channel-modal"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function VideosPage() {
  const [followModalOpen, setFollowModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <PageHeader
          title="Videos"
          description="Discover and manage YouTube videos from followed channels"
        >
          <Button onClick={() => setFollowModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Follow Channel
          </Button>
        </PageHeader>

        <VideoList viewMode={viewMode} onViewModeChange={setViewMode} />

        <FollowChannelModal
          open={followModalOpen}
          onOpenChange={setFollowModalOpen}
        />
      </div>
    </MainLayout>
  )
}
