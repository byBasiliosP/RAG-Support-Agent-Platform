# RAG Support Agent

AI-powered IT support platform with RAG, WebSockets, and Vertex AI integration.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:9000/health
```

## Features

- **RAG-Powered Support** - Intelligent responses using vector search + LLM
- **Ticket Management** - Full CRUD with categories, priorities, SLA tracking
- **Knowledge Base** - Versioned articles with auto-generation from tickets
- **Real-Time Updates** - WebSocket support for live notifications
- **Voice Support** - ElevenLabs integration for voice interactions
- **Analytics** - Sentiment analysis, trends, and performance metrics

## Documentation

- [API Reference](docs/API_GUIDE.md)
- [Operations Runbook](docs/RUNBOOK.md)

## Architecture

| Service | Port | Technology |
|---------|------|------------|
| Backend API | 9000 | FastAPI + Python |
| Database | 5432 | PostgreSQL 18 + pgvector |
| Cache | 6379 | Redis |
| AI | - | Google Vertex AI (Gemini) |

## Configuration

Create `.env` with:
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
GOOGLE_PROJECT_ID=your-project
GOOGLE_LOCATION=us-central1
```

Place Google credentials at `secrets/google-credentials.json`.

## Development

```bash
# Rebuild after changes
docker-compose build backend
docker-compose up -d backend

# View logs
docker logs -f new-support-agent-backend-1
```
