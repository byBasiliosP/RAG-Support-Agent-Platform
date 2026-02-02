# Operations Runbook

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Cloud credentials (for Vertex AI)

### Start Services
```bash
cd /Volumes/WD_4D/NYU\ Dev/New-Support-Agent
docker-compose up -d
```

### Verify Health
```bash
curl http://localhost:9000/health
```

---

## Service Ports

| Service | Port |
|---------|------|
| Backend API | 9000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection | Yes |
| `GOOGLE_PROJECT_ID` | GCP project for Vertex AI | For AI features |
| `GOOGLE_LOCATION` | GCP region (default: us-central1) | For AI features |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | For AI features |

---

## Common Operations

### Restart Backend
```bash
docker-compose restart backend
```

### View Logs
```bash
docker logs -f new-support-agent-backend-1
```

### Database Migration
```bash
docker exec -it new-support-agent-backend-1 alembic upgrade head
```

### Rebuild After Code Changes
```bash
docker-compose build backend
docker-compose up -d backend
```

---

## Troubleshooting

### Backend Won't Start

1. **Check logs:** `docker logs new-support-agent-backend-1`
2. **Common issues:**
   - Missing `GOOGLE_PROJECT_ID` → AI features disabled but service runs
   - Database connection → Verify PostgreSQL is healthy
   - Import errors → Check for syntax/dependency issues

### Slow RAG Queries

1. Check Redis connection
2. Verify vector database is populated
3. Consider adjusting `k` parameter for retrieval

### WebSocket Not Connecting

1. Verify backend is running on port 9000
2. Check CORS settings in `main.py`
3. Ensure client uses correct WebSocket URL (`ws://`, not `http://`)

---

## Monitoring

### Health Endpoints
- `GET /health` - Basic health
- `GET /ws/stats` - WebSocket connections

### Logs Location
- Docker: `docker logs new-support-agent-backend-1`
- Structured logs in JSON format

---

## Backup & Recovery

### Database Backup
```bash
docker exec new-support-agent-postgres-1 pg_dump -U support_user support_tickets_db > backup.sql
```

### Database Restore
```bash
cat backup.sql | docker exec -i new-support-agent-postgres-1 psql -U support_user support_tickets_db
```
