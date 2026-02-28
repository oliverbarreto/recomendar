# Tech Stack

## Prompt used to generate this file
```markdown
Here is an example table with a technology stack, please create tables with the current project tech stack, one for the frontend, and another one for the backend

## Definitive Tech Stack Selections

{ This section outlines the definitive technology choices for the project. These selections should be made after a thorough understanding of the project's requirements, components, data models, and core workflows. The Architect Agent should guide the user through these decisions, ensuring each choice is justified and recorded accurately in the table below.

This table is the **single source of truth** for all technology selections. Other architecture documents (e.g., Frontend Architecture) must refer to these choices and elaborate on their specific application rather than re-defining them.

Key decisions to discuss and finalize here, which will then be expanded upon and formally documented in the detailed stack table below, include considerations such as:

- Preferred Starter Template Frontend: { Url to template or starter, if used }
- Preferred Starter Template Backend: { Url to template or starter, if used }
- Primary Language(s) & Version(s): {e.g., TypeScript 5.x, Python 3.11 - Specify exact versions, e.g., `5.2.3`}
- Primary Runtime(s) & Version(s): {e.g., Node.js 22.x - Specify exact versions, e.g., `22.0.1`}

Must be definitive selections; do not list open-ended choices (e.g., for web scraping, pick one tool, not two). Specify exact versions (e.g., `18.2.0`). If 'Latest' is used, it implies the latest stable version _at the time of this document's last update_, and the specific version (e.g., `xyz-library@2.3.4`) should be recorded. Pinning versions is strongly preferred to avoid unexpected breaking changes for the AI agent. }

| Category             | Technology              | Version / Details | Description / Purpose                   | Justification (Optional) |
| :------------------- | :---------------------- | :---------------- | :-------------------------------------- | :----------------------- |
| **Languages**        | {e.g., TypeScript}      | {e.g., 5.x}       | {Primary language for backend/frontend} | {Why this language?}     |
|                      | {e.g., Python}          | {e.g., 3.11}      | {Used for data processing, ML}          | {...}                    |
| **Runtime**          | {e.g., Node.js}         | {e.g., 22.x}      | {Server-side execution environment}     | {...}                    |
| **Frameworks**       | {e.g., NestJS}          | {e.g., 10.x}      | {Backend API framework}                 | {Why this framework?}    |
|                      | {e.g., React}           | {e.g., 18.x}      | {Frontend UI library}                   | {...}                    |
| **Databases**        | {e.g., PostgreSQL}      | {e.g., 15}        | {Primary relational data store}         | {...}                    |
|                      | {e.g., Redis}           | {e.g., 7.x}       | {Caching, session storage}              | {...}                    |
| **Cloud Platform**   | {e.g., AWS}             | {N/A}             | {Primary cloud provider}                | {...}                    |
| **Cloud Services**   | {e.g., AWS Lambda}      | {N/A}             | {Serverless compute}                    | {...}                    |
|                      | {e.g., AWS S3}          | {N/A}             | {Object storage for assets/state}       | {...}                    |
|                      | {e.g., AWS EventBridge} | {N/A}             | {Event bus / scheduled tasks}           | {...}                    |
| **Infrastructure**   | {e.g., AWS CDK}         | {e.g., Latest}    | {Infrastructure as Code tool}           | {...}                    |
|                      | {e.g., Docker}          | {e.g., Latest}    | {Containerization}                      | {...}                    |
| **UI Libraries**     | {e.g., Material UI}     | {e.g., 5.x}       | {React component library}               | {...}                    |
| **State Management** | {e.g., Redux Toolkit}   | {e.g., Latest}    | {Frontend state management}             | {...}                    |
| **Testing**          | {e.g., Jest}            | {e.g., Latest}    | {Unit/Integration testing framework}    | {...}                    |
|                      | {e.g., Playwright}      | {e.g., Latest}    | {End-to-end testing framework}          | {...}                    |
| **CI/CD**            | {e.g., GitHub Actions}  | {N/A}             | {Continuous Integration/Deployment}     | {...}                    |
| **Other Tools**      | {e.g., LangChain.js}    | {e.g., Latest}    | {LLM interaction library}               | {...}                    |
|                      | {e.g., Cheerio}         | {e.g., Latest}    | {HTML parsing/scraping}                 | {...}                    |
```

---

## Tech Stack Selections

Okay, I will create the technology stack tables based on our discussions and decisions for both the frontend and backend of your project.

Since we're building from scratch (or close to it) and aiming for modern stacks:

- **Preferred Starter Template Frontend:** None explicitly chosen, will use `create-next-app`.
- **Preferred Starter Template Backend:** None explicitly chosen, will build from a basic FastAPI setup.
- **Primary Language(s) & Version(s):**
    - Frontend: TypeScript (latest stable with Next.js 15, e.g., ~5.3.x or as per `create-next-app`)
    - Backend: Python (latest stable 3.11.x or 3.12.x, e.g., `3.11.8`)
- **Primary Runtime(s) & Version(s):**
    - Frontend: Node.js (latest LTS, e.g., `20.11.1` or `22.x` if stable and supported by Next.js 15)

Here are the detailed tech stack tables:

## Definitive Tech Stack Selections

This section outlines the definitive technology choices for the project. These selections have been made after a thorough understanding of the project's requirements, components, data models, and core workflows.

This table is the **single source of truth** for all technology selections. Other architecture documents must refer to these choices and elaborate on their specific application rather than re-defining them.

---

### Frontend Technology Stack

| Category             | Technology                | Version / Details                     | Description / Purpose                                 | Justification                                                                                                |
| :------------------- | :------------------------ | :------------------------------------ | :---------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Languages**        | TypeScript                | ~5.3.x (or latest via Next.js 15)     | Primary language for frontend development.            | Strong typing, improved developer experience, better code maintainability. Standard for modern Next.js.     |
| **Runtime**          | Node.js                   | LTS (e.g., 20.11.1 or latest stable)  | JavaScript runtime for building and developing Next.js. | Required for Next.js. LTS for stability.                                                                   |
| **Frameworks**       | Next.js                   | 15.x (App Router)                     | React framework for server-side rendering, static site generation, routing, etc. | Modern, performant, excellent DX, App Router for new features.                                             |
|                      | React                     | 19.x (or as per Next.js 15)           | Core UI library.                                      | Bundled with Next.js, industry standard for component-based UI.                                              |
| **UI Libraries**     | Tailwind CSS              | ~3.4.x                                | Utility-first CSS framework.                          | Rapid UI development, highly customizable, consistent styling.                                               |
|                      | Shadcn/ui (Recommended)   | Latest                                | Collection of re-usable components built with Radix UI and Tailwind CSS. | Accelerates UI development, accessible, stylable. User can choose this or build custom components.         |
|                      | Framer Motion (Optional)  | Latest                                | Animation library for React.                          | For creating smooth and modern UI animations as requested.                                                   |
| **State Management** | React Context API         | Bundled with React                    | For simple global state (e.g., auth state).           | Built-in, sufficient for simpler state needs.                                                                |
|                      | Zustand / Jotai (Optional)| Latest                                | Lightweight state management libraries.               | For more complex client-side state if Context API becomes cumbersome.                                        |
| **Forms**            | React Hook Form (Recommended) | Latest                                | Performant, flexible, and extensible forms with easy-to-use validation. | Manages form state and validation efficiently.                                                               |
|                      | Zod                       | Latest                                | TypeScript-first schema declaration and validation.     | For client-side (and potentially shared backend) data validation. Pairs well with React Hook Form.         |
| **API Communication**| Fetch API (Browser)       | N/A                                   | Native browser API for making HTTP requests.          | Built-in, no extra dependencies for basic API calls.                                                         |
|                      | `EventSource` API (Browser)| N/A                                   | Native browser API for Server-Sent Events.            | For real-time status updates from the backend.                                                               |
| **Testing**          | Jest (Recommended)        | Latest                                | JavaScript testing framework.                         | For unit and integration tests of components and utilities. Often configured with Next.js.                   |
|                      | React Testing Library     | Latest                                | Testing utilities for React components.               | Encourages testing components in a user-centric way.                                                         |
|                      | Playwright (Recommended)  | Latest                                | End-to-end testing framework.                         | For testing complete user flows across the application.                                                      |
| **Linting/Formatting**| ESLint                    | Latest                                | Pluggable JavaScript linter.                          | Code quality and consistency. Included with `create-next-app`.                                             |
|                      | Prettier                  | Latest                                | Opinionated code formatter.                           | Consistent code style.                                                                                       |
| **Build Tool**       | Next.js CLI / Webpack/SWC | Bundled                               | Handles building, bundling, and optimization.         | Integrated into Next.js.                                                                                     |
| **Containerization** | Docker                    | Latest                                | For creating a consistent deployment environment.     | Standard for containerizing applications.                                                                    |

---

### Backend Technology Stack

| Category             | Technology                | Version / Details                | Description / Purpose                                      | Justification                                                                                                |
| :------------------- | :------------------------ | :------------------------------- | :--------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Languages**        | Python                    | 3.11.8 (or latest 3.11.x/3.12.x) | Primary language for backend API development.              | Mature, extensive libraries, strong AI/ML ecosystem, excellent for web backends with FastAPI.                |
| **Frameworks**       | FastAPI                   | Latest (e.g., 0.110.x)           | Modern, fast (high-performance) web framework for building APIs. | High performance, async support, automatic data validation & serialization (Pydantic), great DX.             |
| **Databases**        | SQLite                    | Bundled with Python              | File-based relational database.                              | Simple setup, sufficient for homelab/few users, good async support with `aiosqlite`.                         |
| **ORM / DB Driver**  | SQLModel                  | Latest                           | Python ORM that combines Pydantic and SQLAlchemy.          | Modern, reduces boilerplate, excellent type safety, integrates perfectly with FastAPI, async-first.          |
|                      | `aiosqlite`               | Latest                           | Async SQLite driver for Python.                            | Required for async operations with SQLite.                                                                   |
| **Migrations**       | Alembic                   | Latest                           | Database migration tool for SQLAlchemy (and thus SQLModel). | Robust schema migration management.                                                                          |
| **Data Validation**  | Pydantic                  | Bundled with FastAPI/SQLModel    | Data validation and settings management using Python type hints. | Core to FastAPI and SQLModel for request/response validation and data structuring.                         |
| **Async Server**     | Uvicorn                   | Latest                           | ASGI server for FastAPI.                                   | High-performance ASGI server, standard for FastAPI.                                                          |
| **YouTube Processing**| `yt-dlp`                  | Latest                           | Command-line program to download videos/audio from YouTube & other sites. | Powerful, actively maintained, feature-rich for metadata and audio extraction. Used via `asyncio.subprocess`. |
| **Transcript**       | `youtube-transcript-api`  | Latest                           | Python API to fetch YouTube transcripts.                   | Simple, direct way to get YouTube-generated transcripts.                                                     |
| **Podcast Generation**| `podgen`                  | Latest                           | Python library for generating podcast RSS feeds.             | Specifically designed for creating podcast feeds, familiar from the old app.                                 |
| **Background Tasks** | FastAPI `BackgroundTasks` | Bundled with FastAPI             | For running operations after returning a response.         | Simple way to offload non-blocking tasks like YouTube processing.                                            |
| **Real-time (Backend)**| `sse-starlette`           | Latest                           | Server-Sent Events (SSE) utilities for Starlette/FastAPI.  | To push real-time processing status updates to the frontend.                                                 |
| **Testing**          | Pytest                    | Latest                           | Python testing framework.                                  | Powerful and flexible for unit and integration tests.                                                        |
|                      | `httpx`                   | Latest                           | Async HTTP client for Python (for testing FastAPI).        | For making async requests to the API during tests.                                                           |
| **Linting/Formatting**| Ruff (Recommended)        | Latest                           | Extremely fast Python linter and formatter (can replace Black, Flake8, isort). | Speed, comprehensive checks, auto-fixing.                                                                    |
|                      | Black (Alternative)       | Latest                           | Opinionated Python code formatter.                         | Ensures consistent code style if Ruff is not chosen for formatting.                                          |
| **Dependency Mgt.**  | Poetry (Recommended)      | Latest                           | Tool for dependency management and packaging in Python.    | Modern, robust dependency resolution and virtual environment management.                                     |
| **Containerization** | Docker                    | Latest                           | For creating a consistent deployment environment.          | Standard for containerizing applications.                                                                    |

This provides a definitive list for the project. The "Version / Details" column aims for specific versions where possible, or indicates "Latest" with an example if the exact version will be determined upon project initialization (but should then be pinned).
