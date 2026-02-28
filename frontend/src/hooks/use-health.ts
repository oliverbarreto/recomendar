/**
 * React Query hooks for health API
 */
import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/lib/api'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useHealthDatabase() {
  return useQuery({
    queryKey: ['health', 'database'],
    queryFn: () => healthApi.checkDatabase(),
    refetchInterval: 30000,
  })
}

export function useHealthDetailed() {
  return useQuery({
    queryKey: ['health', 'detailed'],
    queryFn: () => healthApi.checkDetailed(),
    refetchInterval: 30000,
  })
}