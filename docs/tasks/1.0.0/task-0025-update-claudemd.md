# Prompt

We have made several changes to the application and the way we deploy it using Docker. We want to update the `CLAUDE.md` file. 

There is a new `DEPLOYMENT.md` file in the root folder that describes in detail the new development and production deployment process with docker, and locally without docker.

We also changed an important thing. We now use two separate databases for development (`backend/data/labcastarr-dev.db`) and production (`backend/data/labcastarr.db`).

We want to update the `CLAUDE.md` file with the current state of the codebase.


---

## Result


⏺ I've successfully updated the CLAUDE.md file with the current state of the codebase, incorporating the
new deployment processes and database changes. Here are the key updates made:

Key Changes Made:

🗃️ Database Configuration

- Updated to reflect separate databases for development (labcastarr-dev.db) and production
(labcastarr.db)
- Added environment detection explanation via backend/app/core/config.py
- Updated database path documentation and troubleshooting

🐳 Docker Deployment

- Streamlined Docker Compose section to reference DEPLOYMENT.md for detailed instructions
- Clarified development vs production Docker configurations
- Updated command examples to show environment-specific database usage
- Removed redundant deployment details now covered in DEPLOYMENT.md

🔧 Environment Configuration

- Restructured environment section to clearly separate development and production configurations
- Added specific environment file references (.env.development vs .env.production)
- Included production-specific variables (domains, CORS origins, etc.)
- Added security note about generating API keys with openssl rand -base64 32

📚 References and Cross-links

- Added reference to DEPLOYMENT.md for detailed deployment instructions
- Maintained existing architecture documentation and development guidelines
- Preserved all Cursor rules and code style enforcement information

The updated CLAUDE.md now accurately reflects the current codebase state with the dual database setup and comprehensive Docker deployment strategy, while maintaining all the essential development guidance for future Claude Code instances.
