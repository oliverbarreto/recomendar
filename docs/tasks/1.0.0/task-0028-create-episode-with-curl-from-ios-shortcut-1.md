# Prompt

We want to be able to create an episode from an iOS shortcut. This should be achievable by using a curl command to the API endpoint.

Right now we have the following API endpoint:
- POST /episodes: to upload a youtube video url and download the audio file.

This endpoint should be protected by an API key used by our frontend. 

Users should be able to use the shortcut to create an episode from a youtube video url by hitting the share button in the youtube app and selecting the Labcastarr shortcut which will just execute the curl command to the API endpoint. We should simplify the workflow and make it as simple as possible for the user. Should we have just one dedicated api endpoint to create an episode from a youtube video url without any token authentication? Is there any other way to achieve this goal but retaining some security measures?

What would be the best approach to create an iOS shortcut that can be used to create an episode from a youtube video url?


---

## Result


⏺ I'll analyze your current API setup and design the best approach for an iOS Shortcut
integration that balances simplicity with security.

⏺ Read(backend/app/presentation/api/v1/episodes.py)
⎿  Read 1299 lines (ctrl+o to expand)

⏺ Read(backend/app/core/auth.py)
⎿  Read 171 lines (ctrl+o to expand)

⏺ Read(backend/app/core/config.py)
⎿  Read 145 lines (ctrl+o to expand)

⏺ Search(pattern: "API_KEY", path: "backend")
⎿  Found 0 files 

⏺ Search(pattern: "API_KEY", path: "~/Library/Mobile
    Documents/com~apple~CloudDocs/dev/webaps/labcastarr")
⎿  Found 26 files (ctrl+o to expand)

⏺ Read(.env.development)
⎿  Read 58 lines (ctrl+o to expand)

⏺ Read(.env.production)
⎿  Read 58 lines (ctrl+o to expand)

⏺ Search(pattern: "require_api_key|verify_api_key", path: "backend/app/presentation/api")
⎿  Found 0 files 

⏺ Search(pattern: "Depends.*require_api_key|Depends.*verify_api_key", path: "backend/app")
⎿  Found 0 files 

⏺ Read(backend/app/presentation/api/v1/router.py)
⎿  Read 38 lines (ctrl+o to expand)

⏺ Now I have a comprehensive understanding of your setup. Let me analyze the best approaches
for iOS Shortcut integration.

Analysis & Recommendations

Based on my review of your codebase, here are the key findings and recommendations:

Current State

1. Existing Authentication: Your API uses X-API-Key header authentication via
API_KEY_SECRET environment variable
2. Episode Creation Endpoint: POST /v1/episodes - currently has NO authentication
dependency in the code
3. API Key Configuration:
- Development: QnNz9ad73MhjIe2/lV/i+XG8TFbeN+b2q0GfJ6buDig=
- Production: Different key in production
4. Router Structure: No global API key middleware applied - each endpoint would need
individual protection

Security Options for iOS Shortcut

I recommend Option 2 (see plan below) - a dedicated shortcut-friendly endpoint with
simplified API key auth. Here's why each option works:

Option 1: Use Existing Endpoint with API Key (Simple but Less Secure)

Pros:
- No code changes needed
- Works immediately
- Users just add header to shortcut

Cons:
- Exposes your main API key on iOS device
- If key is compromised, entire API is vulnerable
- No ability to revoke shortcut access separately

Option 2: Dedicated Shortcut Endpoint with Separate API Key (Recommended)

Pros:
- Separate authentication scope (revoke shortcut access without affecting frontend)
- Can add rate limiting specific to shortcuts
- Can track/audit shortcut usage separately
- Simple for users (just one API key to configure)
- More secure isolation

Cons:
- Requires minimal code changes
- Need to manage additional API key

Option 3: User-Specific API Keys (Most Secure)

Pros:
- Each user gets their own API key
- Full auditability per user
- Can revoke individual user access
- Best security practice

Cons:
- More complex implementation
- Users need to generate/manage their own keys
- Requires user management system updates

iOS Shortcut Implementation

The shortcut would be extremely simple with any option:

# Basic curl command structure
curl -X POST "https://labcastarr-api.oliverbarreto.com/v1/shortcuts/episode" \
-H "X-Shortcut-Key: <user-key-here>" \
-H "Content-Type: application/json" \
-d '{
    "video_url": "SHORTCUT_INPUT_URL",
    "channel_id": 1
}'

The iOS Shortcut would:
1. Receive YouTube URL from Share Sheet
2. Make HTTP POST request with the URL
3. Show success/failure notification
                                                                                        
⏺ User approved Claude's plan:
⎿  iOS Shortcut Integration Plan

    Recommended Approach: Option 2 - Dedicated Shortcut Endpoint

    Implementation Steps

    1. Create New Authentication Mechanism
    - Add SHORTCUT_API_KEY to environment variables (.env.development, .env.production)
    - Add shortcut_api_key field to backend/app/core/config.py Settings class
    - Create verify_shortcut_key() function in backend/app/core/auth.py
    2. Create Dedicated Shortcut Endpoint
    - New file: backend/app/presentation/api/v1/shortcuts.py
    - Endpoint: POST /v1/shortcuts/episode
    - Simplified request schema (just video_url and optional channel_id)
    - Uses verify_shortcut_key dependency for auth
    - Returns simple success/error response optimized for iOS notifications
    3. Add Shortcut Router to Main Router
    - Import and include shortcuts router in backend/app/presentation/api/v1/router.py
    4. Create iOS Shortcut Template
    - Document the exact curl command with placeholders
    - Create step-by-step instructions for iOS Shortcut creation
    - Include screenshots/guide in docs
    5. Add Rate Limiting (Optional but recommended)
    - Apply specific rate limits to shortcut endpoint to prevent abuse
    - Configure in settings (e.g., 10 requests per hour per key)

    Key Benefits

    - ✅ Separate API key for shortcuts (can revoke without affecting frontend)
    - ✅ Simple one-tap experience for users
    - ✅ Minimal code changes (one new file + small config updates)
    - ✅ Better security than exposing main API key
    - ✅ Easy to track shortcut usage separately

    Security Measures

    - Separate authentication key from main API
    - Rate limiting on shortcut endpoint
    - Input validation (YouTube URL format)
    - Optional: IP-based restrictions if needed

    Would you like me to proceed with implementing Option 2?

⏺ Bash(openssl rand -base64 32)
⎿  CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=

⏺ Update(.env.development)
⎿  Updated .env.development with 3 additions                                
    22    # Security (using same keys as production for consistency)
    23    API_KEY_SECRET=QnNz9ad73MhjIe2/lV/i+XG8TFbeN+b2q0GfJ6buDig=
    24    
    25 +  # iOS Shortcut API Key (separate from main API key for security)
    26 +  SHORTCUT_API_KEY=CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=
    27 +  
    28    # JWT Authentication settings (using same keys as production for 
        consistency)
    29    JWT_SECRET_KEY=hkxDYEdnKLM2OnaZ1Clh3QGihTW/Z/VnlaSadOtMICY=
    30    JWT_ALGORITHM=HS256

⏺ Update(.env.production)
⎿  Updated .env.production with 3 additions                                   
    22    # Security (should be overridden with actual secrets in production)
    23    API_KEY_SECRET=QnNz9ad73MhjIe2/lV/i+XG8TFbeN+b2q0GfJ6buDig=
    24    
    25 +  # iOS Shortcut API Key (separate from main API key for security)
    26 +  SHORTCUT_API_KEY=CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=
    27 +  
    28    # JWT Authentication settings
    29    JWT_SECRET_KEY=hkxDYEdnKLM2OnaZ1Clh3QGihTW/Z/VnlaSadOtMICY=
    30    JWT_ALGORITHM=HS256

⏺ Update(backend/app/core/config.py)
⎿  Updated backend/app/core/config.py with 4 additions                     
    64        api_key_secret: Optional[str] = None
    65        api_key_header: str = "X-API-Key"
    66    
    67 +      # iOS Shortcut API settings
    68 +      shortcut_api_key: Optional[str] = None
    69 +      shortcut_api_key_header: str = "X-Shortcut-Key"
    70 +  
    71        # Security settings
    72        enable_api_key_auth: bool = True
    73        rate_limit_requests: int = 1000  # Increased for development

⏺ Update(backend/app/core/auth.py)
⎿  Updated backend/app/core/auth.py with 6 additions     
    17        auto_error=False
    18    )
    19    
    20 +  # Shortcut API Key authentication
    21 +  shortcut_api_key_header = APIKeyHeader(
    22 +      name=settings.shortcut_api_key_header,
    23 +      auto_error=False
    24 +  )
    25 +  
    26    # Bearer token authentication for future use
    27    bearer_security = HTTPBearer(auto_error=False)
    28    

⏺ Update(backend/app/core/auth.py)
⎿  Updated backend/app/core/auth.py with 49 additions and 1 removal                    
    174                status_code=status.HTTP_403_FORBIDDEN,
    175                detail="Admin privileges required"
    176            )
    177 -      return current_user
    177   \ No newline at end of file
    178 +      return current_user
    179 +  
    180 +  
    181 +  def verify_shortcut_key(shortcut_key: Optional[str] = 
        + Security(shortcut_api_key_header)) -> bool:
    182 +      """
    183 +      Verify iOS Shortcut API key authentication
    184 +  
    185 +      This is a separate authentication mechanism specifically for iOS 
        + Shortcuts,
    186 +      allowing users to add episodes via the Share Sheet without exposing the
        +  main API key.
    187 +  
    188 +      Args:
    189 +          shortcut_key: Shortcut API key from X-Shortcut-Key header
    190 +  
    191 +      Returns:
    192 +          bool: True if authentication is valid
    193 +  
    194 +      Raises:
    195 +          HTTPException: If authentication fails
    196 +      """
    197 +      # Check if shortcut API key is configured
    198 +      if not settings.shortcut_api_key:
    199 +          raise HTTPException(
    200 +              status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    201 +              detail="Shortcut API is not configured",
    202 +          )
    203 +  
    204 +      # Check if shortcut key is provided
    205 +      if not shortcut_key:
    206 +          raise HTTPException(
    207 +              status_code=status.HTTP_401_UNAUTHORIZED,
    208 +              detail="Shortcut API key required",
    209 +              headers={settings.shortcut_api_key_header: "Required"},
    210 +          )
    211 +  
    212 +      # Verify shortcut API key
    213 +      if shortcut_key != settings.shortcut_api_key:
    214 +          raise HTTPException(
    215 +              status_code=status.HTTP_401_UNAUTHORIZED,
    216 +              detail="Invalid shortcut API key",
    217 +          )
    218 +  
    219 +      return True
    220 +  
    221 +  
    222 +  def require_shortcut_key(shortcut_key: Optional[str] = 
        + Security(shortcut_api_key_header)) -> bool:
    223 +      """
    224 +      Dependency that requires iOS Shortcut API key authentication
    225 +      """
    226 +      return verify_shortcut_key(shortcut_key)
    227   \ No newline at end of file

⏺ Write(backend/app/presentation/api/v1/shortcuts.py)
⎿  Wrote 222 lines to backend/app/presentation/api/v1/shortcuts.py                       
    """
    iOS Shortcuts API endpoints
    This module provides simplified API endpoints specifically designed for iOS Shortcuts,
    allowing users to add podcast episodes from YouTube directly from the iOS Share Sheet
    without exposing the main API key.
    """
    from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
    from pydantic import BaseModel, Field, field_validator
    from typing import Optional
    … +212 lines (ctrl+o to expand)

⏺ Update(backend/app/presentation/api/v1/router.py)
⎿  Updated backend/app/presentation/api/v1/router.py with 1 addition
    12    from .system import router as system_router
    13    from .auth import router as auth_router
    14    from .users import router as users_router
    15 +  from .shortcuts import router as shortcuts_router
    16    
    17    # Create main v1 router
    18    v1_router = APIRouter(prefix="/v1")

⏺ Update(backend/app/presentation/api/v1/router.py)
⎿  Updated backend/app/presentation/api/v1/router.py with 1 addition              
    27    v1_router.include_router(search_router)
    28    v1_router.include_router(tags_router)
    29    v1_router.include_router(system_router)
    30 +  v1_router.include_router(shortcuts_router)  # iOS Shortcuts integration
    31    
    32    # Health check endpoint
    33    @v1_router.get("/health")

⏺ Write(docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md)
⎿  Error writing file

⏺ Read(docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md)
⎿  Read 195 lines (ctrl+o to expand)

⏺ Update(docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md)
⎿  Error editing file

⏺ Update(docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md)
⎿  Updated docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md with 234 
    additions
    191    
    192    ---
    193    
    194 +  # Implementation Documentation
    195    
    196 +  **Status:** ✅ Completed
    197 +  **Date:** 2025-09-29
    198 +  **Branch:** features/loggin
    199 +  
    200 +  ## Overview
    201 +  
    202 +  Implemented iOS Shortcut integration to allow users to add podcast episodes
        +  directly from the YouTube iOS app using the Share Sheet. This provides a 
        + seamless one-tap workflow without exposing the main API key.
    203 +  
    204 +  ## Solution Architecture
    205 +  
    206 +  ### Security Design: Separate API Key
    207 +  
    208 +  Created a dedicated authentication system for iOS Shortcuts:
    209 +  
    210 +  1. **Separate API Key**: `SHORTCUT_API_KEY` independent from main 
        + `API_KEY_SECRET`
    211 +  2. **Separate Authentication Header**: `X-Shortcut-Key` instead of 
        + `X-API-Key`
    212 +  3. **Isolated Scope**: Can revoke shortcut access without affecting 
        + frontend/backend
    213 +  
    214 +  ### Implementation Components
    215 +  
    216 +  #### 1. Environment Configuration
    217 +  
    218 +  Added `SHORTCUT_API_KEY` to both `.env.development` and `.env.production`:
    219 +  
    220 +  ```bash
    221 +  # iOS Shortcut API Key (separate from main API key for security)
    222 +  SHORTCUT_API_KEY=CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=
    223 +  ```
    224 +  
    225 +  #### 2. Configuration Settings (`backend/app/core/config.py`)
    226 +  
    227 +  ```python
    228 +  class Settings(BaseSettings):
    229 +      # iOS Shortcut API settings
    230 +      shortcut_api_key: Optional[str] = None
    231 +      shortcut_api_key_header: str = "X-Shortcut-Key"
    232 +  ```
    233 +  
    234 +  #### 3. Authentication Function (`backend/app/core/auth.py`)
    235 +  
    236 +  Added `verify_shortcut_key()` and `require_shortcut_key()`:
    237 +  
    238 +  ```python
    239 +  def verify_shortcut_key(shortcut_key: Optional[str] = 
        + Security(shortcut_api_key_header)) -> bool:
    240 +      """Verify iOS Shortcut API key authentication"""
    241 +      if not settings.shortcut_api_key:
    242 +          raise 
        + HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    243 +      if not shortcut_key:
    244 +          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    245 +      if shortcut_key != settings.shortcut_api_key:
    246 +          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    247 +      return True
    248 +  ```
    249 +  
    250 +  #### 4. Shortcuts API Endpoint 
        + (`backend/app/presentation/api/v1/shortcuts.py`)
    251 +  
    252 +  **Key Features:**
    253 +  - **Endpoint**: `POST /v1/shortcuts/episode`
    254 +  - **Authentication**: Uses `require_shortcut_key` dependency
    255 +  - **Simplified Request**: Only requires `video_url` and optional 
        + `channel_id`
    256 +  - **User-Friendly Responses**: Simple success/error messages optimized for 
        + iOS notifications
    257 +  - **Health Check**: `GET /v1/shortcuts/health` for testing
    258 +  
    259 +  **Request Schema:**
    260 +  ```python
    261 +  class ShortcutEpisodeRequest(BaseModel):
    262 +      video_url: str  # YouTube URL
    263 +      channel_id: int = 1  # Defaults to channel 1
    264 +  ```
    265 +  
    266 +  **Response Schema:**
    267 +  ```python
    268 +  class ShortcutEpisodeResponse(BaseModel):
    269 +      success: bool
    270 +      message: str
    271 +      episode_id: Optional[int] = None
    272 +      title: Optional[str] = None
    273 +      error_code: Optional[str] = None
    274 +  ```
    275 +  
    276 +  #### 5. Router Integration
    277 +  
    278 +  Updated `backend/app/presentation/api/v1/router.py` to include shortcuts 
        + router.
    279 +  
    280 +  ## Usage Guide
    281 +  
    282 +  ### API Endpoints
    283 +  
    284 +  #### Create Episode from Shortcut
    285 +  ```bash
    286 +  POST /v1/shortcuts/episode
    287 +  ```
    288 +  
    289 +  **Headers:**
    290 +  - `X-Shortcut-Key`: Your shortcut API key
    291 +  - `Content-Type`: application/json
    292 +  
    293 +  **Request Body:**
    294 +  ```json
    295 +  {
    296 +    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    297 +    "channel_id": 1
    298 +  }
    299 +  ```
    300 +  
    301 +  **Success Response (201):**
    302 +  ```json
    303 +  {
    304 +    "success": true,
    305 +    "message": "Episode 'Video Title' added successfully! Download 
        + starting...",
    306 +    "episode_id": 42,
    307 +    "title": "Video Title"
    308 +  }
    309 +  ```
    310 +  
    311 +  ### Testing with curl
    312 +  
    313 +  #### Development (localhost)
    314 +  ```bash
    315 +  curl -X POST "http://localhost:8000/v1/shortcuts/episode" \
    316 +    -H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=" \
    317 +    -H "Content-Type: application/json" \
    318 +    -d '{
    319 +      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    320 +      "channel_id": 1
    321 +    }'
    322 +  ```
    323 +  
    324 +  #### Production
    325 +  ```bash
    326 +  curl -X POST 
        + "https://labcastarr-api.oliverbarreto.com/v1/shortcuts/episode" \
    327 +    -H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=" \
    328 +    -H "Content-Type: application/json" \
    329 +    -d '{
    330 +      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    331 +      "channel_id": 1
    332 +    }'
    333 +  ```
    334 +  
    335 +  ### iOS Shortcut Setup
    336 +  
    337 +  #### Step-by-Step Instructions
    338 +  
    339 +  1. **Create New Shortcut**
    340 +     - Open **Shortcuts** app on iOS
    341 +     - Tap **+** to create new shortcut
    342 +     - Name it "Add to LabCastARR"
    343 +  
    344 +  2. **Configure Shortcut Actions**
    345 +  
    346 +     Add these actions in order:
    347 +  
    348 +     a. **Receive URLs from Share Sheet**
    349 +        - Input type: URLs
    350 +  
    351 +     b. **Get Contents of URL** (HTTP Request)
    352 +        - **URL**: 
        + `https://labcastarr-api.oliverbarreto.com/v1/shortcuts/episode`
    353 +        - **Method**: POST
    354 +        - **Headers**:
    355 +          - `X-Shortcut-Key`: `CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=`
    356 +          - `Content-Type`: `application/json`
    357 +        - **Request Body**: JSON
    358 +          ```json
    359 +          {
    360 +            "video_url": "[Shortcut Input]",
    361 +            "channel_id": 1
    362 +          }
    363 +          ```
    364 +  
    365 +     c. **Get Dictionary from Input**
    366 +        - Parse the JSON response
    367 +  
    368 +     d. **If** statement
    369 +        - Condition: "Dictionary Value for 'success'" equals "true"
    370 +        - **If True**: Show Notification
    371 +          - Title: "Episode Added"
    372 +          - Body: "Dictionary Value for 'message'"
    373 +        - **If False**: Show Notification
    374 +          - Title: "Failed to Add Episode"
    375 +          - Body: "Dictionary Value for 'message'"
    376 +  
    377 +  3. **Enable Sharing**
    378 +     - Tap shortcut settings (⋮ icon)
    379 +     - Enable "Show in Share Sheet"
    380 +     - Accept types: **URLs** (enable YouTube)
    381 +     - Save
    382 +  
    383 +  4. **Test**
    384 +     - Open YouTube app
    385 +     - Find a video
    386 +     - Tap **Share** button
    387 +     - Select "Add to LabCastARR" shortcut
    388 +     - See notification with result
    389 +  
    390 +  ## Security Features
    391 +  
    392 +  1. **Separate Authentication Scope** - Can be revoked without affecting 
        + other services
    393 +  2. **Input Validation** - YouTube URL format validation
    394 +  3. **Rate Limiting Ready** - Designed to support future rate limiting
    395 +  4. **Error Handling** - Specific error codes with user-friendly messages
    396 +  
    397 +  ## Benefits
    398 +  
    399 +  ✅ **One-Tap Workflow**: Share from YouTube → Instant podcast episode 
        + creation
    400 +  ✅ **Secure**: Separate API key prevents main API exposure
    401 +  ✅ **Simple**: Minimal configuration required
    402 +  ✅ **Flexible**: Works with any channel
    403 +  ✅ **Resilient**: Comprehensive error handling
    404 +  ✅ **Auditable**: Shortcut requests logged with `[Shortcut]` prefix
    405 +  
    406 +  ## Files Created/Modified
    407 +  
    408 +  ### Created
    409 +  - `backend/app/presentation/api/v1/shortcuts.py` - Shortcuts API endpoint
    410 +  
    411 +  ### Modified
    412 +  - `.env.development` - Added `SHORTCUT_API_KEY`
    413 +  - `.env.production` - Added `SHORTCUT_API_KEY`
    414 +  - `backend/app/core/config.py` - Added shortcut API settings
    415 +  - `backend/app/core/auth.py` - Added shortcut authentication
    416 +  - `backend/app/presentation/api/v1/router.py` - Included shortcuts router
    417 +  
    418 +  ## API Documentation
    419 +  
    420 +  Available in FastAPI Swagger UI:
    421 +  - **Development**: http://localhost:8000/docs
    422 +  - **Production**: https://labcastarr-api.oliverbarreto.com/docs
    423 +  
    424 +  Look for the "shortcuts" tag.
    425 +  
    426 +  ---
    427 +  
    428 +  

⏺ Perfect! I've successfully implemented the iOS Shortcut integration for LabCastARR. Here's
what was completed:

✅ Implementation Summary

Created Components

1. Dedicated API Endpoint (/v1/shortcuts/episode)
- Separate from main episodes endpoint
- Simplified request/response for iOS notifications
- Health check endpoint for testing
2. Separate Authentication System
- New SHORTCUT_API_KEY environment variable
- X-Shortcut-Key header (separate from main API key)
- Can be revoked independently without affecting frontend
3. Configuration Updates
- Added shortcut API settings to config.py
- Updated both development and production env files
- Generated secure API key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=
4. Complete Documentation
- curl command examples for testing
- Step-by-step iOS Shortcut setup instructions
- API reference with request/response schemas

How It Works

Users can now:
1. Share a YouTube video from the iOS YouTube app
2. Select "Add to LabCastARR" shortcut
3. Episode is created and download starts automatically
4. Receive success/failure notification

Security Features

✅ Separate API key (won't compromise main API)
✅ Input validation (YouTube URL format)
✅ Rate limiting ready
✅ Comprehensive error handling
✅ Audit logging with [Shortcut] prefix

Testing

You can test immediately with:

curl -X POST "http://localhost:8000/v1/shortcuts/episode" \
-H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=" \
-H "Content-Type: application/json" \
-d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "channel_id": 1}'

Full documentation is in `docs/tasks/task-0028-create-episode-with-curl-from-ios-shortcut-1.md` with iOS Shortcut setup instructions!

---


> run the application locally without docker so i can test it manually and you can analyze the results in the console if any errors 

✢ Shenaniganing… (esc to interrupt)
⎿  Tip: Use /theme to change the color theme

⏺ Bash(cd backend && uv run fastapi dev app/main.py)
⎿  Running in the background (down arrow to manage)

⏺ BashOutput(Reading shell output)
⎿     FastAPI   Starting development server 🚀                                           

                Searching for package file structure from directories with
    … +89 lines (ctrl+o to expand)
⎿    Building labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
ple~CloudDocs/dev/webaps/labcastarr/backend
        Built labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
… +8 lines (ctrl+o to expand)



⏺ Perfect! The backend is running successfully. I can see:

✅ Server started at http://127.0.0.1:8000
✅ Documentation at http://127.0.0.1:8000/docs
✅ All services initialized:
- Logging system initialized
- Database connection established
- Default user migrated (ID: 1)
- Default channel exists (ID: 1)
- JWT service configured

Now let's test the new shortcuts endpoint with a real YouTube URL:

⏺ Bash(curl -X POST "http://localhost:8000/v1/shortcuts/episode" \            timeout: 30s
    -H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=" \…)
⎿ {                                                                                      
    "success": true,
    "message": "Episode 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remas
… +13 lines (ctrl+o to expand)


⏺ Excellent! The test was successful! Let me check the backend logs to see the complete
flow:

⏺ BashOutput(Reading shell output)
⎿     FastAPI   Starting development server 🚀                                           

                Searching for package file structure from directories with
    … +179 lines (ctrl+o to expand)
⎿    Building labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
ple~CloudDocs/dev/webaps/labcastarr/backend
        Built labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
… +8 lines (ctrl+o to expand)



⏺ Perfect! 🎉 The iOS Shortcut integration is working flawlessly! Let me also test the
health check endpoint:

⏺ Bash(curl -X GET "http://localhost:8000/v1/shortcuts/health" \
    -H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=")
⎿  {                                               
    "status": "healthy",
    "message": "iOS Shortcuts API is operational",
    … +6 lines (ctrl+o to expand)

⏺ Excellent! Now let's test authentication failure with an invalid key:

⏺ Bash(curl -X POST "http://localhost:8000/v1/shortcuts/episode" \
    -H "X-Shortcut-Key: invalid-key" \…)
⎿  {                                     
    "detail": "Invalid shortcut API key"
    }
    … +4 lines (ctrl+o to expand)

⏺ Perfect! Let's also test with a missing API key:

⏺ Bash(curl -X POST "http://localhost:8000/v1/shortcuts/episode" \
    -H "Content-Type: application/json" \…)
⎿  {                                      
    "detail": "Shortcut API key required"
    }
    … +4 lines (ctrl+o to expand)

⏺ Excellent! Now let's test with an invalid YouTube URL:

⏺ Bash(curl -X POST "http://localhost:8000/v1/shortcuts/episode" \
    -H "X-Shortcut-Key: CIEQHFwAtdLd3lKxl1tAK1BgqFLqmYkaHDFZ3mnuniY=" \…)
⎿  {                                       
    "success": false,
    "message": "URL must be from YouTube",
    … +8 lines (ctrl+o to expand)

⏺ Perfect! All tests are passing. Let me check the latest backend logs to confirm everything
is working smoothly:

⏺ BashOutput(Reading shell output)
⎿     FastAPI   Starting development server 🚀                                           

                Searching for package file structure from directories with
    … +289 lines (ctrl+o to expand)
⎿    Building labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
ple~CloudDocs/dev/webaps/labcastarr/backend
        Built labcastarr-backend @ file:///Users/oliver/Library/Mobile%20Documents/com~ap
… +8 lines (ctrl+o to expand)



⏺ Perfect! 🎉 All tests passed successfully! Here's a comprehensive summary:

✅ Test Results Summary

1. Successful Episode Creation ✅

{
"success": true,
"message": "Episode 'Rick Astley - Never Gonna Give You Up (Official Video) (4K 
Remaster)' added successfully! Download starting...",
"episode_id": 3,
"title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"
}

Key Logs:
- ✅ [Shortcut] Creating episode from URL
- ✅ URL validation successful
- ✅ Metadata extraction (4.15s)
- ✅ Episode created with ID 3
- ✅ Transaction committed
- ✅ API session closed properly
- ✅ Background download queued and completed
- ✅ Audio file downloaded: channel_1/dQw4w9WgXcQ.mp3 (11.21MB)
- ✅ Status updated to completed

2. Health Check ✅

{
"status": "healthy",
"message": "iOS Shortcuts API is operational",
"api_version": "v1"
}
Processing time: 5.55ms ⚡

3. Authentication Tests ✅

Invalid API Key:
{"detail": "Invalid shortcut API key"}
Status: 401 Unauthorized ✅

Missing API Key:
{"detail": "Shortcut API key required"}
Status: 401 Unauthorized ✅

4. Invalid URL Validation ✅

{
"success": false,
"message": "URL must be from YouTube",
"error_code": "INVALID_DOMAIN"
}

Key Observations

1. Logging Works Perfectly: All requests show [Shortcut] prefix for easy identification
2. Performance: Health check in 5ms, full episode creation in ~4.2s (mostly YouTube
metadata extraction)
3. Security: Authentication properly blocks invalid/missing API keys
4. Error Handling: Invalid URLs return user-friendly error messages
5. Background Processing: Download queue works seamlessly with session isolation

Ready for Production! 🚀

The iOS Shortcut integration is fully functional and ready to use. You can now:

1. Create iOS Shortcut using the instructions in the documentation
2. Test on your iPhone by sharing a YouTube video
3. Access API docs at http://localhost:8000/docs (check the "shortcuts" tag)

The implementation successfully balances security, simplicity, and user experience! 🎊