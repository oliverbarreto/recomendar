/**
 * Comprehensive settings interface with tabbed navigation
 */
"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Radio,
  Podcast,
  Copy,
  RefreshCw,
  ExternalLink,
  Upload,
  Trash2,
  Plus,
  Tag as TagIcon,
  Save,
  CheckCircle2,
  Activity,
  ExternalLinkIcon,
  Settings,
  AlertTriangle,
  Loader2,
  Database,
  FileX,
  AlertCircle,
  Bell,
  ListTodo,
  X,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { HealthCheck } from "@/components/features/health-check"
import {
  channelApi,
  feedApi,
  tagApi,
  episodeApi,
  ApiError,
  userApi,
} from "@/lib/api"
import { useAuth } from "@/contexts/auth-context"
import type { Tag, Channel } from "@/types"
import { apiClient } from "@/lib/api-client"
import { SubscriptionCheckFrequency } from "@/types"
import { useTasksSummary, usePurgeTasks } from "@/hooks/use-task-status"

// Mock data
const mockChannelData = {
  name: "My Home Lab Podcast",
  description:
    "A podcast covering home lab setups, self-hosting, and technology tutorials for enthusiasts and professionals.",
  website: "https://homelab.example.com",
  image: "/api/placeholder/400/400",
  category: "Technology",
  language: "en",
  explicit: false,
  author: {
    name: "John Doe",
    email: "john@example.com",
  },
  owner: {
    name: "John Doe",
    email: "john@example.com",
  },
  feedUrl: "https://labcastarr.local/feeds/1/feed.xml",
}

const mockTags = [
  { id: 1, name: "docker", color: "#2563eb", count: 5 },
  { id: 2, name: "homelab", color: "#059669", count: 8 },
  { id: 3, name: "tutorial", color: "#dc2626", count: 12 },
  { id: 4, name: "kubernetes", color: "#7c3aed", count: 3 },
  { id: 5, name: "networking", color: "#ea580c", count: 6 },
]

interface TagRowProps {
  tag: Tag
  isEditing: boolean
  onEdit: (id: number) => void
  onUpdate: (id: number, name: string, color: string) => void
  onCancelEdit: () => void
  onDelete: (id: number, name: string) => void
  onNavigateToChannel: (tagId: number) => void
}

function TagRow({
  tag,
  isEditing,
  onEdit,
  onUpdate,
  onCancelEdit,
  onDelete,
  onNavigateToChannel,
}: TagRowProps) {
  const [editName, setEditName] = useState(tag.name)
  const [editColor, setEditColor] = useState(tag.color)
  const [isUpdating, setIsUpdating] = useState(false)

  const handleSave = async () => {
    if (!editName.trim()) {
      toast.error("Tag name cannot be empty")
      return
    }

    setIsUpdating(true)
    try {
      await onUpdate(tag.id, editName.trim(), editColor)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleCancel = () => {
    setEditName(tag.name)
    setEditColor(tag.color)
    onCancelEdit()
  }

  if (isEditing) {
    return (
      <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
        <div className="flex items-center gap-3 flex-1">
          <Input
            type="color"
            value={editColor}
            onChange={(e) => setEditColor(e.target.value)}
            className="w-12 h-8"
          />
          <Input
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            className="flex-1 max-w-48"
            placeholder="Tag name"
          />
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={isUpdating || !editName.trim()}
          >
            {isUpdating ? "Saving..." : "Save"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleCancel}>
            Cancel
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-3 border rounded-lg hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
      <div className="flex items-center gap-3">
        <div
          className="w-4 h-4 rounded-full"
          style={{ backgroundColor: tag.color }}
        />
        <Badge
          variant="outline"
          style={{ borderColor: tag.color, color: tag.color }}
        >
          {tag.name}
        </Badge>
        <span className="text-sm text-muted-foreground">
          {tag.usage_count || 0} episodes
        </span>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onNavigateToChannel(tag.id)}
          className="gap-2"
          title={`View episodes tagged with "${tag.name}"`}
        >
          <ExternalLinkIcon className="w-4 h-4" />
        </Button>
        <Button variant="outline" size="sm" onClick={() => onEdit(tag.id)}>
          Edit
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDelete(tag.id, tag.name)}
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}

export function SettingsInterface() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState("account")
  const [isGeneratingFeed, setIsGeneratingFeed] = useState(false)
  const [channelData, setChannelData] = useState(mockChannelData)
  const [newTagName, setNewTagName] = useState("")
  const [newTagColor, setNewTagColor] = useState("#2563eb")
  const [isLoading, setIsLoading] = useState(true)
  const [realChannelData, setRealChannelData] = useState<Channel | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isUploadingImage, setIsUploadingImage] = useState(false)

  // Account management states
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [profileData, setProfileData] = useState({
    name: user?.name || "",
    email: user?.email || "",
  })
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })
  const [channelImageUrl, setChannelImageUrl] = useState<string | null>(null)
  const [tags, setTags] = useState<Tag[]>([])
  const [isLoadingTags, setIsLoadingTags] = useState(false)
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [editingTagId, setEditingTagId] = useState<number | null>(null)

  // Delete library state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleteStep, setDeleteStep] = useState<
    "confirm" | "type-delete" | "deleting" | "result"
  >("confirm")
  const [deleteConfirmText, setDeleteConfirmText] = useState("")
  const [episodeCount, setEpisodeCount] = useState<number | null>(null)
  const [isLoadingCount, setIsLoadingCount] = useState(false)
  const [isDeletingLibrary, setIsDeletingLibrary] = useState(false)
  const [deleteResult, setDeleteResult] = useState<{
    success: boolean
    message: string
    details?: Record<string, unknown>
    error?: string
  } | null>(null)

  // Task management state
  const [showPurgeDialog, setShowPurgeDialog] = useState(false)
  const [purgeStatus, setPurgeStatus] = useState<
    "PENDING" | "FAILURE" | "SUCCESS"
  >("PENDING")

  // Hooks for task management
  const { data: tasksSummary, isLoading: isLoadingTasks } = useTasksSummary(
    activeTab === "advanced"
  )
  const purgeTasks = usePurgeTasks()

  // Load channel data on component mount
  useEffect(() => {
    loadChannelData()
  }, [])

  // Load tags when channel data is available
  useEffect(() => {
    if (realChannelData?.id) {
      loadTags()
    }
  }, [realChannelData?.id])

  const loadTags = async () => {
    if (!realChannelData?.id) return

    setIsLoadingTags(true)
    try {
      const response = await tagApi.getAll(realChannelData.id)
      setTags(response.tags)
    } catch (error) {
      console.error("Failed to load tags:", error)
      toast.error("Failed to load tags")
    } finally {
      setIsLoadingTags(false)
    }
  }

  const loadChannelData = async () => {
    try {
      setIsLoading(true)

      // Get channel data (assuming first channel for now)
      const channels = await channelApi.getAll({ limit: 1 })
      if (channels.length === 0) {
        setRealChannelData(null)
        return
      }

      const channel = channels[0]
      // IMPORTANT NOTE: This was failing because the feed_url value in the database was an empty string. Defaulting to localhost url instead of the correct production url. However, the second part of the expresion should have been correct.
      // const feedUrl = channel.feed_url || `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/feeds/${channel.id}/feed.xml`
      const feedUrl =
        channel.feed_url ||
        `${process.env.BACKEND_URL || "http://localhost:8000"}/v1/feeds/${
          channel.id
        }/feed.xml`

      setRealChannelData({
        id: channel.id,
        name: channel.name,
        description: channel.description,
        feedUrl,
        lastUpdated: new Date(channel.updated_at).toLocaleDateString(),
        status: "active",
      })

      // Update channel data state for the form
      setChannelData({
        ...channelData,
        name: channel.name,
        description: channel.description || "",
        website: channel.website_url || "",
        category: channel.category || "Technology",
        language: channel.language || "en",
        explicit: channel.explicit_content || false,
        author: {
          name: channel.author_name || "",
          email: channel.author_email || "",
        },
        owner: {
          name: channel.owner_name || "",
          email: channel.owner_email || "",
        },
        feedUrl,
      })

      // Load channel image if available
      if (channel.image_url) {
        const imageUrl = `${channelApi.getImageUrl(channel.id)}?t=${Date.now()}`
        setChannelImageUrl(imageUrl)
      } else {
        setChannelImageUrl(null)
      }
    } catch (error) {
      console.error("Failed to load channel data:", error)
      toast.error("Failed to load channel data")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveChannel = async () => {
    if (!realChannelData) {
      toast.error("No channel data to save")
      return
    }

    setIsSaving(true)
    try {
      const updateData = {
        name: channelData.name,
        description: channelData.description,
        website_url: channelData.website || undefined,
        category: channelData.category,
        language: channelData.language,
        explicit_content: channelData.explicit,
        author_name: channelData.author.name,
        author_email: channelData.author.email,
        owner_name: channelData.owner.name,
        owner_email: channelData.owner.email,
      }

      await channelApi.update(realChannelData.id, updateData)
      toast.success("Channel settings saved successfully")

      // Reload channel data to get updated values
      await loadChannelData()
    } catch (error) {
      console.error("Failed to save channel:", error)
      toast.error("Failed to save channel settings")
    } finally {
      setIsSaving(false)
    }
  }

  const handleImageUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0]
    if (!file || !realChannelData) return

    // Validate file type
    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if (!allowedTypes.includes(file.type)) {
      toast.error("Please select a valid image file (JPEG, PNG, or WebP)")
      return
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image file must be less than 5MB")
      return
    }

    setIsUploadingImage(true)
    try {
      await channelApi.uploadImage(realChannelData.id, file)
      toast.success("Channel image uploaded successfully")

      // Update the image URL to trigger re-render
      const newImageUrl = `${channelApi.getImageUrl(
        realChannelData.id
      )}?t=${Date.now()}`
      setChannelImageUrl(newImageUrl)

      // Reload channel data
      await loadChannelData()
    } catch (error) {
      console.error("Failed to upload image:", error)
      toast.error("Failed to upload channel image")
    } finally {
      setIsUploadingImage(false)
      // Clear the input
      if (event.target) {
        event.target.value = ""
      }
    }
  }

  const handleCopyFeedUrl = async () => {
    try {
      await navigator.clipboard.writeText(channelData.feedUrl)
      toast.success("Feed URL copied to clipboard")
    } catch {
      toast.error("Failed to copy feed URL")
    }
  }

  const handleRegenerateFeed = async () => {
    if (!realChannelData) return
    setIsGeneratingFeed(true)
    try {
      await feedApi.validateFeed(realChannelData.id)
      toast.success("RSS Feed regenerated successfully")
    } catch (error) {
      toast.error("Failed to regenerate RSS Feed")
    } finally {
      setIsGeneratingFeed(false)
    }
  }

  const handleAddTag = async () => {
    if (!newTagName.trim() || !realChannelData?.id) {
      toast.error("Please enter a tag name")
      return
    }

    // Check if tag name already exists
    if (
      tags.some(
        (tag) => tag.name.toLowerCase() === newTagName.trim().toLowerCase()
      )
    ) {
      toast.error("A tag with this name already exists")
      return
    }

    setIsAddingTag(true)
    try {
      const newTag = await tagApi.create(realChannelData.id, {
        name: newTagName.trim(),
        color: newTagColor,
      })

      setTags((prev) => [...prev, newTag])
      setNewTagName("")
      setNewTagColor("#2563eb") // Reset to default color
      toast.success(`Tag "${newTag.name}" created successfully`)
    } catch (error) {
      console.error("Failed to create tag:", error)
      toast.error("Failed to create tag")
    } finally {
      setIsAddingTag(false)
    }
  }

  const handleDeleteTag = async (tagId: number, tagName: string) => {
    if (
      !confirm(
        `Are you sure you want to delete the tag "${tagName}"? This action cannot be undone.`
      )
    ) {
      return
    }

    try {
      await tagApi.delete(tagId)
      setTags((prev) => prev.filter((tag) => tag.id !== tagId))
      toast.success(`Tag "${tagName}" deleted successfully`)
    } catch (error) {
      console.error("Failed to delete tag:", error)
      toast.error("Failed to delete tag")
    }
  }

  const handleUpdateTag = async (
    tagId: number,
    name: string,
    color: string
  ) => {
    try {
      const updatedTag = await tagApi.update(tagId, { name, color })
      setTags((prev) =>
        prev.map((tag) => (tag.id === tagId ? updatedTag : tag))
      )
      setEditingTagId(null)
      toast.success(`Tag "${updatedTag.name}" updated successfully`)
    } catch (error) {
      console.error("Failed to update tag:", error)
      toast.error("Failed to update tag")
    }
  }

  const handleNavigateToChannel = (tagId: number) => {
    router.push(`/channel?tags=${tagId}`)
  }

  // Delete library functions
  const loadEpisodeCount = async () => {
    if (!realChannelData?.id) return

    setIsLoadingCount(true)
    try {
      const result = await episodeApi.getCount(realChannelData.id)
      setEpisodeCount(result.episode_count)
    } catch (error) {
      console.error("Failed to load episode count:", error)
      toast.error("Failed to load episode count")
      setEpisodeCount(null)
    } finally {
      setIsLoadingCount(false)
    }
  }

  const handleDeleteLibraryClick = () => {
    setDeleteStep("confirm")
    setDeleteConfirmText("")
    setDeleteResult(null)
    setShowDeleteDialog(true)
    loadEpisodeCount()
  }

  const handleDeleteConfirm = () => {
    setDeleteStep("type-delete")
  }

  const handleDeleteCancel = () => {
    setShowDeleteDialog(false)
    setDeleteStep("confirm")
    setDeleteConfirmText("")
    setDeleteResult(null)
  }

  const handleDeleteExecute = async () => {
    if (deleteConfirmText !== "DELETE" || !realChannelData?.id) {
      return
    }

    setDeleteStep("deleting")
    setIsDeletingLibrary(true)

    try {
      const result = await episodeApi.bulkDeleteAll(realChannelData.id, {
        dryRun: false,
        timeout: 600000, // 10 minutes for large libraries
        maxRetries: 3,
      })

      setDeleteResult({
        success: result.success,
        message: result.message,
        details: {
          total_episodes: result.total_episodes,
          deleted_episodes: result.deleted_episodes,
          failed_episodes: result.failed_episodes,
          deleted_files: result.deleted_files,
          failed_files: result.failed_files,
          partial_completion: result.partial_completion,
          failed_episode_details: result.failed_episode_details,
        },
      })

      if (result.success) {
        if (result.partial_completion) {
          toast.warning(
            `Library partially deleted: ${result.deleted_episodes}/${result.total_episodes} episodes deleted`
          )
        } else {
          toast.success(
            `Successfully deleted ${result.deleted_episodes} episodes and ${result.deleted_files} media files`
          )
        }
      } else {
        toast.error(`Delete failed: ${result.error_message || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Delete library error:", error)

      let errorMessage = "Failed to delete library"
      let errorDetails = null

      if (error instanceof ApiError) {
        errorMessage = error.message
        errorDetails = error.response
      } else if (error instanceof Error) {
        errorMessage = error.message
      }

      setDeleteResult({
        success: false,
        message: errorMessage,
        error: errorMessage,
        details: errorDetails,
      })

      toast.error(errorMessage)
    } finally {
      setIsDeletingLibrary(false)
      setDeleteStep("result")
    }
  }

  const resetDeleteDialog = () => {
    setShowDeleteDialog(false)
    setDeleteStep("confirm")
    setDeleteConfirmText("")
    setDeleteResult(null)
    setEpisodeCount(null)

    // Reload page data to reflect changes
    if (deleteResult?.success) {
      window.location.reload()
    }
  }

  // Task management handlers
  const handlePurgeTasksClick = (status: "PENDING" | "FAILURE" | "SUCCESS") => {
    setPurgeStatus(status)
    setShowPurgeDialog(true)
  }

  const handlePurgeTasksExecute = async () => {
    try {
      const result = await purgeTasks.mutateAsync({
        status: purgeStatus,
        olderThanMinutes: undefined, // Purge all tasks with this status
      })

      toast.success(
        `Purged ${result.deleted} ${purgeStatus} tasks` +
          (result.revoked > 0 ? ` (${result.revoked} revoked from queue)` : "")
      )
      setShowPurgeDialog(false)
    } catch (error) {
      console.error("Purge tasks error:", error)
      toast.error(
        `Failed to purge tasks: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      )
    }
  }

  const handlePurgeTasksCancel = () => {
    setShowPurgeDialog(false)
  }

  // Update profile data when user changes
  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name || "",
        email: user.email || "",
      })
    }
  }, [user])

  // Account management functions
  const handleProfileUpdate = async () => {
    if (!profileData.name.trim() || !profileData.email.trim()) {
      toast.error("Please fill in all fields")
      return
    }

    if (!profileData.email.includes("@")) {
      toast.error("Please enter a valid email address")
      return
    }

    setIsUpdatingProfile(true)
    try {
      await userApi.updateProfile({
        name: profileData.name.trim(),
        email: profileData.email.trim(),
      })
      toast.success("Profile updated successfully")
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update profile"
      )
    } finally {
      setIsUpdatingProfile(false)
    }
  }

  const handlePasswordChange = async () => {
    if (
      !passwordData.currentPassword ||
      !passwordData.newPassword ||
      !passwordData.confirmPassword
    ) {
      toast.error("Please fill in all password fields")
      return
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error("New passwords do not match")
      return
    }

    if (passwordData.newPassword.length < 8) {
      toast.error("New password must be at least 8 characters long")
      return
    }

    setIsChangingPassword(true)
    try {
      await userApi.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword,
      })
      toast.success("Password changed successfully")
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      })
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to change password"
      )
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      toast.success("Logged out successfully")
      router.push("/login")
    } catch (error) {
      toast.error("Error logging out")
    }
  }

  const renderAccountTab = () => (
    <div className="space-y-6">
      {/* User Profile Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            User Profile
          </CardTitle>
          <CardDescription>
            Manage your account information and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="profile-name">Full Name</Label>
              <Input
                id="profile-name"
                value={profileData.name}
                onChange={(e) =>
                  setProfileData({ ...profileData, name: e.target.value })
                }
                placeholder="Enter your full name"
                disabled={isUpdatingProfile}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="profile-email">Email Address</Label>
              <Input
                id="profile-email"
                type="email"
                value={profileData.email}
                onChange={(e) =>
                  setProfileData({ ...profileData, email: e.target.value })
                }
                placeholder="Enter your email address"
                disabled={isUpdatingProfile}
              />
            </div>
          </div>
          <div className="flex justify-between items-center pt-4">
            <div className="text-sm text-muted-foreground">
              <p>Account Type: {user?.isAdmin ? "Administrator" : "User"}</p>
              <p>
                Member since:{" "}
                {user?.createdAt
                  ? new Date(user.createdAt).toLocaleDateString()
                  : "Unknown"}
              </p>
            </div>
            <Button
              onClick={handleProfileUpdate}
              disabled={isUpdatingProfile}
              className="gap-2"
            >
              {isUpdatingProfile ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isUpdatingProfile ? "Updating..." : "Update Profile"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>
            Update your password to keep your account secure
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Current Password</Label>
            <Input
              id="current-password"
              type="password"
              value={passwordData.currentPassword}
              onChange={(e) =>
                setPasswordData({
                  ...passwordData,
                  currentPassword: e.target.value,
                })
              }
              placeholder="Enter your current password"
              disabled={isChangingPassword}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={passwordData.newPassword}
                onChange={(e) =>
                  setPasswordData({
                    ...passwordData,
                    newPassword: e.target.value,
                  })
                }
                placeholder="Enter new password"
                disabled={isChangingPassword}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={passwordData.confirmPassword}
                onChange={(e) =>
                  setPasswordData({
                    ...passwordData,
                    confirmPassword: e.target.value,
                  })
                }
                placeholder="Confirm new password"
                disabled={isChangingPassword}
              />
            </div>
          </div>
          <div className="flex justify-end pt-4">
            <Button
              onClick={handlePasswordChange}
              disabled={isChangingPassword}
              variant="outline"
              className="gap-2"
            >
              {isChangingPassword ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Settings className="w-4 h-4" />
              )}
              {isChangingPassword ? "Changing..." : "Change Password"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Session Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Session Management
          </CardTitle>
          <CardDescription>
            Manage your login session and security
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Sign out of your account</p>
              <p className="text-sm text-muted-foreground">
                This will log you out and redirect to the login page
              </p>
            </div>
            <Button
              onClick={handleLogout}
              variant="destructive"
              className="gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderChannelTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radio className="w-5 h-5" />
            Channel Information
          </CardTitle>
          <CardDescription>
            Configure your podcast channel details and metadata
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="channel-name">Channel Name</Label>
              <Input
                id="channel-name"
                value={channelData.name}
                onChange={(e) =>
                  setChannelData({ ...channelData, name: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select value={channelData.category}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Technology">Technology</SelectItem>
                  <SelectItem value="Education">Education</SelectItem>
                  <SelectItem value="Business">Business</SelectItem>
                  <SelectItem value="Science">Science</SelectItem>
                  <SelectItem value="News">News</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              rows={4}
              value={channelData.description}
              onChange={(e) =>
                setChannelData({ ...channelData, description: e.target.value })
              }
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="website">Website URL *</Label>
              <Input
                id="website"
                type="url"
                required
                value={channelData.website}
                onChange={(e) =>
                  setChannelData({ ...channelData, website: e.target.value })
                }
                placeholder="https://your-podcast-website.com"
              />
              <p className="text-sm text-muted-foreground">
                Required for iTunes compliance
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Select value={channelData.language}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="explicit">Content Rating</Label>
              <Select
                value={channelData.explicit ? "yes" : "no"}
                onValueChange={(value) =>
                  setChannelData({
                    ...channelData,
                    explicit: value === "yes",
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Explicit Content</SelectItem>
                  <SelectItem value="no">Clean Content</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Mark if podcast contains explicit language or content
              </p>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <h4 className="font-semibold">Author Information</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="author-name">Author Name</Label>
                <Input
                  id="author-name"
                  value={channelData.author.name}
                  onChange={(e) =>
                    setChannelData({
                      ...channelData,
                      author: { ...channelData.author, name: e.target.value },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="author-email">Author Email</Label>
                <Input
                  id="author-email"
                  type="email"
                  value={channelData.author.email}
                  onChange={(e) =>
                    setChannelData({
                      ...channelData,
                      author: { ...channelData.author, email: e.target.value },
                    })
                  }
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Channel Artwork</h4>
            <div className="flex items-center gap-4">
              <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center overflow-hidden border">
                {channelImageUrl ? (
                  <img
                    src={channelImageUrl}
                    alt="Channel artwork"
                    className="w-full h-full object-cover rounded-lg"
                    onError={(e) => {
                      console.error(
                        "Failed to load channel image:",
                        channelImageUrl
                      )
                      setChannelImageUrl(null)
                    }}
                    onLoad={() => {
                      console.log(
                        "Channel image loaded successfully:",
                        channelImageUrl
                      )
                    }}
                  />
                ) : (
                  <Radio className="w-8 h-8 text-muted-foreground" />
                )}
              </div>
              <div className="space-y-2">
                <div className="relative">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    disabled={isUploadingImage}
                  />
                  <Button
                    variant="outline"
                    className="gap-2"
                    disabled={isUploadingImage}
                  >
                    <Upload
                      className={cn(
                        "w-4 h-4",
                        isUploadingImage && "animate-spin"
                      )}
                    />
                    {isUploadingImage ? "Uploading..." : "Upload New Image"}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  Recommended: 1400x1400px, square format, max 5MB
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={handleSaveChannel}
          className="gap-2"
          disabled={isSaving}
        >
          <Save className={cn("w-4 h-4", isSaving && "animate-spin")} />
          {isSaving ? "Saving..." : "Save Channel Settings"}
        </Button>
      </div>
    </div>
  )

  const renderRSSTab = () => {
    if (isLoading) {
      return (
        <div className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-muted rounded w-1/4" />
                <div className="h-10 bg-muted rounded" />
                <div className="h-16 bg-muted rounded" />
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    if (!realChannelData) {
      return (
        <div className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="text-center py-8">
                <Podcast className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Channel Found</h3>
                <p className="text-muted-foreground">
                  Create a channel first to configure RSS feed settings.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Podcast className="h-5 w-5" />
              RSS Feed
            </CardTitle>
            <CardDescription>
              Use this URL in your podcast app to subscribe to your channel
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex-1 p-3 bg-muted rounded-md font-mono text-sm overflow-hidden">
                <div className="truncate">{realChannelData.feedUrl}</div>
              </div>
              <Button variant="outline" size="sm" onClick={handleCopyFeedUrl}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a
                  href={realChannelData.feedUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Badge
                  variant="outline"
                  className={
                    realChannelData.status === "active"
                      ? "text-green-600 border-green-600"
                      : "text-red-600 border-red-600"
                  }
                >
                  {realChannelData.status === "active" ? "Active" : "Inactive"}
                </Badge>
                <span>Last updated: {realChannelData.lastUpdated}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRegenerateFeed}
                disabled={isGeneratingFeed}
                className="gap-2"
              >
                <RefreshCw
                  className={cn("h-4 w-4", isGeneratingFeed && "animate-spin")}
                />
                Regenerate
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Feed Validation</CardTitle>
            <CardDescription>
              Your RSS feed compatibility status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium text-green-800 dark:text-green-200">
                    iTunes Compatible
                  </div>
                  <div className="text-sm text-green-600 dark:text-green-400">
                    Valid RSS 2.0 format
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium text-green-800 dark:text-green-200">
                    Spotify Ready
                  </div>
                  <div className="text-sm text-green-600 dark:text-green-400">
                    All requirements met
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderTagsTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TagIcon className="w-5 h-5" />
            Tag Management
          </CardTitle>
          <CardDescription>
            Create and manage tags for organizing your episodes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <h4 className="font-semibold">Add New Tag</h4>
            <div className="flex gap-2">
              <Input
                placeholder="Tag name"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className="flex-1"
              />
              <Input
                type="color"
                value={newTagColor}
                onChange={(e) => setNewTagColor(e.target.value)}
                className="w-16"
              />
              <Button
                onClick={handleAddTag}
                className="gap-2"
                disabled={isAddingTag}
              >
                <Plus
                  className={cn("w-4 h-4", isAddingTag && "animate-spin")}
                />
                {isAddingTag ? "Adding..." : "Add Tag"}
              </Button>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <h4 className="font-semibold">Existing Tags</h4>
            {isLoadingTags ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded-full bg-muted" />
                        <div className="h-6 w-16 bg-muted rounded" />
                        <div className="h-4 w-20 bg-muted rounded" />
                      </div>
                      <div className="flex gap-2">
                        <div className="h-8 w-12 bg-muted rounded" />
                        <div className="h-8 w-8 bg-muted rounded" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : tags.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <TagIcon className="w-12 h-12 mx-auto mb-2" />
                <p>No tags yet. Create your first tag above!</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {tags.map((tag) => (
                  <TagRow
                    key={tag.id}
                    tag={tag}
                    isEditing={editingTagId === tag.id}
                    onEdit={(id) => setEditingTagId(id)}
                    onUpdate={handleUpdateTag}
                    onCancelEdit={() => setEditingTagId(null)}
                    onDelete={handleDeleteTag}
                    onNavigateToChannel={handleNavigateToChannel}
                  />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  // Subscription settings state
  const [subscriptionFrequency, setSubscriptionFrequency] =
    useState<SubscriptionCheckFrequency>(SubscriptionCheckFrequency.DAILY)
  const [preferredCheckHour, setPreferredCheckHour] = useState<number>(2)
  const [preferredCheckMinute, setPreferredCheckMinute] = useState<number>(0)
  const [timezone, setTimezone] = useState<string>("Europe/Madrid")
  const [availableTimezones, setAvailableTimezones] = useState<string[]>([])
  const [isLoadingSettings, setIsLoadingSettings] = useState(true)
  const [isSavingSettings, setIsSavingSettings] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Store original values to detect changes
  const [originalFrequency, setOriginalFrequency] =
    useState<SubscriptionCheckFrequency>(SubscriptionCheckFrequency.DAILY)
  const [originalHour, setOriginalHour] = useState<number>(2)
  const [originalMinute, setOriginalMinute] = useState<number>(0)
  const [originalTimezone, setOriginalTimezone] = useState<string>("Europe/Madrid")

  const loadUserSettings = async () => {
    try {
      setIsLoadingSettings(true)
      const [settings, timezones] = await Promise.all([
        apiClient.getUserSettings(),
        apiClient.getAvailableTimezones()
      ])

      if (settings?.subscription_check_frequency) {
        setSubscriptionFrequency(
          settings.subscription_check_frequency as SubscriptionCheckFrequency
        )
        setOriginalFrequency(
          settings.subscription_check_frequency as SubscriptionCheckFrequency
        )
      }
      if (settings?.preferred_check_hour !== undefined) {
        setPreferredCheckHour(settings.preferred_check_hour)
        setOriginalHour(settings.preferred_check_hour)
      }
      if (settings?.preferred_check_minute !== undefined) {
        setPreferredCheckMinute(settings.preferred_check_minute)
        setOriginalMinute(settings.preferred_check_minute)
      }
      if (settings?.timezone) {
        setTimezone(settings.timezone)
        setOriginalTimezone(settings.timezone)
      }
      if (timezones) {
        setAvailableTimezones(timezones)
      }
      setHasUnsavedChanges(false)
    } catch (error) {
      console.error("Failed to load user settings:", error)
      toast.error("Failed to load settings")
    } finally {
      setIsLoadingSettings(false)
    }
  }

  useEffect(() => {
    if (activeTab === "subscriptions") {
      loadUserSettings()
    }
  }, [activeTab])

  // Check if there are unsaved changes
  useEffect(() => {
    const changed =
      subscriptionFrequency !== originalFrequency ||
      preferredCheckHour !== originalHour ||
      preferredCheckMinute !== originalMinute ||
      timezone !== originalTimezone
    setHasUnsavedChanges(changed)
  }, [
    subscriptionFrequency,
    preferredCheckHour,
    preferredCheckMinute,
    timezone,
    originalFrequency,
    originalHour,
    originalMinute,
    originalTimezone,
  ])

  const handleSaveSettings = async () => {
    try {
      setIsSavingSettings(true)
      const updateData = {
        subscription_check_frequency: subscriptionFrequency,
        preferred_check_hour: preferredCheckHour,
        preferred_check_minute: preferredCheckMinute,
        timezone: timezone,
      }
      console.log("Saving settings:", updateData)
      const result = await apiClient.updateUserSettings(updateData)
      console.log("Settings saved successfully:", result)
      // Update original values
      setOriginalFrequency(subscriptionFrequency)
      setOriginalHour(preferredCheckHour)
      setOriginalMinute(preferredCheckMinute)
      setOriginalTimezone(timezone)
      setHasUnsavedChanges(false)
      toast.success("Settings saved successfully")
    } catch (error) {
      console.error("Failed to save settings - Full error:", error)
      toast.error(
        `Failed to save settings: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      )
    } finally {
      setIsSavingSettings(false)
    }
  }

  const handleDiscardChanges = () => {
    setSubscriptionFrequency(originalFrequency)
    setPreferredCheckHour(originalHour)
    setPreferredCheckMinute(originalMinute)
    setTimezone(originalTimezone)
    setHasUnsavedChanges(false)
  }

  const renderSubscriptionsTab = () => {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Subscription Settings
            </CardTitle>
            <CardDescription>
              Configure how often the system checks for new videos from followed
              channels
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoadingSettings ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <Label className="mb-3" htmlFor="frequency">
                    Check Frequency
                  </Label>
                  <Select
                    value={subscriptionFrequency}
                    onValueChange={(value) =>
                      setSubscriptionFrequency(
                        value as SubscriptionCheckFrequency
                      )
                    }
                    disabled={isSavingSettings}
                  >
                    <SelectTrigger id="frequency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={SubscriptionCheckFrequency.DAILY}>
                        Daily
                      </SelectItem>
                      <SelectItem value={SubscriptionCheckFrequency.WEEKLY}>
                        Weekly
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground mt-2">
                    This setting controls how often the system checks all your
                    followed channels for new videos. Daily checks run every
                    day, and weekly runs once per week.
                  </p>
                </div>

                <Separator />
                {/* 🤖 Place hour and minute Pickers side by side in a single row */}
                <div>
                  <Label className="mb-3 block">
                    Preferred Check Time
                  </Label>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <Label
                        htmlFor="check-hour"
                        className="text-sm text-muted-foreground mr-1"
                      >
                        Hour
                      </Label>
                      <Select
                        value={preferredCheckHour.toString()}
                        onValueChange={(value) =>
                          setPreferredCheckHour(parseInt(value))
                        }
                        disabled={isSavingSettings}
                      >
                        <SelectTrigger id="check-hour" className="w-[72px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="max-h-[200px]">
                          {Array.from({ length: 24 }, (_, i) => (
                            <SelectItem key={i} value={i.toString()}>
                              {i.toString().padStart(2, "0")}:00
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <span className="text-muted-foreground text-lg font-mono">
                      :
                    </span>
                    <div className="flex items-center gap-1">
                      <Label
                        htmlFor="check-minute"
                        className="text-sm text-muted-foreground mr-1"
                      >
                        Minute
                      </Label>
                      <Select
                        value={preferredCheckMinute.toString()}
                        onValueChange={(value) =>
                          setPreferredCheckMinute(parseInt(value))
                        }
                        disabled={isSavingSettings}
                      >
                        <SelectTrigger id="check-minute" className="w-[72px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">:00</SelectItem>
                          <SelectItem value="30">:30</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <span className="ml-2 text-xs text-muted-foreground">
                      (00:00 - 23:59 UTC)
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Set the time when automated channel checks should run. The system checks every 30 minutes (at :00 and :30), so only these minute values are available. Time is in your selected timezone.
                  </p>
                </div>

                <Separator />

                {/* Timezone Selector */}
                <div>
                  <Label className="mb-3" htmlFor="timezone">
                    Timezone
                  </Label>
                  <Select
                    value={timezone}
                    onValueChange={setTimezone}
                    disabled={isSavingSettings}
                  >
                    <SelectTrigger id="timezone">
                      <SelectValue placeholder="Select timezone" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {availableTimezones.map((tz) => (
                        <SelectItem key={tz} value={tz}>
                          {tz}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground mt-2">
                    Select your preferred timezone. This affects how scheduled
                    check times are displayed and calculated.
                  </p>
                </div>

                <Separator />

                {/* Save/Discard buttons */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2">
                    {hasUnsavedChanges && (
                      <Badge
                        variant="outline"
                        className="text-amber-600 border-amber-600"
                      >
                        Unsaved changes
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={handleDiscardChanges}
                      disabled={!hasUnsavedChanges || isSavingSettings}
                    >
                      Discard
                    </Button>
                    <Button
                      onClick={handleSaveSettings}
                      disabled={!hasUnsavedChanges || isSavingSettings}
                      className="gap-2"
                    >
                      {isSavingSettings ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          Save Changes
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderSystemTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>
            API connection and system health information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <HealthCheck />
        </CardContent>
      </Card>
    </div>
  )

  const renderAdvancedTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Library Management
          </CardTitle>
          <CardDescription>
            Manage your entire episode library and media files
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Delete All Episodes Section */}
          <div className="border border-destructive/20 rounded-lg p-4 bg-destructive/5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="font-semibold text-destructive mb-2">
                  Delete All Episodes
                </h4>
                <p className="text-sm text-muted-foreground mb-4">
                  Permanently delete all episodes and their media files from
                  your library. This action cannot be undone and will remove all
                  downloaded content.
                </p>

                {realChannelData ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">Channel:</span>
                      <Badge variant="outline">{realChannelData.name}</Badge>
                    </div>

                    <Button
                      variant="destructive"
                      onClick={handleDeleteLibraryClick}
                      className="gap-2"
                      disabled={isDeletingLibrary}
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete All Episodes
                    </Button>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    No channel data available. Please ensure your channel is
                    properly configured.
                  </div>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Task Management Section */}
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-foreground flex items-center gap-2">
                <ListTodo className="w-4 h-4" />
                Background Task Management
              </h4>
              <p className="text-sm text-muted-foreground mt-1">
                View and manage background tasks for video discovery and
                downloads
              </p>
            </div>

            {isLoadingTasks ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : tasksSummary ? (
              <div className="space-y-4">
                {/* Task Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Pending Tasks */}
                  <Card
                    className={cn(
                      "transition-colors",
                      (tasksSummary.by_status?.PENDING || 0) > 0 &&
                        "border-yellow-500/30 bg-yellow-500/5"
                    )}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">
                            Pending
                          </p>
                          <p className="text-2xl font-bold">
                            {tasksSummary.by_status?.PENDING || 0}
                          </p>
                        </div>
                        {(tasksSummary.by_status?.PENDING || 0) > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePurgeTasksClick("PENDING")}
                            className="gap-2"
                          >
                            <X className="w-3 h-3" />
                            Clear
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Failed Tasks */}
                  <Card
                    className={cn(
                      "transition-colors",
                      (tasksSummary.by_status?.FAILURE || 0) > 0 &&
                        "border-red-500/30 bg-red-500/5"
                    )}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">
                            Failed
                          </p>
                          <p className="text-2xl font-bold">
                            {tasksSummary.by_status?.FAILURE || 0}
                          </p>
                        </div>
                        {(tasksSummary.by_status?.FAILURE || 0) > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePurgeTasksClick("FAILURE")}
                            className="gap-2"
                          >
                            <X className="w-3 h-3" />
                            Clear
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Completed Tasks */}
                  <Card
                    className={cn(
                      "transition-colors",
                      (tasksSummary.by_status?.SUCCESS || 0) > 0 &&
                        "border-green-500/30 bg-green-500/5"
                    )}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">
                            Completed
                          </p>
                          <p className="text-2xl font-bold">
                            {tasksSummary.by_status?.SUCCESS || 0}
                          </p>
                        </div>
                        {(tasksSummary.by_status?.SUCCESS || 0) > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handlePurgeTasksClick("SUCCESS")}
                            className="gap-2"
                          >
                            <X className="w-3 h-3" />
                            Clear
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Total Count */}
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Total Tasks</span>
                  </div>
                  <Badge variant="secondary">{tasksSummary.total}</Badge>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No task data available</p>
              </div>
            )}
          </div>

          {/* Other Advanced Settings Placeholder */}
          <Separator />

          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Settings className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Additional Settings</h3>
            <p className="text-muted-foreground">
              More advanced configuration options will be available here in
              future updates.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <>
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="account" className="gap-2">
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Account</span>
          </TabsTrigger>
          <TabsTrigger value="tags" className="gap-2">
            <TagIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Tags</span>
          </TabsTrigger>
          <TabsTrigger value="channel" className="gap-2">
            <Radio className="w-4 h-4" />
            <span className="hidden sm:inline">Channel</span>
          </TabsTrigger>
          <TabsTrigger value="subscriptions" className="gap-2">
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">Subscriptions</span>
          </TabsTrigger>
          <TabsTrigger value="rss" className="gap-2">
            <Podcast className="w-4 h-4" />
            <span className="hidden sm:inline">RSS Feed</span>
          </TabsTrigger>
          <TabsTrigger value="system" className="gap-2">
            <Activity className="w-4 h-4" />
            <span className="hidden sm:inline">System Status</span>
          </TabsTrigger>
          <TabsTrigger value="advanced" className="gap-2">
            <Database className="w-4 h-4" />
            <span className="hidden sm:inline">Advanced</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="account">{renderAccountTab()}</TabsContent>
        <TabsContent value="tags">{renderTagsTab()}</TabsContent>
        <TabsContent value="channel">{renderChannelTab()}</TabsContent>
        <TabsContent value="subscriptions">
          {renderSubscriptionsTab()}
        </TabsContent>
        <TabsContent value="rss">{renderRSSTab()}</TabsContent>
        <TabsContent value="system">{renderSystemTab()}</TabsContent>
        <TabsContent value="advanced">{renderAdvancedTab()}</TabsContent>
      </Tabs>

      {/* Delete Library Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent
          className="max-w-2xl"
          showCloseButton={deleteStep !== "deleting"}
        >
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Delete All Episodes
            </DialogTitle>
            <DialogDescription>
              {deleteStep === "confirm" &&
                "This will permanently delete all episodes and media files from your library."}
              {deleteStep === "type-delete" &&
                'Please confirm by typing "DELETE" below.'}
              {deleteStep === "deleting" &&
                "Deleting all episodes and media files..."}
              {deleteStep === "result" && "Deletion operation completed."}
            </DialogDescription>
          </DialogHeader>

          {/* Confirmation Step */}
          {deleteStep === "confirm" && (
            <div className="space-y-4">
              <div className="border border-destructive/20 rounded-lg p-4 bg-destructive/5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-4 h-4 text-destructive" />
                  <span className="font-medium text-destructive">
                    Warning: This action cannot be undone
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <p>• All episode metadata will be permanently deleted</p>
                  <p>
                    • All downloaded media files will be removed from storage
                  </p>
                  <p>• You will need to re-add episodes manually</p>
                  <p>• RSS feed will be regenerated without any episodes</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Episode Count</Label>
                <div className="flex items-center gap-2">
                  {isLoadingCount ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">
                        Loading episode count...
                      </span>
                    </div>
                  ) : episodeCount !== null ? (
                    <div className="flex items-center gap-2">
                      <Badge variant="destructive" className="text-sm">
                        {episodeCount} episode{episodeCount !== 1 ? "s" : ""}{" "}
                        will be deleted
                      </Badge>
                      {episodeCount === 0 && (
                        <span className="text-sm text-muted-foreground">
                          (No episodes to delete)
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-sm text-destructive">
                      Failed to load episode count
                    </span>
                  )}
                </div>
              </div>

              {realChannelData && (
                <div className="space-y-2">
                  <Label>Channel</Label>
                  <Badge variant="outline">{realChannelData.name}</Badge>
                </div>
              )}
            </div>
          )}

          {/* Type DELETE Step */}
          {deleteStep === "type-delete" && (
            <div className="space-y-4">
              <div className="text-center p-4 border border-destructive/20 rounded-lg bg-destructive/5">
                <p className="text-sm font-medium text-destructive mb-2">
                  {episodeCount
                    ? `${episodeCount} episode${
                        episodeCount !== 1 ? "s" : ""
                      } will be permanently deleted`
                    : "Confirm deletion"}
                </p>
                <p className="text-xs text-muted-foreground">
                  This action cannot be reversed
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="delete-confirm">
                  Type <code className="bg-muted px-1 rounded">DELETE</code> to
                  confirm:
                </Label>
                <Input
                  id="delete-confirm"
                  placeholder="Type DELETE to confirm"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className={cn(
                    deleteConfirmText === "DELETE" &&
                      "border-destructive focus:border-destructive"
                  )}
                  autoFocus
                />
              </div>
            </div>
          )}

          {/* Deleting Step */}
          {deleteStep === "deleting" && (
            <div className="space-y-4">
              <div className="flex items-center justify-center p-8">
                <div className="text-center space-y-4">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto text-destructive" />
                  <div>
                    <p className="font-medium">
                      Deleting episodes and media files...
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      This may take several minutes for large libraries
                    </p>
                  </div>
                </div>
              </div>

              <div className="border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  <span className="text-sm text-amber-800 dark:text-amber-200">
                    Please do not close this dialog or navigate away during
                    deletion
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Result Step */}
          {deleteStep === "result" && deleteResult && (
            <div className="space-y-4">
              <div
                className={cn(
                  "border rounded-lg p-4",
                  deleteResult.success
                    ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950"
                    : "border-destructive/20 bg-destructive/5"
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  {deleteResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-destructive" />
                  )}
                  <span
                    className={cn(
                      "font-medium",
                      deleteResult.success
                        ? "text-green-800 dark:text-green-200"
                        : "text-destructive"
                    )}
                  >
                    {deleteResult.success
                      ? "Deletion Completed"
                      : "Deletion Failed"}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {deleteResult.message}
                </p>
              </div>

              {deleteResult.details && (
                <div className="space-y-3">
                  <h4 className="font-medium">Operation Details</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-1">
                      <span className="text-muted-foreground">
                        Total Episodes:
                      </span>
                      <div className="font-medium">
                        {deleteResult.details.total_episodes || 0}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <span className="text-muted-foreground">
                        Deleted Episodes:
                      </span>
                      <div className="font-medium text-green-600">
                        {deleteResult.details.deleted_episodes || 0}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <span className="text-muted-foreground">
                        Failed Episodes:
                      </span>
                      <div className="font-medium text-destructive">
                        {deleteResult.details.failed_episodes || 0}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <span className="text-muted-foreground">
                        Deleted Files:
                      </span>
                      <div className="font-medium text-green-600">
                        {deleteResult.details.deleted_files || 0}
                      </div>
                    </div>
                  </div>

                  {deleteResult.details.failed_episode_details &&
                    deleteResult.details.failed_episode_details.length > 0 && (
                      <div className="space-y-2">
                        <h5 className="font-medium text-destructive">
                          Failed Episodes
                        </h5>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {deleteResult.details.failed_episode_details.map(
                            (
                              failed: Record<string, unknown>,
                              index: number
                            ) => (
                              <div
                                key={index}
                                className="text-xs bg-muted p-2 rounded"
                              >
                                <div className="font-medium">
                                  {String(failed.title || "Unknown")}
                                </div>
                                <div className="text-muted-foreground">
                                  {Array.isArray(failed.errors)
                                    ? failed.errors.join(", ")
                                    : "Unknown error"}
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            {deleteStep === "confirm" && (
              <>
                <Button variant="outline" onClick={handleDeleteCancel}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDeleteConfirm}
                  disabled={episodeCount === 0 || isLoadingCount}
                >
                  Continue
                </Button>
              </>
            )}

            {deleteStep === "type-delete" && (
              <>
                <Button variant="outline" onClick={handleDeleteCancel}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDeleteExecute}
                  disabled={deleteConfirmText !== "DELETE" || isDeletingLibrary}
                  className="gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete All Episodes
                </Button>
              </>
            )}

            {deleteStep === "deleting" && (
              <Button variant="outline" disabled>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Deleting...
              </Button>
            )}

            {deleteStep === "result" && (
              <Button onClick={resetDeleteDialog}>
                {deleteResult?.success ? "Close" : "Close"}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Purge Tasks Confirmation Dialog */}
      <Dialog open={showPurgeDialog} onOpenChange={setShowPurgeDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Clear {purgeStatus} Tasks
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to clear all {purgeStatus} tasks from the
              database?
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="border border-yellow-500/20 rounded-lg p-4 bg-yellow-500/5">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-yellow-500" />
                <span className="font-medium text-yellow-600 dark:text-yellow-500">
                  This will:
                </span>
              </div>
              <div className="space-y-1 text-sm text-muted-foreground">
                {purgeStatus === "PENDING" && (
                  <>
                    <p>• Revoke all pending tasks from the queue</p>
                    <p>• Remove task records from the database</p>
                    <p>• Stop tasks from being executed</p>
                  </>
                )}
                {purgeStatus === "FAILURE" && (
                  <>
                    <p>• Remove all failed task records</p>
                    <p>• Clear error logs from the database</p>
                    <p>• Clean up stuck/failed tasks</p>
                  </>
                )}
                {purgeStatus === "SUCCESS" && (
                  <>
                    <p>• Remove all completed task records</p>
                    <p>• Clear task history from the database</p>
                    <p>• Free up database space</p>
                  </>
                )}
              </div>
            </div>

            {tasksSummary && (
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <span className="text-sm font-medium">
                  Tasks to be cleared:
                </span>
                <Badge variant="secondary">
                  {tasksSummary.by_status?.[purgeStatus] || 0}
                </Badge>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={handlePurgeTasksCancel}
              disabled={purgeTasks.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handlePurgeTasksExecute}
              disabled={purgeTasks.isPending}
              className="gap-2"
            >
              {purgeTasks.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Clearing...
                </>
              ) : (
                <>
                  <X className="w-4 h-4" />
                  Clear Tasks
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
