# Project Structure

This is an analysis of the best way to structure the project as a monorepo with a `Next.js` frontend and a `FastAPI` backend, keeping in mind the specific requirements.

## Monorepo Structure Evaluation

When using a monorepo structure, especially with distinct frontend and backend applications, the primary goals are usually:
- **Simplified Dependency Management:** Managing shared libraries or types.
- **Atomic Commits/PRs:** Changes across frontend and backend can be bundled.
- **Streamlined CI/CD:** Building, testing, and deploying applications together or independently with clear dependencies.
- **Improved Developer Experience:** Easier local setup and cross-project navigation.

**Pros:** 👍

* **Simplicity & Clarity:** Easy to understand structure, clear separation of concerns.
* **Independent Development:** Teams/individuals can work on frontend or backend with minimal overlap.
* **Efficient Backend Packaging:** `uv` provides very fast dependency resolution and installation for the backend.
* **Independent Scaling:** Frontend and backend can be scaled independently in production.
* **Mature Tooling (Frontend) & Modern Tooling (Backend):** Leverages well-established frontend tools and a cutting-edge Python package manager.
* **Straightforward Dockerization:** Each service has its own Dockerfile; `uv` integrates well into this.

**Cons:** 👎

* **Manual Code Sharing:** Sharing code or types (e.g., API interfaces if not using OpenAPI generation) between frontend and backend still requires manual effort or a separate shared local package strategy.
* **Build Orchestration:** No overarching monorepo tool to optimize builds across both `frontend` and `backend` (e.g., only rebuilding what changed at the root level). For the scale of this setup, this is usually not a significant drawback.


## **Dependency Management:**

### **Frontend:** Managed by `package.json` (and a lock file like `package-lock.json` or `yarn.lock`) within the `frontend` directory. Standard `npm install` or `yarn install`.

- `src/` folder: This is the primary location for the Next.js application code, including:
    - `app/` (if using the App Router) or `pages/` (if using the Pages Router).
    - `components/`
    - `lib/` (or `utils/`, `hooks/`, etc.)
    - `styles/`

- Files like `package.json`, `next.config.js`, `tailwind.config.js`, `tsconfig.json`, `Dockerfile`, and the `public/` directory remain at the root of the frontend folder, as they are typically configured to be at this level.

### **Backend (with `uv`):**
- Dependencies are declared in `pyproject.toml` under the `[project.dependencies]` section (and `[project.optional-dependencies]` for development tools if desired).
    - `uv` uses this file to resolve and install packages. You might create a virtual environment using `uv venv` and install dependencies with `uv pip sync pyproject.toml` or `uv pip install -r requirements.txt` if you choose to generate one using `uv pip compile pyproject.toml -o requirements.txt`.
    - `uv` can also manage virtual environments directly.

## **Directory Structure:**

We will have FOUR main folders inside the root project folder: 
- one for the `frontend` application
- and one for the `backend` application
- there will also be another folder `web` with the project's old code that we want to modernize with the new code. This is only for reference and will be removed later.
- lastly, the `project-docs/` will contain all project planning and reference documentation.

You can access full detailed arcchitecure for both the frontend and backend in the following files:
- [Frontend Architecture](./project-frontend-architecture.md)
- [Backend Architecture](./project-backend-architecture.md)

The summarized directory structure will be as follows:

```bash
your-app-name/
├── web/                      # OLD CODE ONLY USED FOR REFERENCE: FLASK APP WITH SQLITE DATABASE - WILL BE REMOVED LATER - DO NOT MODIFY THIS CODE
│   ├── ...                   # ... OLD CODE
├── frontend/                 # Next.js + React + TailwindCSS + ShadCN
│   ├── src/                  # <--- Next.js application code resides here
│   │   ├── app/                # Next.js App Router: Pages/Layouts/Routes. MUST contain route segments, layouts, and page components.
│   │   ├── components/                 # Shared/Reusable UI Components.
│   │   ├── features/                   # Feature-specific logic, hooks, non-global state, services, and components solely used by that feature.
│   │   ├── hooks/                      # Global/sharable custom React Hooks. MUST be generic and usable by multiple features/components.
│   │   ├── lib/ / utils/             # Utility functions, helpers, constants. MUST contain pure functions and constants, no side effects or framework-specific code unless clearly named (e.g., `react-helpers.ts`).
│   │   ├── services/                   # Global API service clients or SDK configurations. MUST define base API client instances and core data fetching/mutation services.
│   │   ├── store/                      # Global state management setup (e.g., Redux store, Zustand store).
│   │   ├── styles/                     # Global styles, theme configurations (if not using `globals.css` or similar, or for specific styling systems like SCSS partials).
│   │   └── types/                      # Global TypeScript type definitions/interfaces. MUST contain types shared across multiple features/modules.
│   │   ├── public/               # Static assets (images, fonts, etc.)
│   │   ├── package.json          # Frontend dependencies and scripts
│   │   ├── next.config.js        # Next.js configuration
│   │   ├── tsconfig.json         # TypeScript configuration for frontend
│   │   ├── tailwind.config.js    # Tailwind CSS configuration
│   │   ├── postcss.config.js     # PostCSS configuration
│   │   ├── Dockerfile            # Frontend Dockerfile
│   │   └── ...                   # Other config files like .eslintrc.json, .prettierrc.json
├── backend/                  # FastAPI + SQLite + SQLModel (using uv)
│   ├── app/
│   │   ├── routers/
│   │   ├── models/
│   │   ├── services/
│   │   ├── main.py
│   │   └── __init__.py
│   ├── tests/
│   ├── pyproject.toml        # For uv (and project metadata)
│   ├── uv.lock               # Lock file generated by uv (optional, but recommended)
│   ├── .env.example
│   ├── Dockerfile            # Backend Dockerfile (using uv)
│   └── ...
├── docker-compose.yml        # For local development and multi-container orchestration
├── .env                      # Environment variables for the project
├── .gitignore                # Git ignore file for the project
└── README.md
```

## Deployment with Docker Compose

We will have individual Dockerfiles for each app for better caching and separation of concerns. Then we will have a `docker-compose.yml` file in the root of the project. 

- `frontend/Dockerfile`: Builds the Next.js application (with multi-stage builds).
- `backend/Dockerfile`: Sets up the Python environment, **installs `uv`**, installs dependencies using `uv`, and runs the FastAPI application.


### Example `docker-compose.yml` file:

Here is an example of a `docker-compose.yml` file that can be used to deploy the project with Docker Compose.

```yaml
# project_folder/docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./apps/frontend # Path to Dockerfile directory
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      # Example: API URL for the frontend to connect to the backend
      # Ensure Next.js app reads this (e.g. process.env.NEXT_PUBLIC_API_URL)
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api # Or http://backend:8000/api if using service name
      # Add other necessary environment variables
    # volumes:
    #   - ./apps/frontend:/app # For development hot-reloading (not for production)
    #   - /app/node_modules # Anonymous volume to prevent host node_modules overwriting container's
    #   - /app/.next # Similar for .next folder
    depends_on:
      - backend # Optional: ensures backend starts before frontend attempts to connect
    restart: unless-stopped
    networks:
      - app-network

  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      # Example: Database URL for SQLite (path within the container)
      - DATABASE_URL=sqlite:///./sql_app.db
      # Add other necessary environment variables
    volumes:
      # Persist SQLite database file
      - backend_db_data:/code # Mount a volume to where your SQLite DB file will live, e.g., /code/sql_app.db
    restart: unless-stopped
    networks:
      - app-network

volumes:
  backend_db_data: # Named volume to persist SQLite data

networks:
  app-network:
    driver: bridge
```

