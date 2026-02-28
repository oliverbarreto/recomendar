/**
 * Followed Channels Page
 *
 * Page for managing followed YouTube channels
 */
"use client"

import React, { useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { PageHeader } from "@/components/layout/page-header"
import { FollowedChannelsList } from "@/components/features/subscriptions/followed-channels-list"
import { FollowChannelModal } from "@/components/features/subscriptions/follow-channel-modal"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function FollowedChannelsPage() {
  const [followModalOpen, setFollowModalOpen] = useState(false)

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <PageHeader
          title="Followed Channels"
          description="Manage followed YouTube channels and discover new videos"
        >
          <Button onClick={() => setFollowModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Follow Channel
          </Button>
        </PageHeader>

        <FollowedChannelsList />

        <FollowChannelModal
          open={followModalOpen}
          onOpenChange={setFollowModalOpen}
        />
      </div>
    </MainLayout>
  )
}
