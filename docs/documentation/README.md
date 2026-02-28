# LabCastARR Documentation

**Updated:** 2026-01-29

This folder contains comprehensive, up-to-date documentation for the LabCastARR project. These documents reflect the current state of the codebase after thorough analysis.

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 00 | [PROJECT-STATUS-OVERVIEW.md](./00-PROJECT-STATUS-OVERVIEW.md) | Executive summary of project status, features, and current state |
| 01 | [ARCHITECTURE.md](./01-ARCHITECTURE.md) | System architecture overview, Clean Architecture layers, design patterns |
| 02 | [DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md) | Complete database schema, table definitions, migrations |
| 03 | [API-REFERENCE.md](./03-API-REFERENCE.md) | API endpoints documentation with request/response formats |
| 04 | [FRONTEND-ARCHITECTURE.md](./04-FRONTEND-ARCHITECTURE.md) | Frontend structure, components, hooks, state management |
| 05 | [CELERY-TASKS.md](./05-CELERY-TASKS.md) | Background tasks, Celery configuration, workflows |
| 06 | [DEPLOYMENT-GUIDE.md](./06-DEPLOYMENT-GUIDE.md) | Development and production deployment procedures |
| 07 | [ENVIRONMENT-CONFIGURATION.md](./07-ENVIRONMENT-CONFIGURATION.md) | Environment variables reference and configuration |
| 08 | [BACKEND-ARCHITECTURE.md](./08-BACKEND-ARCHITECTURE.md) | Backend internals, Clean Architecture implementation, external service integrations (yt-dlp, FFmpeg, PodGen) |

---

## Quick Links

### For Development

- Start with: [00-PROJECT-STATUS-OVERVIEW.md](./00-PROJECT-STATUS-OVERVIEW.md)
- System architecture: [01-ARCHITECTURE.md](./01-ARCHITECTURE.md)
- Backend internals: [08-BACKEND-ARCHITECTURE.md](./08-BACKEND-ARCHITECTURE.md)
- Frontend internals: [04-FRONTEND-ARCHITECTURE.md](./04-FRONTEND-ARCHITECTURE.md)
- API endpoints: [03-API-REFERENCE.md](./03-API-REFERENCE.md)

### For Deployment

- Deployment procedures: [06-DEPLOYMENT-GUIDE.md](./06-DEPLOYMENT-GUIDE.md)
- Environment setup: [07-ENVIRONMENT-CONFIGURATION.md](./07-ENVIRONMENT-CONFIGURATION.md)

### For Database Work

- Schema reference: [02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md)
- Migrations are managed via Alembic in `backend/alembic/`

### For Background Tasks

- Celery tasks: [05-CELERY-TASKS.md](./05-CELERY-TASKS.md)
- YouTube channel discovery architecture: See also `../TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md`

### For External Service Integrations

- yt-dlp, FFmpeg, PodGen, YouTube RSS: [08-BACKEND-ARCHITECTURE.md](./08-BACKEND-ARCHITECTURE.md) (Section: External Service Integrations)

---

## Related Documentation

The following documents in the parent directory provide additional context:

| Document | Description |
|----------|-------------|
| `TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md` | In-depth technical analysis of the YouTube channel following feature |
| `FUNCTIONALITY.md` | Feature-level functionality documentation |
| `DEPLOYMENT.md` | Original deployment guide |
| `API-UPLOAD-ENDPOINT.md` | Detailed file upload endpoint documentation |
| `AUTHENTICATION_ENHANCEMENTS_SUMMARY.md` | Authentication system improvements |
| `PRODUCTION-DEPLOYMENT-SOP.md` | Standard operating procedure for production deployments |

---

## Project Root Documentation

| Document | Description |
|----------|-------------|
| `/CLAUDE.md` | AI assistant instructions and development guidelines |
| `/README.md` | User-facing project overview and quick start |

---

## Notes

- These documents were created on 2026-01-29 based on thorough codebase analysis
- The original documentation files in the parent directory have been preserved
- For the most accurate information, always verify against the actual codebase
- If discrepancies are found, the codebase is the source of truth

---

## Statistics Summary

| Metric | Count |
|--------|-------|
| Backend Python Files | 100+ |
| Frontend TypeScript Files | 150+ |
| API Endpoints | 50+ |
| Database Tables | 14 |
| Alembic Migrations | 14 |
| Frontend Pages | 16 |
| React Components | 70+ |
| Custom Hooks | 12 |
| Celery Tasks | 5 |

---

**Project Status:** Feature-complete, Production-ready
