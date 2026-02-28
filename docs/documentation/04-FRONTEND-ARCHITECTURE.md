# LabCastARR Frontend Architecture

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Directory Structure](#directory-structure)
3. [Pages and Routing](#pages-and-routing)
4. [Component Organization](#component-organization)
5. [State Management](#state-management)
6. [Custom Hooks](#custom-hooks)
7. [API Integration](#api-integration)
8. [Authentication Flow](#authentication-flow)
9. [Styling Approach](#styling-approach)
10. [Key Component Reference](#key-component-reference)

---

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.x | React framework with App Router |
| React | 18+ | UI library |
| TypeScript | 5.x | Type safety |
| TailwindCSS | v4 | Utility-first CSS |
| ShadCN UI | Latest | Component library (Radix-based) |
| React Query | @tanstack/react-query | Server state management |
| React Hook Form | Latest | Form management |
| Zod | Latest | Schema validation |
| Sonner | Latest | Toast notifications |
| React Dropzone | Latest | File upload handling |

---

## Directory Structure

```
frontend/src/
├── app/                              # Next.js App Router
│   ├── layout.tsx                    # Root layout with providers
│   ├── page.tsx                      # Home page (redirects to /channel)
│   ├── globals.css                   # Global styles + Tailwind
│   │
│   ├── login/
│   │   └── page.tsx                  # Login page
│   ├── setup/
│   │   └── page.tsx                  # Initial setup wizard
│   ├── channel/
│   │   └── page.tsx                  # Channel dashboard (main view)
│   │
│   ├── episodes/
│   │   ├── add/
│   │   │   └── page.tsx              # Add episode method selection
│   │   ├── add-from-youtube/
│   │   │   └── page.tsx              # YouTube URL form
│   │   ├── add-from-upload/
│   │   │   └── page.tsx              # File upload form
│   │   └── [id]/
│   │       └── page.tsx              # Episode detail view
│   │
│   ├── subscriptions/
│   │   ├── page.tsx                  # Subscriptions landing
│   │   ├── channels/
│   │   │   └── page.tsx              # Followed YouTube channels
│   │   └── videos/
│   │       └── page.tsx              # Discovered videos list
│   │
│   ├── search/
│   │   └── page.tsx                  # Advanced search
│   ├── settings/
│   │   └── page.tsx                  # User & channel settings
│   ├── activity/
│   │   └── page.tsx                  # Event log / activity table
│   └── not-found.tsx                 # 404 page
│
├── components/
│   ├── ui/                           # ShadCN UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── form.tsx
│   │   ├── select.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   ├── skeleton.tsx
│   │   ├── toast.tsx
│   │   ├── sonner.tsx
│   │   └── ... (30+ components)
│   │
│   ├── features/                     # Feature-specific components
│   │   ├── episodes/
│   │   │   ├── episode-card.tsx
│   │   │   ├── episode-grid.tsx
│   │   │   ├── episode-detail.tsx
│   │   │   ├── add-episode-form.tsx
│   │   │   ├── upload-episode-form.tsx
│   │   │   ├── audio-player.tsx
│   │   │   ├── search-bar.tsx
│   │   │   ├── filter-panel.tsx
│   │   │   └── bulk-actions.tsx
│   │   │
│   │   ├── channels/
│   │   │   ├── channel-form.tsx
│   │   │   └── create-channel-form.tsx
│   │   │
│   │   ├── subscriptions/
│   │   │   ├── follow-channel-modal.tsx
│   │   │   ├── followed-channels-list.tsx
│   │   │   ├── video-list.tsx
│   │   │   └── youtube-video-card.tsx
│   │   │
│   │   ├── tags/
│   │   │   ├── tag-manager.tsx
│   │   │   └── tag-selector.tsx
│   │   │
│   │   ├── activity/
│   │   │   ├── activity-table.tsx
│   │   │   ├── activity-filters.tsx
│   │   │   └── date-range-picker.tsx
│   │   │
│   │   ├── settings/
│   │   │   └── settings-interface.tsx
│   │   │
│   │   ├── search/
│   │   │   └── search-interface.tsx
│   │   │
│   │   └── notifications/
│   │       └── notification-item.tsx
│   │
│   ├── layout/                       # Layout components
│   │   ├── main-layout.tsx           # Main app wrapper
│   │   ├── auth-layout.tsx           # Auth pages wrapper
│   │   ├── header.tsx                # Top navigation
│   │   ├── sidepanel.tsx             # Side navigation
│   │   ├── mobile-nav.tsx            # Mobile navigation
│   │   ├── notification-bell.tsx     # Notification dropdown
│   │   └── page-header.tsx           # Page title component
│   │
│   ├── providers/                    # React context providers
│   │   ├── auth-provider.tsx         # JWT authentication
│   │   ├── query-provider.tsx        # React Query setup
│   │   └── theme-provider.tsx        # Dark/light theme
│   │
│   └── shared/                       # Shared utilities
│       ├── file-dropzone.tsx         # Drag-drop file upload
│       ├── loading.tsx               # Loading spinner
│       ├── theme-toggle.tsx          # Theme switcher
│       └── pagination-controls.tsx   # Pagination UI
│
├── hooks/                            # Custom React hooks
│   ├── use-episodes.ts               # Episode CRUD
│   ├── use-channels.ts               # Channel CRUD
│   ├── use-followed-channels.ts      # Subscriptions
│   ├── use-youtube-videos.ts         # Discovered videos
│   ├── use-notifications.ts          # Notifications
│   ├── use-task-status.ts            # Celery task polling
│   ├── use-search.ts                 # Search functionality
│   ├── use-tags.ts                   # Tag management
│   ├── use-toast.ts                  # Toast notifications
│   ├── use-health.ts                 # Backend health check
│   └── use-activity-detection.ts     # Activity for token refresh
│
├── lib/                              # Utilities
│   ├── api.ts                        # API client configuration
│   ├── query-client.ts               # React Query config
│   ├── utils.ts                      # General utilities
│   └── security.ts                   # Security helpers
│
├── types/                            # TypeScript definitions
│   ├── episode.ts                    # Episode interfaces
│   └── index.ts                      # Type exports
│
└── contexts/                         # React contexts
    └── auth-context.tsx              # Authentication context
```

---

## Pages and Routing

### Route Map

| Route | Page Component | Description |
|-------|----------------|-------------|
| `/` | `page.tsx` | Redirects to `/channel` |
| `/login` | `login/page.tsx` | User authentication |
| `/setup` | `setup/page.tsx` | Initial setup wizard |
| `/channel` | `channel/page.tsx` | Main dashboard with episodes |
| `/episodes/add` | `episodes/add/page.tsx` | Choose add method |
| `/episodes/add-from-youtube` | `episodes/add-from-youtube/page.tsx` | YouTube URL form |
| `/episodes/add-from-upload` | `episodes/add-from-upload/page.tsx` | File upload form |
| `/episodes/[id]` | `episodes/[id]/page.tsx` | Episode detail |
| `/subscriptions` | `subscriptions/page.tsx` | Subscriptions landing |
| `/subscriptions/channels` | `subscriptions/channels/page.tsx` | Followed channels |
| `/subscriptions/videos` | `subscriptions/videos/page.tsx` | Discovered videos |
| `/search` | `search/page.tsx` | Advanced search |
| `/settings` | `settings/page.tsx` | Settings page |
| `/activity` | `activity/page.tsx` | Event log |

### Layout Structure

```typescript
// app/layout.tsx (Root Layout)
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              {children}
              <Toaster />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

// Authenticated pages use MainLayout
<MainLayout>
  <Header />
  <div className="flex">
    <SidePanel />
    <main>{children}</main>
  </div>
</MainLayout>
```

---

## Component Organization

### Component Categories

#### 1. UI Components (`components/ui/`)

Base components from ShadCN UI library. These are primitive, reusable components:

```typescript
// Example: Button component
import { Button } from "@/components/ui/button";

<Button variant="default" size="md" onClick={handleClick}>
  Click Me
</Button>
```

**Available Components:**
- Form: `button`, `input`, `textarea`, `select`, `checkbox`, `form`
- Display: `card`, `badge`, `avatar`, `progress`, `skeleton`
- Overlay: `dialog`, `alert-dialog`, `popover`, `dropdown-menu`
- Navigation: `tabs`, `pagination`
- Feedback: `toast`, `sonner`

#### 2. Feature Components (`components/features/`)

Domain-specific components organized by feature:

```typescript
// Example: Episode card
import { EpisodeCard } from "@/components/features/episodes/episode-card";

<EpisodeCard
  episode={episode}
  onPlay={handlePlay}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

#### 3. Layout Components (`components/layout/`)

Application structure components:

```typescript
// Main layout with navigation
<MainLayout>
  <Header />
  <SidePanel />
  <main>{children}</main>
</MainLayout>
```

#### 4. Provider Components (`components/providers/`)

Context providers for global state:

```typescript
// Root providers setup
<ThemeProvider>
  <QueryProvider>
    <AuthProvider>
      {children}
    </AuthProvider>
  </QueryProvider>
</ThemeProvider>
```

---

## State Management

### Server State (React Query)

All server data is managed through React Query with custom hooks:

```typescript
// Query example
export function useEpisodes(channelId: number) {
  return useQuery({
    queryKey: ['episodes', channelId],
    queryFn: () => api.get(`/v1/episodes?channel_id=${channelId}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Mutation example
export function useCreateEpisode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateEpisodeDTO) =>
      api.post('/v1/episodes', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
    },
  });
}
```

### Client State

Minimal client state, primarily for:
- Authentication state (`auth-context.tsx`)
- Theme preference (`theme-provider.tsx`)
- Form state (React Hook Form)

### Query Key Structure

```typescript
// Consistent query key patterns
const queryKeys = {
  episodes: ['episodes'],
  episodesByChannel: (channelId: number) => ['episodes', channelId],
  episode: (id: number) => ['episodes', 'detail', id],
  channels: ['channels'],
  channel: (id: number) => ['channels', id],
  followedChannels: ['followed-channels'],
  youtubeVideos: (channelId?: number) => ['youtube-videos', channelId],
  notifications: ['notifications'],
  unreadCount: ['notifications', 'unread-count'],
  taskStatus: (taskId: string) => ['tasks', taskId],
};
```

---

## Custom Hooks

### Episode Hooks (`use-episodes.ts`)

```typescript
// List episodes
const { data, isLoading, error } = useEpisodes(channelId);

// Create episode
const createMutation = useCreateEpisode();
createMutation.mutate({ channelId, videoUrl, title });

// Upload episode
const uploadMutation = useUploadEpisode();
uploadMutation.mutate({ channelId, file, title, description });

// Delete episode
const deleteMutation = useDeleteEpisode();
deleteMutation.mutate(episodeId);
```

### Followed Channels Hooks (`use-followed-channels.ts`)

```typescript
// List followed channels
const { data } = useFollowedChannels();

// Follow channel
const followMutation = useFollowChannel();
followMutation.mutate({ url, autoApprove });

// Trigger video check
const checkMutation = useTriggerCheck();
checkMutation.mutate(channelId);

// Trigger RSS check (fast)
const rssCheckMutation = useTriggerCheckRss();
rssCheckMutation.mutate(channelId);
```

### YouTube Videos Hooks (`use-youtube-videos.ts`)

```typescript
// List discovered videos
const { data } = useYouTubeVideos({ channelId, state });

// Mark as reviewed
const reviewMutation = useMarkVideoReviewed();

// Discard video
const discardMutation = useDiscardVideo();

// Create episode from video
const createMutation = useCreateEpisodeFromVideo();
createMutation.mutate({ videoId, channelId });
```

### Task Status Hook (`use-task-status.ts`)

```typescript
// Poll task status
const { data: taskStatus, isLoading } = useTaskStatus(taskId, {
  enabled: !!taskId,
  refetchInterval: (data) =>
    data?.status === 'SUCCESS' || data?.status === 'FAILURE'
      ? false
      : 2000, // Poll every 2 seconds while running
});
```

### Notifications Hooks (`use-notifications.ts`)

```typescript
// List notifications
const { data } = useNotifications();

// Unread count
const { data: count } = useUnreadCount();

// Mark as read
const markReadMutation = useMarkNotificationRead();

// Mark all as read
const markAllReadMutation = useMarkAllRead();
```

---

## API Integration

### API Client (`lib/api.ts`)

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

class ApiClient {
  private accessToken: string | null = null;

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      await this.handleError(response);
    }

    return response.json();
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      await this.handleError(response);
    }

    return response.json();
  }

  // ... put, delete methods
}

export const api = new ApiClient();
```

### Error Handling

```typescript
private async handleError(response: Response): Promise<never> {
  const error = await response.json().catch(() => ({}));

  if (response.status === 401) {
    // Attempt token refresh
    const refreshed = await this.refreshToken();
    if (!refreshed) {
      // Redirect to login
      window.location.href = '/login';
    }
    throw new Error('Token refreshed, retry request');
  }

  throw new ApiError(error.detail?.error || 'Request failed', response.status);
}
```

---

## Authentication Flow

### Authentication Context

```typescript
// contexts/auth-context.tsx
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isRefreshing: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      // Validate token and set user
      validateToken(token);
    } else {
      setIsLoading(false);
    }
  }, []);

  // Set up automatic refresh
  useEffect(() => {
    const interval = setInterval(() => {
      const token = localStorage.getItem('accessToken');
      if (token && shouldRefresh(token)) {
        refreshToken();
      }
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post('/v1/auth/login', { email, password });
    localStorage.setItem('accessToken', response.access_token);
    localStorage.setItem('refreshToken', response.refresh_token);
    api.setAccessToken(response.access_token);
    setUser(response.user);
  };

  // ... refreshToken, logout implementations
}
```

### Token Refresh Strategy

1. **Automatic Refresh (48 minutes)** - Background refresh at 80% of token lifetime
2. **Activity-Based Refresh** - Refresh on user activity after 5 minutes idle
3. **On-Demand Refresh** - On 401 errors, attempt refresh before redirect

```typescript
// hooks/use-activity-detection.ts
export function useActivityDetection(onActivity: () => void) {
  useEffect(() => {
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];

    const handleActivity = debounce(() => {
      onActivity();
    }, 5 * 60 * 1000); // 5 minutes debounce

    events.forEach(event => {
      window.addEventListener(event, handleActivity);
    });

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [onActivity]);
}
```

---

## Styling Approach

### TailwindCSS v4

```typescript
// Utility-first approach
<div className="flex items-center gap-4 p-4 bg-card rounded-lg border">
  <Avatar className="h-10 w-10" />
  <div className="flex-1">
    <h3 className="font-medium text-foreground">{title}</h3>
    <p className="text-sm text-muted-foreground">{description}</p>
  </div>
</div>
```

### ShadCN UI Theming

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    /* ... more CSS variables */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode variables */
  }
}
```

### Component Composition

```typescript
// Compose components with cn() utility
import { cn } from "@/lib/utils";

export function EpisodeCard({ episode, className }: Props) {
  return (
    <Card className={cn(
      "hover:shadow-md transition-shadow",
      episode.status === 'failed' && "border-destructive",
      className
    )}>
      {/* content */}
    </Card>
  );
}
```

---

## Key Component Reference

### Episode Card

```typescript
// components/features/episodes/episode-card.tsx
interface EpisodeCardProps {
  episode: Episode;
  onPlay: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function EpisodeCard({ episode, onPlay, onEdit, onDelete }: EpisodeCardProps) {
  return (
    <Card>
      <CardHeader>
        <img src={episode.thumbnail_url} alt={episode.title} />
      </CardHeader>
      <CardContent>
        <h3>{episode.title}</h3>
        <p>{episode.description}</p>
        <div className="flex gap-2">
          {episode.tags.map(tag => (
            <Badge key={tag.id} style={{ backgroundColor: tag.color }}>
              {tag.name}
            </Badge>
          ))}
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onPlay}>Play</Button>
        <Button variant="outline" onClick={onEdit}>Edit</Button>
        <Button variant="destructive" onClick={onDelete}>Delete</Button>
      </CardFooter>
    </Card>
  );
}
```

### File Upload Form

```typescript
// components/features/episodes/upload-episode-form.tsx
export function UploadEpisodeForm() {
  const [file, setFile] = useState<File | null>(null);
  const uploadMutation = useUploadEpisode();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setFile(file);
      // Extract audio metadata
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/mpeg': ['.mp3'],
      'audio/mp4': ['.m4a'],
      'audio/wav': ['.wav'],
      'audio/ogg': ['.ogg'],
      'audio/flac': ['.flac'],
    },
    maxSize: 500 * 1024 * 1024, // 500MB
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <div {...getRootProps()} className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center",
          isDragActive && "border-primary bg-primary/10"
        )}>
          <input {...getInputProps()} />
          {file ? (
            <p>{file.name}</p>
          ) : (
            <p>Drop audio file here or click to browse</p>
          )}
        </div>

        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* More form fields */}

        <Button type="submit" disabled={uploadMutation.isPending}>
          {uploadMutation.isPending ? 'Uploading...' : 'Upload Episode'}
        </Button>
      </form>
    </Form>
  );
}
```

### Notification Bell

```typescript
// components/layout/notification-bell.tsx
export function NotificationBell() {
  const { data: unreadCount } = useUnreadCount();
  const { data: notifications } = useNotifications();
  const markAllRead = useMarkAllRead();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0">
              {unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between p-2">
          <h4 className="font-medium">Notifications</h4>
          <Button variant="ghost" size="sm" onClick={() => markAllRead.mutate()}>
            Mark all read
          </Button>
        </div>
        <DropdownMenuSeparator />
        <ScrollArea className="h-80">
          {notifications?.map(notification => (
            <NotificationItem key={notification.id} notification={notification} />
          ))}
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

**End of Document**
