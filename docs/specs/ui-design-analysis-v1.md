# UI/UX Design Specification for LabCastARR

**Project:** LabCastARR - Personal Podcast Channel Creator  
**Version:** 2.0 - Next.js + FastAPI Implementation  
**Date:** September 10, 2025  
**Author:** AI UI/UX Analyst  

---

## 1. Introduction & Goals

### 1.1 Purpose of Redesign

LabCastARR is a modern homelab application that allows users to download audio tracks from YouTube videos and create personal podcast channels compatible with popular podcast applications like Spotify and Apple Podcasts. This specification outlines the UI/UX design for the new Next.js + FastAPI implementation.

**Key Requirements:**
- **Single-user homelab application** with API key authentication
- **Modern tech stack**: Next.js 15+, FastAPI, ShadCN v4, TailwindCSS v4
- **YouTube-to-podcast workflow** with real-time progress tracking
- **Clean, functional interface** optimized for personal use

### 1.2 Design Vision & Guiding Principles

**Vision Statement:** Create a clean, efficient, and modern interface that makes converting YouTube videos to podcast episodes effortless and enjoyable.

**Core Principles:**
1. **Functionality First**: Clean, uncluttered interfaces focusing on core workflow
2. **YouTube-Inspired**: Familiar card-based layouts users understand
3. **Real-time Feedback**: Live progress updates and status indicators
4. **Mobile-Responsive**: Works seamlessly across all devices
5. **Performance-Oriented**: Fast loading with optimized interactions
6. **Homelab-Friendly**: Simple deployment and maintenance

---

## 2. Application Architecture Overview

### 2.1 Page Structure

**Primary Pages (Authenticated Only):**
- **Channel Page** (`/channel`) - Main dashboard with episode grid
- **Add Episode Page** (`/episodes/add`) - YouTube URL input form
- **Episode Detail Page** (`/episodes/[id]`) - Individual episode management
- **Settings Page** (`/settings`) - Channel configuration and tags management

**Redirects:**
- Home Page (`/`) → redirects to `/channel`

**API Endpoints:**
- RSS Feed (`/feed`) - Public podcast feed
- Static Media (`/static/media/*`) - Audio file serving

### 2.2 Navigation Structure

```
Top Navigation:
├── Brand Logo (LabCastARR)
├── Channel (main dashboard)
├── Add Episode (+ icon)
├── Settings (gear icon)
├── Search Bar (filter episodes)
└── Notifications (download progress)

No user authentication UI - API key handled in backend
```

---

## 3. New Design System (ShadCN + TailwindCSS v4)

### 3.1 Color Palette

**Primary Colors (YouTube-Inspired with Dark Theme):**
```css
/* TailwindCSS v4 Custom Properties */
@theme {
  --color-primary: #ef4444;      /* Red-500 */
  --color-primary-foreground: #ffffff;
  
  --color-secondary: #f1f5f9;    /* Slate-100 */
  --color-secondary-foreground: #0f172a; /* Slate-900 */
  
  --color-background: #ffffff;
  --color-foreground: #0f172a;   /* Slate-900 */
  
  --color-card: #ffffff;
  --color-card-foreground: #0f172a;
  
  --color-popover: #ffffff;
  --color-popover-foreground: #0f172a;
  
  --color-muted: #f8fafc;        /* Slate-50 */
  --color-muted-foreground: #64748b; /* Slate-500 */
  
  --color-accent: #f1f5f9;       /* Slate-100 */
  --color-accent-foreground: #0f172a;
  
  --color-destructive: #dc2626;  /* Red-600 */
  --color-destructive-foreground: #ffffff;
  
  --color-border: #e2e8f0;       /* Slate-200 */
  --color-input: #e2e8f0;        /* Slate-200 */
  --color-ring: #ef4444;         /* Red-500 */
}

/* Dark Mode Support */
.dark {
  --color-background: #0f0f0f;
  --color-foreground: #fafafa;
  --color-card: #1a1a1a;
  --color-card-foreground: #fafafa;
  --color-popover: #1a1a1a;
  --color-popover-foreground: #fafafa;
  --color-muted: #262626;
  --color-muted-foreground: #a3a3a3;
  --color-accent: #262626;
  --color-accent-foreground: #fafafa;
  --color-border: #404040;
  --color-input: #404040;
}

/* Status Colors */
@theme {
  --color-success: #10b981;      /* Emerald-500 */
  --color-warning: #f59e0b;      /* Amber-500 */
  --color-error: #ef4444;        /* Red-500 */
  --color-info: #3b82f6;         /* Blue-500 */
}
```

### 3.2 Typography (TailwindCSS v4 + Inter)

**Font Configuration:**
```css
@theme {
  --font-family-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif;
  --font-family-mono: ui-monospace, "JetBrains Mono", "Fira Code", monospace;
}

/* Type Scale */
@theme {
  --font-size-xs: 0.75rem;      /* 12px */
  --font-size-sm: 0.875rem;     /* 14px */
  --font-size-base: 1rem;       /* 16px */
  --font-size-lg: 1.125rem;     /* 18px */
  --font-size-xl: 1.25rem;      /* 20px */
  --font-size-2xl: 1.5rem;      /* 24px */
  --font-size-3xl: 1.875rem;    /* 30px */
  --font-size-4xl: 2.25rem;     /* 36px */
  --font-size-5xl: 3rem;        /* 48px */
}

/* Font Weights */
@theme {
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}

/* Line Heights */
@theme {
  --line-height-tight: 1.25;
  --line-height-snug: 1.375;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.625;
}
```

### 3.3 Spacing & Layout (TailwindCSS v4)

**Spacing Scale:**
```css
@theme {
  --spacing-px: 1px;
  --spacing-0: 0;
  --spacing-0_5: 0.125rem;      /* 2px */
  --spacing-1: 0.25rem;         /* 4px */
  --spacing-1_5: 0.375rem;      /* 6px */
  --spacing-2: 0.5rem;          /* 8px */
  --spacing-2_5: 0.625rem;      /* 10px */
  --spacing-3: 0.75rem;         /* 12px */
  --spacing-3_5: 0.875rem;      /* 14px */
  --spacing-4: 1rem;            /* 16px */
  --spacing-5: 1.25rem;         /* 20px */
  --spacing-6: 1.5rem;          /* 24px */
  --spacing-8: 2rem;            /* 32px */
  --spacing-10: 2.5rem;         /* 40px */
  --spacing-12: 3rem;           /* 48px */
  --spacing-16: 4rem;           /* 64px */
  --spacing-20: 5rem;           /* 80px */
  --spacing-24: 6rem;           /* 96px */
}
```

**Breakpoints:**
```css
@theme {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

**Container Sizes:**
```css
@theme {
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}
```

### 3.4 Component Specifications (ShadCN v4)

**Border Radius:**
```css
@theme {
  --radius: 0.5rem;             /* 8px - default */
  --radius-sm: 0.25rem;         /* 4px */
  --radius-md: 0.375rem;        /* 6px */
  --radius-lg: 0.75rem;         /* 12px */
  --radius-xl: 1rem;            /* 16px */
  --radius-full: 9999px;
}
```

**Shadows:**
```css
@theme {
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}
```

### 3.5 Icon System (Lucide React)

**Icon Configuration:**
- **Library**: Lucide React v0.400+
- **Default Size**: 20px (w-5 h-5)
- **Stroke Width**: 2px
- **Style**: Outlined icons with consistent stroke
- **Usage**: Import individual icons for better tree-shaking

```typescript
// Example icon imports
import { Plus, Settings, Search, Bell, Play, Download, Trash2 } from 'lucide-react'
```

---

## 4. ShadCN Component Library Specifications

### 4.1 Button Component

```typescript
interface ButtonProps {
  variant: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size: 'default' | 'sm' | 'lg' | 'icon'
  disabled?: boolean
  loading?: boolean
  children: React.ReactNode
}
```

**Button Variants:**
- **Default**: Primary red background (`bg-primary text-primary-foreground`)
- **Destructive**: Red destructive (`bg-destructive text-destructive-foreground`)
- **Outline**: Border with transparent background (`border border-input bg-background`)
- **Secondary**: Secondary background (`bg-secondary text-secondary-foreground`)
- **Ghost**: Transparent with hover effects (`hover:bg-accent hover:text-accent-foreground`)
- **Link**: Text-only button (`text-primary underline-offset-4 hover:underline`)

### 4.2 Card Component

```typescript
interface CardProps {
  className?: string
  children: React.ReactNode
}

interface EpisodeCardProps {
  episode: {
    id: string
    title: string
    author: string
    description: string
    thumbnail: string
    duration: string
    publishedAt: string
    downloadStatus: 'pending' | 'downloading' | 'completed' | 'error'
    progress?: number
  }
  onPlay?: () => void
  onDelete?: () => void
  onEdit?: () => void
}
```

**Card Structure:**
```tsx
<Card className="overflow-hidden">
  <div className="aspect-video relative">
    <Image src={thumbnail} alt={title} className="object-cover" fill />
    <Badge variant="secondary" className="absolute bottom-2 right-2">
      {duration}
    </Badge>
  </div>
  <CardContent className="p-4">
    <CardTitle className="line-clamp-2">{title}</CardTitle>
    <p className="text-sm text-muted-foreground">{author}</p>
    <p className="text-xs text-muted-foreground mt-1">{publishedAt}</p>
  </CardContent>
</Card>
```

### 4.3 Input & Form Components

```typescript
interface InputProps {
  type?: string
  placeholder?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  className?: string
  disabled?: boolean
  error?: string
}

interface FormFieldProps {
  label: string
  description?: string
  error?: string
  children: React.ReactNode
}
```

**Form Implementation with react-hook-form + Zod:**
```tsx
const formSchema = z.object({
  url: z.string().url("Please enter a valid YouTube URL"),
})

export function AddEpisodeForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { url: "" },
  })

  return (
    <Form {...form}>
      <FormField
        control={form.control}
        name="url"
        render={({ field }) => (
          <FormItem>
            <FormLabel>YouTube URL</FormLabel>
            <FormControl>
              <Input placeholder="https://youtube.com/watch?v=..." {...field} />
            </FormControl>
            <FormDescription>
              Paste the URL of the YouTube video you want to add
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </Form>
  )
}
```

### 4.4 Navigation Components

```typescript
interface NavigationProps {
  currentPath: string
  notifications?: NotificationItem[]
}

interface NotificationItem {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
  timestamp: string
  progress?: number
}
```

**Top Navigation Structure:**
```tsx
<header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
  <div className="container flex h-14 items-center">
    <div className="mr-4 hidden md:flex">
      <Link href="/channel" className="mr-6 flex items-center space-x-2">
        <Icons.logo className="h-6 w-6" />
        <span className="hidden font-bold sm:inline-block">LabCastARR</span>
      </Link>
      <nav className="flex items-center space-x-6 text-sm font-medium">
        <Link href="/channel">Channel</Link>
        <Link href="/episodes/add">
          <Plus className="h-4 w-4" />
        </Link>
        <Link href="/settings">Settings</Link>
      </nav>
    </div>
    <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
      <div className="w-full flex-1 md:w-auto md:flex-none">
        <SearchInput />
      </div>
      <NotificationDropdown />
    </div>
  </div>
</header>
```

### 4.5 Progress & Status Components

```typescript
interface ProgressProps {
  value: number
  max?: number
  className?: string
}

interface StatusBadgeProps {
  status: 'pending' | 'downloading' | 'completed' | 'error'
  progress?: number
}
```

**Progress Component:**
```tsx
export function DownloadProgress({ value, max = 100 }: ProgressProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-muted-foreground">Downloading...</span>
        <span className="text-muted-foreground">{value}%</span>
      </div>
      <Progress value={value} className="w-full" />
    </div>
  )
}
```

---

## 5. Screen Specifications

### 5.1 Channel Page (`/channel`) - Main Dashboard

**Purpose**: Primary interface displaying all downloaded episodes in a YouTube-style grid

**Layout Structure:**
```
Header Navigation (Sticky)
├── LabCastARR Logo
├── Channel (active)
├── Add Episode (+)
├── Settings
├── Search Bar
└── Notifications

Channel Overview Section
├── Channel Statistics (Total Episodes, Storage Used)
├── RSS Feed URL (Copy Button)
├── Quick Actions (Add Episode, Regenerate Feed)
└── Sort/Filter Controls

Episode Grid
├── Responsive Grid Layout (1-6 columns based on screen size)
├── Episode Cards with Thumbnails
├── Loading Skeletons for Downloading Episodes
├── Empty State (No Episodes Yet)
└── Pagination (if needed)

Floating Action Button (Mobile)
└── Add Episode (+) - Fixed bottom right
```

**Responsive Grid:**
```css
/* Grid Layout */
.episodes-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

/* Responsive breakpoints */
@media (min-width: 640px) {
  .episodes-grid {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
}
```

**Episode Card States:**
- **Completed**: Full card with play button, thumbnail, metadata
- **Downloading**: Card with progress bar and loading spinner
- **Pending**: Placeholder card with metadata, no audio yet
- **Error**: Card with error indicator and retry option

### 5.2 Add Episode Page (`/episodes/add`)

**Purpose**: Simple form to submit YouTube URLs for processing

**Layout Structure:**
```
Header Navigation
├── Breadcrumb: Channel > Add Episode

Main Form Section
├── Page Title: "Add New Episode"
├── URL Input Field (Large, Prominent)
├── Validation Messages
├── Submit Button
└── Helper Text/Examples

URL Preview Section (After Valid URL)
├── Video Thumbnail
├── Title and Channel Name
├── Duration and Upload Date
├── Confirm Addition Button
└── Cancel Option

Processing State (After Submission)
├── Progress Steps Indicator
├── Current Status Message
├── Progress Bar (if available)
├── Cancel Download Option
└── View Channel Button
```

**Form Implementation:**
```tsx
export function AddEpisodeForm() {
  const [preview, setPreview] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Add New Episode</CardTitle>
        <CardDescription>
          Paste a YouTube URL to add it to your podcast channel
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4">
          <FormField>
            <FormLabel>YouTube URL</FormLabel>
            <Input
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              className="text-lg py-3"
            />
            <FormDescription>
              Supports youtube.com and youtu.be links
            </FormDescription>
          </FormField>
          
          {preview && (
            <VideoPreview video={preview} />
          )}
          
          <Button type="submit" className="w-full" size="lg">
            Add Episode
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
```

### 5.3 Episode Detail Page (`/episodes/[id]`)

**Purpose**: Full episode management interface with playback and editing

**Layout Structure:**
```
Header Navigation
├── Breadcrumb: Channel > Episode Title

Episode Header
├── Large Thumbnail
├── Play/Pause Button (HTML5 Audio)
├── Episode Title (Editable)
├── Author/Channel Name
├── Publication Date
└── Action Buttons (Edit, Delete, YouTube Link)

Episode Content
├── Audio Player (Full Controls)
├── Description (Expandable, Editable)
├── Tags (Editable Chips)
├── Duration and File Size
└── Download Link

Metadata Section
├── Original YouTube URL
├── Download Date
├── File Format and Quality
├── Processing Status
└── RSS Feed Status

Edit Mode (Toggle)
├── Editable Form Fields
├── Tag Management
├── Save/Cancel Actions
└── Validation Messages
```

**Audio Player Integration:**
```tsx
export function EpisodePlayer({ episode }: { episode: Episode }) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center space-x-4">
          <div className="relative w-24 h-24 flex-shrink-0">
            <Image
              src={episode.thumbnail}
              alt={episode.title}
              className="rounded-md object-cover"
              fill
            />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold truncate">{episode.title}</h3>
            <p className="text-sm text-muted-foreground">{episode.author}</p>
            <audio
              controls
              className="w-full mt-2"
              src={episode.audioUrl}
              preload="metadata"
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### 5.4 Settings Page (`/settings`)

**Purpose**: Channel configuration, RSS feed management, and tag administration

**Layout Structure:**
```
Header Navigation
├── Breadcrumb: Channel > Settings

Settings Navigation (Tabs)
├── Channel Info
├── RSS Configuration
├── Tags Management
└── Advanced

Channel Info Section
├── Podcast Name (Required)
├── Description (Rich Text)
├── Channel Image URL
├── Website URL
├── Category Selection
├── Language Selection
└── Explicit Content Toggle

RSS Configuration
├── Generated Feed URL (Copy Button)
├── Author Information
├── Owner Information
├── Copyright Information
├── Regenerate Feed Button
└── Feed Validation Status

Tags Management
├── Existing Tags List
├── Add New Tag Form
├── Tag Usage Statistics
├── Bulk Tag Operations
└── Tag Color Coding

Advanced Settings
├── Download Quality Preferences
├── File Format Options
├── Storage Management
├── API Configuration
└── Export/Import Data
```

**Settings Form Implementation:**
```tsx
export function ChannelSettings() {
  const form = useForm<ChannelSettings>({
    resolver: zodResolver(channelSettingsSchema),
  })
  
  return (
    <Tabs defaultValue="channel" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="channel">Channel Info</TabsTrigger>
        <TabsTrigger value="rss">RSS Feed</TabsTrigger>
        <TabsTrigger value="tags">Tags</TabsTrigger>
        <TabsTrigger value="advanced">Advanced</TabsTrigger>
      </TabsList>
      
      <TabsContent value="channel" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Channel Information</CardTitle>
            <CardDescription>
              Configure your podcast channel details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField name="name">
                  <FormLabel>Podcast Name</FormLabel>
                  <FormControl>
                    <Input placeholder="My Awesome Podcast" />
                  </FormControl>
                </FormField>
                
                <FormField name="category">
                  <FormLabel>Category</FormLabel>
                  <FormControl>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="technology">Technology</SelectItem>
                        <SelectItem value="education">Education</SelectItem>
                        <SelectItem value="entertainment">Entertainment</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                </FormField>
              </div>
            </Form>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  )
}
```

---

## 6. Real-time Features & WebSocket Integration

### 6.1 Download Progress Tracking

**WebSocket Connection:**
```typescript
interface DownloadProgress {
  episodeId: string
  status: 'pending' | 'downloading' | 'processing' | 'completed' | 'error'
  progress: number
  message: string
  estimatedTime?: string
}

export function useDownloadProgress(episodeId: string) {
  const [progress, setProgress] = useState<DownloadProgress>()
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/episodes/${episodeId}/progress`)
    
    ws.onmessage = (event) => {
      const data: DownloadProgress = JSON.parse(event.data)
      setProgress(data)
    }
    
    return () => ws.close()
  }, [episodeId])
  
  return progress
}
```

### 6.2 Notification System

**Notification Types:**
- Download started
- Download progress updates
- Download completed
- Download failed
- RSS feed updated
- Storage warnings

**Implementation:**
```tsx
export function NotificationDropdown() {
  const { notifications, markAsRead, clearAll } = useNotifications()
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          {notifications.length > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 text-xs">
              {notifications.length}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>Notifications</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onMarkAsRead={markAsRead}
          />
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

---

## 7. Responsive Design Strategy

### 7.1 Mobile-First Approach

**Breakpoint Strategy:**
```css
/* Mobile First (320px+) */
.episodes-grid {
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* Tablet (640px+) */
@media (min-width: 640px) {
  .episodes-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .episodes-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Large Desktop (1280px+) */
@media (min-width: 1280px) {
  .episodes-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

### 7.2 Touch-Friendly Design

**Touch Targets:**
- Minimum 44px touch targets
- Adequate spacing between interactive elements
- Swipe gestures for card actions (future enhancement)
- Pull-to-refresh for episode list

**Mobile Navigation:**
```tsx
export function MobileNavigation() {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-background border-t md:hidden">
      <nav className="flex items-center justify-around py-2">
        <Link href="/channel" className="flex flex-col items-center p-2">
          <Home className="h-5 w-5" />
          <span className="text-xs mt-1">Channel</span>
        </Link>
        <Link href="/episodes/add" className="flex flex-col items-center p-2">
          <Plus className="h-5 w-5" />
          <span className="text-xs mt-1">Add</span>
        </Link>
        <Link href="/settings" className="flex flex-col items-center p-2">
          <Settings className="h-5 w-5" />
          <span className="text-xs mt-1">Settings</span>
        </Link>
      </nav>
    </div>
  )
}
```

---

## 8. Performance & Optimization

### 8.1 Image Optimization

**Next.js Image Component:**
```tsx
import { Image } from 'next/image'

export function EpisodeThumbnail({ src, alt, ...props }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={320}
      height={180}
      className="rounded-md object-cover"
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      {...props}
    />
  )
}
```

### 8.2 Data Fetching with React Query

**Episode List Query:**
```typescript
export function useEpisodes() {
  return useQuery({
    queryKey: ['episodes'],
    queryFn: async () => {
      const response = await fetch('/api/episodes')
      return response.json()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds for active downloads
  })
}

export function useEpisode(id: string) {
  return useQuery({
    queryKey: ['episodes', id],
    queryFn: async () => {
      const response = await fetch(`/api/episodes/${id}`)
      return response.json()
    },
  })
}
```

### 8.3 Loading States

**Skeleton Components:**
```tsx
export function EpisodeCardSkeleton() {
  return (
    <Card>
      <div className="aspect-video bg-muted animate-pulse rounded-t-lg" />
      <CardContent className="p-4">
        <Skeleton className="h-4 w-3/4 mb-2" />
        <Skeleton className="h-3 w-1/2 mb-1" />
        <Skeleton className="h-3 w-1/4" />
      </CardContent>
    </Card>
  )
}
```

---

## 9. Accessibility Features

### 9.1 WCAG 2.1 AA Compliance

**Keyboard Navigation:**
- All interactive elements accessible via keyboard
- Logical tab order throughout application
- Visible focus indicators
- Skip links for main content areas

**Screen Reader Support:**
```tsx
export function EpisodeCard({ episode }) {
  return (
    <Card role="article" aria-labelledby={`episode-${episode.id}-title`}>
      <div className="aspect-video relative">
        <Image
          src={episode.thumbnail}
          alt={`Thumbnail for ${episode.title}`}
          fill
          className="object-cover"
        />
      </div>
      <CardContent>
        <CardTitle id={`episode-${episode.id}-title`}>
          {episode.title}
        </CardTitle>
        <p className="sr-only">
          Episode by {episode.author}, duration {episode.duration}
        </p>
        <Button
          aria-label={`Play ${episode.title}`}
          onClick={() => onPlay(episode)}
        >
          <Play className="h-4 w-4" />
          <span className="sr-only">Play episode</span>
        </Button>
      </CardContent>
    </Card>
  )
}
```

### 9.2 Color Contrast & Visual Design

**Contrast Ratios:**
- Text on background: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: 3:1 minimum
- Focus indicators: 3:1 minimum

**Color-blind Friendly:**
- Status indicators use icons + color
- Error states include descriptive text
- Progress indicators show percentage

---

## 10. Implementation Roadmap

### 10.1 Phase 1: Core Foundation (Week 1-2)
- [ ] **Setup Next.js 15 + TailwindCSS v4 + ShadCN**
- [ ] **Implement base design system and theme**
- [ ] **Create core layout components (Header, Navigation)**
- [ ] **Setup React Query for data fetching**
- [ ] **Implement API key authentication**

### 10.2 Phase 2: Main Features (Week 3-4)
- [ ] **Channel page with episode grid**
- [ ] **Add episode form with validation**
- [ ] **Episode detail page with audio player**
- [ ] **Settings page with tabs**
- [ ] **Basic WebSocket integration for progress**

### 10.3 Phase 3: Enhanced UX (Week 5-6)
- [ ] **Real-time notifications system**
- [ ] **Search and filtering functionality**
- [ ] **Mobile responsive optimizations**
- [ ] **Loading states and error handling**
- [ ] **Accessibility improvements**

### 10.4 Phase 4: Polish & Optimization (Week 7-8)
- [ ] **Performance optimizations**
- [ ] **Advanced WebSocket features**
- [ ] **Tag management system**
- [ ] **RSS feed management UI**
- [ ] **Testing and bug fixes**

---

## 11. Success Metrics

### 11.1 Technical Metrics
- **Performance**: Lighthouse scores > 90
- **Accessibility**: WCAG 2.1 AA compliance
- **Mobile Responsiveness**: Works on all device sizes
- **Real-time Updates**: < 1 second latency for progress updates

### 11.2 User Experience Metrics
- **Task Completion**: Adding episode in < 30 seconds
- **Error Recovery**: Clear error messages and retry options
- **Loading Performance**: First contentful paint < 1.5s
- **Mobile Usability**: Touch-friendly interactions

---

## Conclusion

This specification provides a comprehensive blueprint for building a modern, efficient, and user-friendly LabCastARR interface using Next.js 15, ShadCN v4, and TailwindCSS v4. The design focuses on simplicity, performance, and real-time feedback while maintaining a clean, YouTube-inspired aesthetic suitable for a homelab environment.

The component-based architecture ensures maintainability and scalability, while the responsive design guarantees a consistent experience across all devices. Real-time WebSocket integration provides immediate feedback on download progress, enhancing the user experience significantly.

**Next Steps:**
1. Setup development environment with specified tech stack
2. Implement design system and base components
3. Build core pages following the specifications
4. Integrate real-time features and WebSocket connections
5. Optimize for performance and accessibility

---

**Document Version**: 1.0  
**Last Updated**: September 10, 2025  
**Tech Stack**: Next.js 15+ • FastAPI • ShadCN v4 • TailwindCSS v4 • TypeScript  
**Target**: Homelab Personal Use
