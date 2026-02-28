/**
 * Date Range Picker Component
 * 
 * Provides a date range picker using ShadcnUI Calendar component
 * Allows users to select a start and end date for filtering notifications
 */
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, X } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (range: DateRange | undefined) => void
  className?: string
}

/**
 * Format date range for display
 */
function formatDateRange(range: DateRange | undefined): string {
  if (!range?.from) {
    return "All dates"
  }
  
  if (range.from && !range.to) {
    return `From ${format(range.from, "dd/MM/yyyy")}`
  }
  
  if (range.from && range.to) {
    return `${format(range.from, "dd/MM/yyyy")} - ${format(range.to, "dd/MM/yyyy")}`
  }
  
  return "All dates"
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)

  /**
   * Handle date range selection
   */
  const handleSelect = (range: DateRange | undefined) => {
    onDateRangeChange(range)
    // Close popover when both dates are selected
    if (range?.from && range?.to) {
      setOpen(false)
    }
  }

  /**
   * Clear date range
   */
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDateRangeChange(undefined)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "h-9 w-full justify-start text-left font-normal px-3",
            !dateRange?.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
          <span className="flex-1 truncate text-sm">{formatDateRange(dateRange)}</span>
          {dateRange?.from && (
            <button
              type="button"
              className="ml-2 h-4 w-4 shrink-0 opacity-50 hover:opacity-100 flex items-center justify-center transition-opacity"
              onClick={handleClear}
              aria-label="Clear date range"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-auto p-2" 
        align="start" 
        sideOffset={8}
      >
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={dateRange}
          onSelect={handleSelect}
          numberOfMonths={2}
          captionLayout="dropdown"
          className="rounded-lg"
        />
      </PopoverContent>
    </Popover>
  )
}

