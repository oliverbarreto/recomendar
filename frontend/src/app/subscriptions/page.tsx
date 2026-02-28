/**
 * Subscriptions Page
 * 
 * Main page for managing followed channels and discovered videos
 */
"use client"

import React, { useState } from 'react'
import { MainLayout } from '@/components/layout/main-layout'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { VideoList } from '@/components/features/subscriptions/video-list'
import { FollowedChannelsList } from '@/components/features/subscriptions/followed-channels-list'
import { FollowChannelModal } from '@/components/features/subscriptions/follow-channel-modal'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { PageHeader } from '@/components/layout/page-header'

export default function SubscriptionsPage() {
    const [followModalOpen, setFollowModalOpen] = useState(false)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

    return (
        <MainLayout>
            <div className="container mx-auto py-6 space-y-6">
                <PageHeader
                    title="Subscriptions"
                    description="Manage followed YouTube channels and discover new videos"
                >
                    <Button onClick={() => setFollowModalOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Follow Channel
                    </Button>
                </PageHeader>

                <Tabs defaultValue="channels" className="space-y-4">
                    <TabsList>
                        <TabsTrigger value="channels">Followed Channels</TabsTrigger>
                        <TabsTrigger value="videos">Videos</TabsTrigger>
                    </TabsList>

                    <TabsContent value="channels" className="space-y-4">
                        <FollowedChannelsList />
                    </TabsContent>

                    <TabsContent value="videos" className="space-y-4">
                        <VideoList
                            viewMode={viewMode}
                            onViewModeChange={setViewMode}
                        />
                    </TabsContent>
                </Tabs>

                <FollowChannelModal
                    open={followModalOpen}
                    onOpenChange={setFollowModalOpen}
                />
            </div>
        </MainLayout>
    )
}

