import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { AuthProvider } from "@/contexts/auth-context";
import { AuthGuard } from "@/components/providers/auth-provider";
import { AudioProvider } from "@/contexts/audio-context";
import { GlobalMediaPlayer } from "@/components/features/media/global-media-player";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LabCastARR - YouTube to Podcast Converter",
  description: "Convert YouTube videos to podcast episodes with RSS feeds",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AuthProvider>
              <AuthGuard>
                <AudioProvider>
                  <div className="min-h-screen bg-background text-foreground">
                    {children}
                  </div>
                  <GlobalMediaPlayer />
                  <SonnerToaster />
                  <Toaster />
                </AudioProvider>
              </AuthGuard>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
