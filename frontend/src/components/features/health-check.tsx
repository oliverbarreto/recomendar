/**
 * Health check component for testing API connectivity
 */
'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Separator } from '@/components/ui/separator'
import { LoadingSpinner } from '@/components/shared/loading'
import { useHealth, useHealthDatabase, useHealthDetailed } from '@/hooks/use-health'
import { RefreshCw, FileJson } from 'lucide-react'
import { cn } from '@/lib/utils'

export function HealthCheck() {
  const { data: basicHealth, isLoading: basicLoading, error: basicError, refetch: refetchBasic } = useHealth()
  const { data: dbHealth, isLoading: dbLoading, error: dbError, refetch: refetchDb } = useHealthDatabase()
  const { data: detailedHealth, isLoading: detailedLoading, error: detailedError, refetch: refetchDetailed } = useHealthDetailed()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'unhealthy':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            API Health Check
            <Button
              variant="ghost"
              size="sm"
              disabled={basicLoading || dbLoading || detailedLoading}
              onClick={() => {
                refetchBasic()
                refetchDb()
                refetchDetailed()
              }}
            >
              <RefreshCw className={cn("h-4 w-4", (basicLoading || dbLoading || detailedLoading) && "animate-spin")} />
            </Button>
          </CardTitle>
          <CardDescription>
            Real-time monitoring of API and system health
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Error Display */}
          {(basicError || dbError || detailedError) && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded">
              <h4 className="font-medium text-destructive mb-2">Connection Issues</h4>
              {basicError && <p className="text-sm text-muted-foreground">Basic: {basicError.message}</p>}
              {dbError && <p className="text-sm text-muted-foreground">Database: {dbError.message}</p>}
              {detailedError && <p className="text-sm text-muted-foreground">Detailed: {detailedError.message}</p>}
            </div>
          )}

          {/* Detailed Health Data */}
          {detailedHealth && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium">System Details</h4>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2">
                      <FileJson className="h-4 w-4" />
                      View Raw JSON
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-96 max-h-96 overflow-auto">
                    <div className="space-y-2">
                      <h4 className="font-medium">Raw JSON Response</h4>
                      <div className="p-3 bg-muted rounded text-xs overflow-auto">
                        <pre>{JSON.stringify(detailedHealth, null, 2)}</pre>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>

              <div className="space-y-4">
                {/* Basic System Info */}
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="flex justify-between items-center p-3 bg-muted rounded">
                    <span className="text-sm font-medium">Status</span>
                    <Badge variant="secondary" className={getStatusColor(detailedHealth.status)}>
                      {detailedHealth.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-muted rounded">
                    <span className="text-sm font-medium">Service</span>
                    <span className="text-sm">{detailedHealth.service || 'LabCastARR'}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-muted rounded">
                    <span className="text-sm font-medium">Version</span>
                    <span className="text-sm">{detailedHealth.version || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-muted rounded">
                    <span className="text-sm font-medium">Timestamp</span>
                    <span className="text-sm">{formatTimestamp(detailedHealth.timestamp)}</span>
                  </div>
                </div>

                {/* Components Status */}
                {detailedHealth.components && (
                  <>
                    <Separator />
                    <div>
                      <h5 className="font-medium mb-3">Components Status</h5>
                      <div className="space-y-3">
                        {/* Database Component */}
                        {detailedHealth.components.database && (
                          <div className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">Database</span>
                              <Badge variant="secondary" className={getStatusColor(detailedHealth.components.database.status)}>
                                {detailedHealth.components.database.status}
                              </Badge>
                            </div>
                            {detailedHealth.components.database.type && (
                              <div className="text-sm text-muted-foreground">
                                Type: {detailedHealth.components.database.type}
                              </div>
                            )}
                            {detailedHealth.components.database.error && (
                              <div className="text-sm text-destructive mt-1">
                                Error: {detailedHealth.components.database.error}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Filesystem Component */}
                        {detailedHealth.components.filesystem && (
                          <div className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">Filesystem</span>
                              <Badge variant="secondary" className={getStatusColor(detailedHealth.components.filesystem.status)}>
                                {detailedHealth.components.filesystem.status}
                              </Badge>
                            </div>
                            <div className="grid gap-2 text-sm text-muted-foreground">
                              <div className="flex justify-between">
                                <span>Media Path:</span>
                                <span className="font-mono">{detailedHealth.components.filesystem.media_path}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Feeds Path:</span>
                                <span className="font-mono">{detailedHealth.components.filesystem.feeds_path}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Media Accessible:</span>
                                <Badge variant={detailedHealth.components.filesystem.media_accessible ? "default" : "destructive"} className="text-xs">
                                  {detailedHealth.components.filesystem.media_accessible ? "Yes" : "No"}
                                </Badge>
                              </div>
                              <div className="flex justify-between">
                                <span>Feeds Accessible:</span>
                                <Badge variant={detailedHealth.components.filesystem.feeds_accessible ? "default" : "destructive"} className="text-xs">
                                  {detailedHealth.components.filesystem.feeds_accessible ? "Yes" : "No"}
                                </Badge>
                              </div>
                            </div>
                            {detailedHealth.components.filesystem.error && (
                              <div className="text-sm text-destructive mt-2">
                                Error: {detailedHealth.components.filesystem.error}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}