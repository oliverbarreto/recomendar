"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { toast } from 'sonner'

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Toggle } from '@/components/ui/toggle'
import { useCreateChannel, useUpdateChannel } from '@/hooks/use-channels'
import { Channel, ChannelCreateRequest, ChannelUpdateRequest } from '@/types'

const createChannelSchema = z.object({
  user_id: z.number().min(1),
  name: z.string().min(1, 'Channel name is required').max(255),
  description: z.string().min(1, 'Description is required'),
  author_name: z.string().optional(),
  author_email: z.string().email('Invalid email').optional().or(z.literal('')),
})

const updateChannelSchema = z.object({
  name: z.string().min(1, 'Channel name is required').max(255).optional(),
  description: z.string().min(1, 'Description is required').optional(),
  website_url: z.string().url('Invalid URL').optional().or(z.literal('')),
  image_url: z.string().url('Invalid image URL').optional().or(z.literal('')),
  category: z.string().optional(),
  language: z.string().min(2).max(2, 'Language must be 2 characters (ISO 639-1)').optional(),
  explicit_content: z.boolean().optional(),
  author_name: z.string().optional(),
  author_email: z.string().email('Invalid email').optional().or(z.literal('')),
  owner_name: z.string().optional(),
  owner_email: z.string().email('Invalid email').optional().or(z.literal('')),
})

type CreateChannelForm = z.infer<typeof createChannelSchema>
type UpdateChannelForm = z.infer<typeof updateChannelSchema>

interface ChannelFormProps {
  channel?: Channel
  userId?: number
  onSuccess?: (channel: Channel) => void
  onCancel?: () => void
}

export function ChannelForm({ channel, userId = 1, onSuccess, onCancel }: ChannelFormProps) {
  const [isExplicit, setIsExplicit] = useState(channel?.explicit_content ?? false)
  
  const createMutation = useCreateChannel()
  const updateMutation = useUpdateChannel()
  
  const isEditing = !!channel
  const isLoading = createMutation.isPending || updateMutation.isPending

  const form = useForm<CreateChannelForm | UpdateChannelForm>({
    resolver: zodResolver(isEditing ? updateChannelSchema : createChannelSchema),
    defaultValues: isEditing
      ? {
          name: channel?.name || '',
          description: channel?.description || '',
          website_url: channel?.website_url || '',
          image_url: channel?.image_url || '',
          category: channel?.category || 'Technology',
          language: channel?.language || 'en',
          explicit_content: channel?.explicit_content || false,
          author_name: channel?.author_name || '',
          author_email: channel?.author_email || '',
          owner_name: channel?.owner_name || '',
          owner_email: channel?.owner_email || '',
        }
      : {
          user_id: userId,
          name: '',
          description: '',
          author_name: '',
          author_email: '',
        },
  })

  const onSubmit = async (data: CreateChannelForm | UpdateChannelForm) => {
    try {
      let result: Channel
      
      if (isEditing && channel) {
        result = await updateMutation.mutateAsync({
          id: channel.id,
          data: { ...data, explicit_content: isExplicit } as ChannelUpdateRequest,
        })
        toast.success('Channel updated successfully!')
      } else {
        result = await createMutation.mutateAsync({
          ...data,
          explicit_content: isExplicit,
        } as ChannelCreateRequest)
        toast.success('Channel created successfully!')
      }
      
      onSuccess?.(result)
    } catch (error) {
      console.error('Channel operation failed:', error)
      toast.error(isEditing ? 'Failed to update channel' : 'Failed to create channel')
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>
          {isEditing ? 'Edit Channel Settings' : 'Create New Channel'}
        </CardTitle>
        <CardDescription>
          {isEditing 
            ? 'Update your podcast channel settings and RSS feed configuration'
            : 'Create a new podcast channel for your content'
          }
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Basic Information</h3>
              
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Channel Name</FormLabel>
                    <FormControl>
                      <Input placeholder="My Awesome Podcast" {...field} />
                    </FormControl>
                    <FormDescription>
                      The name of your podcast channel
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Tell your audience what your podcast is about..."
                        className="min-h-[100px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      A compelling description of your podcast content
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Extended Settings (only for editing) */}
            {isEditing && (
              <>
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Channel Details</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="website_url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Website URL</FormLabel>
                          <FormControl>
                            <Input placeholder="https://example.com" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="image_url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Podcast Image URL</FormLabel>
                          <FormControl>
                            <Input placeholder="https://example.com/image.jpg" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="category"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Category</FormLabel>
                          <FormControl>
                            <Input placeholder="Technology" {...field} />
                          </FormControl>
                          <FormDescription>iTunes podcast category</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="language"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Language</FormLabel>
                          <FormControl>
                            <Input placeholder="en" maxLength={2} {...field} />
                          </FormControl>
                          <FormDescription>ISO 639-1 language code</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Author Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="author_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Author Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="author_email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Author Email</FormLabel>
                          <FormControl>
                            <Input type="email" placeholder="john@example.com" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="owner_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Owner Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} />
                          </FormControl>
                          <FormDescription>Podcast owner (for iTunes)</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="owner_email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Owner Email</FormLabel>
                          <FormControl>
                            <Input type="email" placeholder="john@example.com" {...field} />
                          </FormControl>
                          <FormDescription>Podcast owner email (for iTunes)</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Content Settings</h3>
                  
                  <div className="flex items-center space-x-2">
                    <Toggle
                      pressed={isExplicit}
                      onPressedChange={setIsExplicit}
                      aria-label="Toggle explicit content"
                    >
                      {isExplicit ? 'Explicit' : 'Clean'}
                    </Toggle>
                    <span className="text-sm text-muted-foreground">
                      Mark if your podcast contains explicit content
                    </span>
                  </div>
                </div>
              </>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-4 pt-6 border-t">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={isLoading}>
                {isLoading
                  ? isEditing
                    ? 'Updating...'
                    : 'Creating...'
                  : isEditing
                  ? 'Update Channel'
                  : 'Create Channel'
                }
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}