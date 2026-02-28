As a senior software engineer and senior architect, I need you to think to analyze how to create a new project structure for the application we want to build. 

The project structure should be:

```
/LabCastARR
  /docs (documentation folder)
  /web (old monolithic flask app for reference)
  /backend
    /api
      ...
    Dockerfile
    pyproject.toml
  /frontend
    /src
      ...
    next.config.js
    package.json
    Dockerfile
  .env
  .env.example
  docker-compose.yml
  README.md
```

## Goals:
1. First, I want you to create the initialize the FastAPI project using uv for dependencies management in the `backend` folder. Follow the instructions in the file @docs/reference/backend-uv-fastapi-installation.md

2. Then, I want you to create the initialize the Next.js with ShadCN and TailwindCSS project with the following structure in the `frontend` folder. Follow the instructions in the file @docs/reference/frontend-create-nextjs-shadcn-app.md    

3. Third, I want you to edit the `docker-compose.yml` file in the root folder to run the application using Docker and Docker Compose. Both frontend and backend should be able to run using Docker Compose at project root level.

4. Fourth, I want you to create the `.env.example` and `.env` files in the root folder to describe the environment variables for the frontend and backend to run the application.

5. Fifth, I want you to create the `README.md` file in the root folder to describe the application.


