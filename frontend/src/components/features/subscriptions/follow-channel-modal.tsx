/**
 * Follow Channel Modal Component
 * 
 * Modal form for following a YouTube channel with auto-approve options
 */
"use client"

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { Loader2, Youtube, Link as LinkIcon } from 'lucide-react'
import { useFollowChannel } from '@/hooks/use-followed-channels'
import { useChannels } from '@/hooks/use-channels'
import { toast } from 'sonner'
import { FollowedChannelCreateRequest } from '@/types'

const followChannelSchema = z.object({
    channel_url: z.string().url('Please enter a valid YouTube channel URL'),
    auto_approve: z.boolean().default(false),
    auto_approve_channel_id: z.number().optional(),
}).refine(
    (data) => !data.auto_approve || data.auto_approve_channel_id,
    {
        message: 'Please select a podcast channel for auto-approval',
        path: ['auto_approve_channel_id'],
    }
)

type FollowChannelFormData = z.infer<typeof followChannelSchema>

interface FollowChannelModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    defaultChannelUrl?: string
}

export function FollowChannelModal({
    open,
    onOpenChange,
    defaultChannelUrl = '',
}: FollowChannelModalProps) {
    const [isSubmitting, setIsSubmitting] = useState(false)
    const followChannelMutation = useFollowChannel()
    const { data: channelsData } = useChannels()
    const channels = channelsData?.data || []

    const form = useForm<FollowChannelFormData>({
        resolver: zodResolver(followChannelSchema),
        defaultValues: {
            channel_url: defaultChannelUrl,
            auto_approve: false,
            auto_approve_channel_id: undefined,
        },
    })

    const autoApprove = form.watch('auto_approve')

    const onSubmit = async (data: FollowChannelFormData) => {
        if (isSubmitting) return

        try {
            setIsSubmitting(true)

            // Build request, ensuring auto_approve is always a boolean (true/false)
            const request: FollowedChannelCreateRequest = {
                channel_url: data.channel_url,
                auto_approve: data.auto_approve ?? false, // Ensure it's always true or false, never undefined
                ...(data.auto_approve_channel_id !== undefined && { auto_approve_channel_id: data.auto_approve_channel_id }),
            }

            console.log('[FollowChannelModal] Submitting request:', {
                channel_url: request.channel_url,
                auto_approve: request.auto_approve,
                auto_approve_channel_id: request.auto_approve_channel_id,
                full_request: request
            })

            await followChannelMutation.mutateAsync(request)

            console.log('[FollowChannelModal] Successfully followed channel')
            form.reset()
            onOpenChange(false)
        } catch (error) {
            console.error('[FollowChannelModal] Error details:', {
                error,
                errorType: error?.constructor?.name,
                message: error instanceof Error ? error.message : 'Unknown error',
                stack: error instanceof Error ? error.stack : undefined,
                // Try to extract response details if available
                response: (error as any)?.response,
                status: (error as any)?.status,
                code: (error as any)?.code
            })
            // Error toast is handled by the mutation
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Youtube className="h-5 w-5 text-red-500" />
                        Follow YouTube Channel
                    </DialogTitle>
                    <DialogDescription>
                        Start monitoring this YouTube channel for new videos. New videos will appear in your subscriptions page.
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="channel_url"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>YouTube Channel URL</FormLabel>
                                    <FormControl>
                                        <div className="relative">
                                            <LinkIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                {...field}
                                                placeholder="https://www.youtube.com/@channelname or https://www.youtube.com/channel/..."
                                                className="pl-9"
                                            />
                                        </div>
                                    </FormControl>
                                    <FormDescription>
                                        Enter a YouTube channel URL or channel handle
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="auto_approve"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                                    <FormControl>
                                        <Checkbox
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                    <div className="space-y-1 leading-none">
                                        <FormLabel>Auto-approve all episodes</FormLabel>
                                        <FormDescription>
                                            Automatically create episodes from all new videos in this channel
                                        </FormDescription>
                                    </div>
                                </FormItem>
                            )}
                        />

                        {autoApprove && (
                            <FormField
                                control={form.control}
                                name="auto_approve_channel_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Podcast Channel</FormLabel>
                                        <Select
                                            onValueChange={(value) => field.onChange(parseInt(value))}
                                            value={field.value?.toString()}
                                        >
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select a podcast channel" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {channels.map((channel) => (
                                                    <SelectItem key={channel.id} value={channel.id.toString()}>
                                                        {channel.name}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>
                                            Select the podcast channel where episodes will be automatically created
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        <DialogFooter>
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                disabled={isSubmitting}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Following...
                                    </>
                                ) : (
                                    'Follow Channel'
                                )}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}

