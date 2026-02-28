/**
 * React Query hooks for Celery task status tracking and management
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { CeleryTaskStatus } from "@/types"

// Query keys factory
export const taskStatusKeys = {
  all: ["task-status"] as const,
  task: (taskId: string) => [...taskStatusKeys.all, "task", taskId] as const,
  channel: (channelId: number) =>
    [...taskStatusKeys.all, "channel", channelId] as const,
  summary: () => [...taskStatusKeys.all, "summary"] as const,
}

/**
 * Hook to poll task status by task ID
 * Automatically stops polling when task completes
 */
export function useTaskStatus(
  taskId: string | null | undefined,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: taskStatusKeys.task(taskId || ""),
    queryFn: async () => {
      if (!taskId) return null
      return await apiClient.getTaskStatus(taskId)
    },
    enabled: enabled && !!taskId,
    refetchInterval: (data) => {
      // Stop polling if task is completed or failed
      if (!data) return false
      if (data.status === "SUCCESS" || data.status === "FAILURE") {
        return false
      }
      // Poll every 2 seconds while task is running
      return 2000
    },
    staleTime: 0, // Always refetch
  })
}

/**
 * Hook to get the latest task status for a followed channel
 * Automatically polls while task is running
 * Returns null if no task status exists yet (404 is handled gracefully)
 */
export function useChannelTaskStatus(
  channelId: number | null | undefined,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: taskStatusKeys.channel(channelId || 0),
    queryFn: async () => {
      if (!channelId) return null
      return await apiClient.getChannelTaskStatus(channelId)
    },
    enabled: enabled && !!channelId,
    refetchInterval: (data) => {
      // FIX: Poll every 500ms (reduced from 2000ms) to catch fast tasks (< 1s)
      // This ensures UI shows "searching" state even for ultra-fast RSS tasks
      if (
        data?.status === "PENDING" ||
        data?.status === "STARTED" ||
        data?.status === "PROGRESS"
      ) {
        return 500 // Reduced from 2000ms to 500ms
      }
      // Poll every 30 seconds otherwise to catch new tasks
      return 30000
    },
    staleTime: 500, // Reduced from 1000ms to match polling interval
  })
}

/**
 * Hook to get summary of all tasks grouped by status
 */
export function useTasksSummary(enabled: boolean = true) {
  return useQuery({
    queryKey: taskStatusKeys.summary(),
    queryFn: () => apiClient.getTasksSummary(),
    enabled,
    refetchInterval: 5000, // Refresh every 5 seconds
    staleTime: 2000,
  })
}

/**
 * Hook to revoke a specific task
 */
export function useRevokeTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (taskId: string) => apiClient.revokeTask(taskId),
    onSuccess: () => {
      // Invalidate all task-related queries
      queryClient.invalidateQueries({ queryKey: taskStatusKeys.all })
    },
  })
}

/**
 * Hook to purge tasks by status
 */
export function usePurgeTasks() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      status,
      olderThanMinutes,
    }: {
      status: string
      olderThanMinutes?: number
    }) => apiClient.purgeTasks(status, olderThanMinutes),
    onSuccess: () => {
      // Invalidate all task-related queries
      queryClient.invalidateQueries({ queryKey: taskStatusKeys.all })
    },
  })
}
