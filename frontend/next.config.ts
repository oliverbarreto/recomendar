import type { NextConfig } from "next";

// Extract domain from FRONTEND_URL if available
const frontendDomain = process.env.FRONTEND_URL
  ? new URL(process.env.FRONTEND_URL).host
  : undefined;

const nextConfig: NextConfig = {
  eslint: {
    // Allow production builds to complete even if there are ESLint errors
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow production builds to complete even if there are TypeScript errors
    ignoreBuildErrors: true,
  },
  // Fix CORS warning for dev origins
  allowedDevOrigins: [
    frontendDomain,
    'localhost:3000',
    '127.0.0.1:3000'
  ].filter(Boolean) as string[],
};

export default nextConfig;
