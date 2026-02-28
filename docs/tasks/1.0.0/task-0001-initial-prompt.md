As a senior software engineer and senior architect, I need you to thouroughly analyze how to implement
the new architecture and features described in the requirements defined in the initial PRD document @docs/specs/prd-v1.md

The project structure is already created. We already created `backend` and `frontend` folders with a working initial version of the frontend and backend using docker compose. The `web` folder is only for reference for the old Flask monolith and will be removed later.

IMPORTANT NOTE: This `web` folder should not be used as a reference for the new architecture. Also, the file @web/CLAUDE.md was created for the old Flask Project so it should not be used as a reference for the new architecture.

## Goals:
1. First, I want you to read the file @docs/specs/prd-v1.md and fully understand the requirements and objectives of the app.

2. Second, with your strong technical expertise, I need you to ultra think to analyze and draft a very detailed implementation plan that will be used to create the implementation plan document for the project (@docs/specs/implementation-plan-v1.md). This document should contain the analysis and design of the new architecture with the following sections:

  **TABLE OF CONTENTS:**
  - Project overview and objectives 
  - Technology Stack (two different tables with the technology stack for both frontend and backend, with the version of the technology)
  - Architecture and System Design Structure (follow clean architecture principles in a practical way, balancing theory with pragmatism, and not over-engineering the solution)
    - frontend
    - backend
  - Core features and functionality (for both frontend and backend)
  - Functional and Non-Functional Requirements (for both frontend and backend)
  - Models and Relationships (for both frontend and backend)
  - Component Architecture (for frontend)
  - UI design definition and structure (for frontend)
  - Project Phases/Milestones (for both frontend and backend - Propose an implementation plan with phases and milestones for the project according to your best architecture design and criteria. The first phase of the project will be to create the project structure and make working initial version of the frontend and backend using docker compose. Then we will start building the new architecture.)
  - Deployment (for both frontend and backend)

3. Third, create a new file called `docs/specs/implementation-plan-v1.md` with the result of the analysis and design of the new architecture.

**Take into account that:**
- Create Mermaid diagrams when you consider to visually improve the document.
- we do not have to migrate anything from the flask monolith. We will start from scratch with the new architecture and a new database with no data.
- We will use new way to publish the xml feed, we will not use Github to host the xml file any more. We will publish a route on the backend that will serve the xml file.
- We will use Docker and Docker Compose to deploy the application.

