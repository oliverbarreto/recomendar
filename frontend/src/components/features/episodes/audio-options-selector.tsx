"use client"

import { useState } from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface AudioOptionsSelectorProps {
  showToggle?: boolean
  audioLanguage: string | null
  audioQuality: string | null
  onLanguageChange: (value: string | null) => void
  onQualityChange: (value: string | null) => void
}

export function AudioOptionsSelector({
  showToggle = true,
  audioLanguage,
  audioQuality,
  onLanguageChange,
  onQualityChange,
}: AudioOptionsSelectorProps) {
  const [enabled, setEnabled] = useState(
    !!(audioLanguage || audioQuality)
  )

  const handleToggle = (checked: boolean) => {
    setEnabled(checked)
    if (!checked) {
      onLanguageChange(null)
      onQualityChange(null)
    } else {
      // Default to "original" language and "low" quality when enabled
      onLanguageChange("default")
      onQualityChange("low")
    }
  }

  const isActive = showToggle ? enabled : !!(audioLanguage || audioQuality)

  return (
    <div className="space-y-3">
      {showToggle && (
        <div className="flex items-center space-x-2">
          <Checkbox
            id="custom-audio-options"
            checked={enabled}
            onCheckedChange={(checked) => handleToggle(checked === true)}
          />
          <Label
            htmlFor="custom-audio-options"
            className="text-sm font-medium cursor-pointer"
          >
            Custom audio options
          </Label>
        </div>
      )}

      {isActive && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Language</Label>
            <Select
              value={audioLanguage || "default"}
              onValueChange={(val) =>
                onLanguageChange(val === "default" ? null : val)
              }
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Original (default)</SelectItem>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Quality</Label>
            <Select
              value={audioQuality || "low"}
              onValueChange={(val) => onQualityChange(val)}
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Select quality" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low (up to 70 kbps)</SelectItem>
                <SelectItem value="medium">Medium (70-150 kbps)</SelectItem>
                <SelectItem value="high">High (150+ kbps)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}
    </div>
  )
}
