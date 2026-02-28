"use client"

import { useState } from 'react'
import { toast } from 'sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useFeedInfo, useValidateFeed, useRssFeed } from '@/hooks/use-feeds'
import { useChannelStatistics } from '@/hooks/use-channels'
import { FeedValidationResponse } from '@/types'
import { ExternalLink, RefreshCw, CheckCircle, AlertTriangle, XCircle, Copy } from 'lucide-react'

interface FeedManagementProps {
  channelId: number
}

export function FeedManagement({ channelId }: FeedManagementProps) {
  const [validationResult, setValidationResult] = useState<FeedValidationResponse | null>(null)
  const [showRssFeed, setShowRssFeed] = useState(false)
  
  const { data: feedInfo, isLoading: feedInfoLoading } = useFeedInfo(channelId)
  const { data: channelStats } = useChannelStatistics(channelId)
  const { data: rssFeedXml, isLoading: rssFeedLoading } = useRssFeed(channelId, 50)
  const validateMutation = useValidateFeed()

  const handleValidate = async () => {
    try {
      const result = await validateMutation.mutateAsync(channelId)
      setValidationResult(result)
      toast.success('Feed validation completed!')
    } catch (error) {
      console.error('Feed validation failed:', error)
      toast.error('Failed to validate RSS feed')
    }
  }

  const handleCopyFeedUrl = () => {
    if (feedInfo?.feed_url) {
      navigator.clipboard.writeText(feedInfo.feed_url)
      toast.success('Feed URL copied to clipboard!')
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusIcon = (isValid: boolean) => {
    if (isValid) {
      return <CheckCircle className="h-4 w-4 text-green-600" />
    }
    return <XCircle className="h-4 w-4 text-red-600" />
  }

  if (feedInfoLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading feed information...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!feedInfo) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No feed information available
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Feed Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            RSS Feed Information
            <Badge variant={feedInfo.episode_count > 0 ? 'default' : 'secondary'}>
              {feedInfo.episode_count} episodes
            </Badge>
          </CardTitle>
          <CardDescription>
            Manage and monitor your podcast RSS feed
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Feed URL</label>
              <div className="flex items-center space-x-2 mt-1">
                <code className="flex-1 text-sm bg-muted p-2 rounded truncate">
                  {feedInfo.feed_url}
                </code>
                <Button size="sm" variant="outline" onClick={handleCopyFeedUrl}>
                  <Copy className="h-3 w-3" />
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <a href={feedInfo.feed_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">Latest Episode</label>
              <div className="mt-1">
                {feedInfo.latest_episode_title ? (
                  <div>
                    <div className="text-sm font-medium">{feedInfo.latest_episode_title}</div>
                    <div className="text-xs text-muted-foreground">
                      {feedInfo.latest_episode_date && 
                        new Date(feedInfo.latest_episode_date).toLocaleDateString()
                      }
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">No episodes yet</div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Feed Validation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Feed Validation
            <Button 
              onClick={handleValidate} 
              disabled={validateMutation.isPending}
              size="sm"
            >
              {validateMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Validate Feed
                </>
              )}
            </Button>
          </CardTitle>
          <CardDescription>
            Check your RSS feed against iTunes Podcast specifications
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {validationResult ? (
            <div className="space-y-4">
              {/* Validation Score */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(validationResult.is_valid)}
                  <span className="font-medium">
                    {validationResult.is_valid ? 'Valid Feed' : 'Issues Found'}
                  </span>
                </div>
                <div className={`text-lg font-bold ${getScoreColor(validationResult.score)}`}>
                  {validationResult.score}/100
                </div>
              </div>

              <Progress value={validationResult.score} className="w-full" />

              {/* Validation Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="font-medium">Episodes</div>
                  <div className="text-muted-foreground">
                    {validationResult.validation_details.total_episodes}
                  </div>
                </div>
                <div>
                  <div className="font-medium">Channel</div>
                  <div className={validationResult.validation_details.channel_complete ? 'text-green-600' : 'text-red-600'}>
                    {validationResult.validation_details.channel_complete ? 'Complete' : 'Incomplete'}
                  </div>
                </div>
                <div>
                  <div className="font-medium">iTunes</div>
                  <div className={validationResult.validation_details.itunes_complete ? 'text-green-600' : 'text-red-600'}>
                    {validationResult.validation_details.itunes_complete ? 'Complete' : 'Incomplete'}
                  </div>
                </div>
                <div>
                  <div className="font-medium">Episodes Valid</div>
                  <div className={validationResult.validation_details.episodes_valid ? 'text-green-600' : 'text-red-600'}>
                    {validationResult.validation_details.episodes_valid ? 'Yes' : 'No'}
                  </div>
                </div>
              </div>

              <Separator />

              {/* Errors */}
              {validationResult.errors.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-600 flex items-center mb-2">
                    <XCircle className="h-4 w-4 mr-2" />
                    Errors ({validationResult.errors.length})
                  </h4>
                  <ul className="space-y-1 text-sm">
                    {validationResult.errors.map((error, index) => (
                      <li key={index} className="text-red-600">• {error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings */}
              {validationResult.warnings.length > 0 && (
                <div>
                  <h4 className="font-medium text-yellow-600 flex items-center mb-2">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Warnings ({validationResult.warnings.length})
                  </h4>
                  <ul className="space-y-1 text-sm">
                    {validationResult.warnings.map((warning, index) => (
                      <li key={index} className="text-yellow-600">• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {validationResult.recommendations.length > 0 && (
                <div>
                  <h4 className="font-medium text-blue-600 flex items-center mb-2">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Recommendations ({validationResult.recommendations.length})
                  </h4>
                  <ul className="space-y-1 text-sm">
                    {validationResult.recommendations.map((rec, index) => (
                      <li key={index} className="text-blue-600">• {rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="text-xs text-muted-foreground">
                Last validated: {new Date(validationResult.validated_at).toLocaleString()}
              </div>
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              Click &quot;Validate Feed&quot; to check your RSS feed for iTunes compliance
            </div>
          )}
        </CardContent>
      </Card>

      {/* Channel Statistics */}
      {channelStats && (
        <Card>
          <CardHeader>
            <CardTitle>Channel Statistics</CardTitle>
            <CardDescription>
              Overview of your channel content and performance
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {channelStats.published_episodes}
                </div>
                <div className="text-sm text-muted-foreground">Published</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {channelStats.processing_episodes}
                </div>
                <div className="text-sm text-muted-foreground">Processing</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">
                  {channelStats.draft_episodes}
                </div>
                <div className="text-sm text-muted-foreground">Draft</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {channelStats.total_episodes}
                </div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium">Total Duration</div>
                <div className="text-muted-foreground">
                  {Math.floor(channelStats.total_duration_seconds / 3600)}h {Math.floor((channelStats.total_duration_seconds % 3600) / 60)}m
                </div>
              </div>
              <div>
                <div className="font-medium">Total Size</div>
                <div className="text-muted-foreground">
                  {(channelStats.total_size_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* View Raw RSS Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Raw RSS Feed
            <Dialog open={showRssFeed} onOpenChange={setShowRssFeed}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  View XML
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
                <DialogHeader>
                  <DialogTitle>RSS Feed XML</DialogTitle>
                  <DialogDescription>
                    Raw XML content of your RSS feed
                  </DialogDescription>
                </DialogHeader>
                <div className="overflow-auto max-h-[60vh]">
                  {rssFeedLoading ? (
                    <div className="flex items-center space-x-2 p-4">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Loading RSS feed...</span>
                    </div>
                  ) : (
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                      {rssFeedXml}
                    </pre>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </CardTitle>
          <CardDescription>
            Preview and inspect your RSS feed XML
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}