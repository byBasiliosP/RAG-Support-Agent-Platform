# AI-Powered Customer Support Agent - Docker Setup ✅

**Status**: ✅ **DEPLOYED AND OPERATIONAL**

This project uses Docker to containerize the complete AI-powered customer support agent stack with all services running successfully.

## 🏗️ **Current Architecture**

- ✅ **Frontend**: Next.js application on port 3000 (RUNNING)
- ✅ **Backend**: FastAPI application on port 9000 (RUNNING)
- ✅ **PostgreSQL**: Database on port 5433 (HEALTHY)
- ✅ **ChromaDB**: Vector store on port 8001 (RUNNING)

**All services verified operational as of June 9, 2025**

## 🚀 **Quick Start** (TESTED ✅)

### **Current Production Deployment**

The application is already running! Access it at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:9000
- **API Documentation**: http://localhost:9000/docs

### **Service Management Commands**

1. **Check current status**:
   ```bash
   docker-compose ps
   ```

2. **View service logs**:
   ```bash
   docker-compose logs -f
   ```

3. **Restart all services**:
   ```bash
   docker-compose restart
   ```

4. **Stop all services**:
   ```bash
   docker-compose down
   ```

5. **Start fresh deployment**:
   ```bash
   docker-compose up -d
   ```

### Development Mode

1. **Start in development mode**:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **This enables**:
   - Hot reloading for frontend
   - Volume mounting for live code changes
   - Development environment variables

## Individual Service Management

### Frontend Only
```bash
# Build frontend image
docker-compose build frontend

# Start frontend only
docker-compose up frontend

# View frontend logs
docker-compose logs -f frontend
```

### Backend Only
```bash
# Build backend image
docker-compose build backend

# Start backend with dependencies
docker-compose up backend postgres chromadb

# View backend logs
docker-compose logs -f backend
```

## Environment Variables

### Frontend (.env)
```
NEXT_PUBLIC_API_URL=http://localhost:9000
NODE_ENV=production
```

### Backend (.env)
```
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=postgresql+asyncpg://support_user:support_pass_2024@postgres:5432/support_tickets_db
CHROMA_URL=http://chromadb:8000
```

## Accessing Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:9000
- **Backend Docs**: http://localhost:9000/docs
- **PostgreSQL**: localhost:5433
- **ChromaDB**: http://localhost:8001

## Troubleshooting

### Rebuild containers
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### View container status
```bash
docker-compose ps
```

### Access container shell
```bash
# Frontend container
docker-compose exec frontend sh

# Backend container
docker-compose exec backend sh
```

### Reset volumes
```bash
docker-compose down -v
docker volume prune
```

## Network Configuration

All services communicate through the `support-app-network` bridge network. Services can reach each other using their service names:

- Frontend can call backend at `http://backend:9000`
- Backend can call ChromaDB at `http://chromadb:8000`
- Backend can call PostgreSQL at `postgres:5432`
