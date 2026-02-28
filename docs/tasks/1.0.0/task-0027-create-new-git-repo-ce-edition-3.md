# Prompt

We want to remove the personal information from the project codebase.

For example, in the file `frontend/next.config.ts`, we have the following code:
```typescript
import type { NextConfig } from "next";

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
    'labcastarr.oliverbarreto.com',
    'localhost:3000',
    '127.0.0.1:3000'
  ],
};

export default nextConfig;
```

As you can see, this file contains referecne to a personal domain `labcastarr.oliverbarreto.com`. This is a personal domain that i use for my own testing. I think that we can use already present environment variables in `.env.production` to fix this issue:

```
# Production Domain Configuration
DOMAIN=oliverbarreto.com
BASE_URL=https://labcastarr-api.oliverbarreto.com
BACKEND_URL=https://labcastarr-api.oliverbarreto.com
FRONTEND_URL=https://labcastarr.oliverbarreto.com
```

Is there any other way that i can remove this reference for example using a environment variable instead that is not hardcoded ?

I want you to analyze this as the first step. Do not analyze the whole codebase yet, do not analyze the other files yet, just analyze how to fix this issue with the file.


---

## Result
