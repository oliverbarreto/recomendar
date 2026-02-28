/**
 * Channel creation form component
 */
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { ArrowLeft, Loader2, Podcast } from 'lucide-react'
import { channelApi } from '@/lib/api'
import { toast } from 'sonner'
import type { ChannelCreateRequest } from '@/types'

const channelFormSchema = z.object({
  name: z.string()
    .min(1, 'Channel name is required')
    .max(100, 'Channel name must be less than 100 characters'),
  description: z.string()
    .min(10, 'Description must be at least 10 characters')
    .max(1000, 'Description must be less than 1000 characters'),
  author_name: z.string()
    .min(1, 'Author name is required')
    .max(100, 'Author name must be less than 100 characters')
    .optional(),
  author_email: z.string()
    .email('Please enter a valid email address')
    .optional(),
})

type ChannelFormData = z.infer<typeof channelFormSchema>

export function CreateChannelForm() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<ChannelFormData>({
    resolver: zodResolver(channelFormSchema),
    defaultValues: {
      name: '',
      description: '',
      author_name: '',
      author_email: '',
    },
  })

  const onSubmit = async (data: ChannelFormData) => {
    if (isSubmitting) return

    try {
      setIsSubmitting(true)
      
      // Create channel request with default user_id of 1 for now
      const channelRequest: ChannelCreateRequest = {
        user_id: 1,
        name: data.name,
        description: data.description,
        author_name: data.author_name,
        author_email: data.author_email,
      }

      const channel = await channelApi.create(channelRequest)
      
      toast.success('Channel created successfully!')

      // Redirect to the main dashboard
      router.push('/')
    } catch (error) {
      console.error('Error creating channel:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create channel'
      toast.error(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Podcast className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle>Channel Information</CardTitle>
              <CardDescription>
                Basic information about your podcast channel
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Channel Name *</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g., My Tech Podcast"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      This will be the title of your podcast channel
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
                    <FormLabel>Description *</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe what your podcast is about..."
                        className="min-h-[100px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      A detailed description that will appear in podcast directories
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="author_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Author Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Your name or your organization"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      The name that will appear as the podcast author
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="author_email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Contact Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="your.email@example.com"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Contact email for your podcast (required by some podcast directories)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  className="gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="gap-2 flex-1"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating Channel...
                    </>
                  ) : (
                    <>
                      <Podcast className="h-4 w-4" />
                      Create Channel
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="text-sm text-muted-foreground">
            <h4 className="font-medium mb-2">What happens next?</h4>
            <ol className="list-decimal list-inside space-y-1">
              <li>Your channel will be created with RSS feed generation</li>
              <li>You&apos;ll be able to add YouTube videos as podcast episodes</li>
              <li>Episodes will be automatically processed and added to your feed</li>
              <li>You can share your RSS feed with podcast platforms</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}