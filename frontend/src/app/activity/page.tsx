/**
 * Activity Page
 *
 * Displays all system notifications in a table format with:
 * - Filters (type, channel, read status, executed by)
 * - Pagination
 * - Bulk actions (mark all as read, delete all)
 * - URL search params for bookmarkable filters
 * - Defaults to "Show all" filter
 */
"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Clock } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { parseISO, isValid } from "date-fns"
import { NotificationType } from "@/types"
import { MainLayout } from "@/components/layout/main-layout"
import { ActivityTable } from "@/components/features/activity/activity-table"
import { ActivityFilters } from "@/components/features/activity/activity-filters"
import { ActivityActions } from "@/components/features/activity/activity-actions"
import { useNotifications } from "@/hooks/use-notifications"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const ITEMS_PER_PAGE = 20

export default function ActivityPage() {
  const searchParams = useSearchParams()

  // Get filters from URL or use defaults
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedType, setSelectedType] = useState<
    NotificationType | undefined
  >((searchParams.get("type") as NotificationType) || undefined)
  const [selectedChannel, setSelectedChannel] = useState<number | undefined>(
    searchParams.get("channel")
      ? parseInt(searchParams.get("channel")!)
      : undefined
  )
  const [selectedReadStatus, setSelectedReadStatus] = useState<
    "unread" | "all"
  >((searchParams.get("status") as "unread" | "all") || "all")
  const [selectedExecutedBy, setSelectedExecutedBy] = useState<
    "user" | "system" | undefined
  >((searchParams.get("executedBy") as "user" | "system") || undefined)

  // Parse date range from URL params
  const parseDateRangeFromUrl = (): DateRange | undefined => {
    const fromParam = searchParams.get("dateFrom")
    const toParam = searchParams.get("dateTo")

    if (!fromParam) {
      return undefined
    }

    const from = parseISO(fromParam)
    const to = toParam ? parseISO(toParam) : undefined

    if (!isValid(from) || (to && !isValid(to))) {
      return undefined
    }

    return { from, to: to || undefined }
  }

  const [dateRange, setDateRange] = useState<DateRange | undefined>(
    parseDateRangeFromUrl()
  )

  // Fetch notifications with server-side pagination
  // Note: Date filtering is done client-side, so we fetch a larger batch when date filter is active
  const hasDateFilter = !!dateRange?.from
  const skip = hasDateFilter ? 0 : (currentPage - 1) * ITEMS_PER_PAGE
  // When date filtering, fetch max allowed (100) to have more data to filter
  // Otherwise use normal pagination
  const limit = hasDateFilter ? 100 : ITEMS_PER_PAGE

  const { data, isLoading } = useNotifications(
    skip,
    limit,
    selectedReadStatus === "unread"
  )

  const allNotifications = data?.notifications || []
  const serverTotal = data?.total || 0
  const unreadCount = data?.unread_count || 0

  /**
   * Update URL search params when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (selectedType) {
      params.set("type", selectedType)
    }
    if (selectedChannel) {
      params.set("channel", selectedChannel.toString())
    }
    if (selectedReadStatus !== "all") {
      params.set("status", selectedReadStatus)
    }
    if (selectedExecutedBy) {
      params.set("executedBy", selectedExecutedBy)
    }
    if (dateRange?.from) {
      params.set("dateFrom", dateRange.from.toISOString().split("T")[0])
      if (dateRange.to) {
        params.set("dateTo", dateRange.to.toISOString().split("T")[0])
      }
    }
    if (currentPage > 1) {
      params.set("page", currentPage.toString())
    }

    const queryString = params.toString()
    const newUrl = queryString ? `/activity?${queryString}` : "/activity"

    // Update URL without triggering a navigation
    window.history.replaceState({}, "", newUrl)
  }, [
    selectedType,
    selectedChannel,
    selectedReadStatus,
    selectedExecutedBy,
    dateRange,
    currentPage,
  ])

  /**
   * Filter notifications by type, channel, executed by, and date range (client-side)
   */
  const filteredNotifications = allNotifications.filter((notification) => {
    // Filter by type
    if (selectedType && notification.type !== selectedType) {
      return false
    }

    // Filter by channel
    if (selectedChannel) {
      const channelId = notification.dataJson?.followed_channel_id
      if (channelId !== selectedChannel) {
        return false
      }
    }

    // Filter by executed by
    if (selectedExecutedBy && notification.executedBy !== selectedExecutedBy) {
      return false
    }

    // Filter by date range
    if (dateRange?.from) {
      try {
        const notificationDate = parseISO(notification.createdAt)
        if (!isValid(notificationDate)) {
          return false
        }

        // Set time to start of day for comparison (using UTC to avoid timezone issues)
        const notificationDateStart = new Date(notificationDate)
        notificationDateStart.setUTCHours(0, 0, 0, 0)

        const fromDate = new Date(dateRange.from)
        fromDate.setUTCHours(0, 0, 0, 0)

        // Check if notification is on or after start date
        if (notificationDateStart.getTime() < fromDate.getTime()) {
          return false
        }

        // Check if notification is on or before end date (if provided)
        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setUTCHours(23, 59, 59, 999)

          if (notificationDateStart.getTime() > toDate.getTime()) {
            return false
          }
        }
      } catch (error) {
        // If date parsing fails, exclude the notification
        console.warn(
          "Error parsing notification date:",
          notification.createdAt,
          error
        )
        return false
      }
    }

    return true
  })

  // Calculate pagination based on filtered results
  const filteredTotal = filteredNotifications.length
  const totalPages = Math.max(1, Math.ceil(filteredTotal / ITEMS_PER_PAGE))

  // Get the current page of filtered notifications
  // When date filter is active, paginate the filtered results client-side
  // Otherwise, the server already paginated them
  const paginatedNotifications = hasDateFilter
    ? filteredNotifications.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
      )
    : filteredNotifications

  /**
   * Handle filter changes
   */
  const handleTypeChange = (type?: NotificationType) => {
    setSelectedType(type)
    setCurrentPage(1)
  }

  const handleChannelChange = (channelId?: number) => {
    setSelectedChannel(channelId)
    setCurrentPage(1)
  }

  const handleReadStatusChange = (status: "unread" | "all") => {
    setSelectedReadStatus(status)
    setCurrentPage(1)
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setCurrentPage(1)
  }

  const handleExecutedByChange = (executedBy?: "user" | "system") => {
    setSelectedExecutedBy(executedBy)
    setCurrentPage(1)
  }

  const handleClearFilters = () => {
    setSelectedType(undefined)
    setSelectedChannel(undefined)
    setSelectedReadStatus("all")
    setSelectedExecutedBy(undefined)
    setDateRange(undefined)
    setCurrentPage(1)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <Clock className="h-8 w-8" />
          <div>
            <h1 className="text-3xl font-bold">Activity</h1>
            <p className="text-muted-foreground">
              View and manage all system notifications
            </p>
          </div>
        </div>

        {/* Actions Bar */}
        <ActivityActions
          hasNotifications={allNotifications.length > 0}
          unreadCount={unreadCount}
        />

        {/* Filters */}
        <ActivityFilters
          selectedType={selectedType}
          selectedChannel={selectedChannel}
          selectedReadStatus={selectedReadStatus}
          selectedExecutedBy={selectedExecutedBy}
          dateRange={dateRange}
          onTypeChange={handleTypeChange}
          onChannelChange={handleChannelChange}
          onReadStatusChange={handleReadStatusChange}
          onExecutedByChange={handleExecutedByChange}
          onDateRangeChange={handleDateRangeChange}
          onClearFilters={handleClearFilters}
        />

        {/* Activity Table */}
        <ActivityTable
          notifications={paginatedNotifications}
          isLoading={isLoading}
        />

        {/* Pagination - only show if we have multiple pages and results */}
        {totalPages > 1 && filteredTotal > 0 && (
          <div className="flex justify-center">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.max(1, currentPage - 1))
                    }
                    className={
                      currentPage === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>

                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <PaginationItem key={pageNum}>
                      <PaginationLink
                        size="icon"
                        onClick={() => handlePageChange(pageNum)}
                        isActive={currentPage === pageNum}
                        className="cursor-pointer"
                      >
                        {pageNum}
                      </PaginationLink>
                    </PaginationItem>
                  )
                })}

                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    size="default"
                    onClick={() =>
                      handlePageChange(Math.min(totalPages, currentPage + 1))
                    }
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        )}

        {/* Results Summary */}
        {!isLoading && paginatedNotifications.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing{" "}
            {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredTotal)}-
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredTotal)} of{" "}
            {filteredTotal} notification{filteredTotal !== 1 ? "s" : ""}
            {hasDateFilter && filteredTotal !== serverTotal && (
              <span className="ml-1 text-xs opacity-75">
                (filtered from {serverTotal} total)
              </span>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}
