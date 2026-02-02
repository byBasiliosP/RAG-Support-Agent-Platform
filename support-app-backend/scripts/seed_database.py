"""
Database seed script for RAG Support Agent
Creates initial data including users, categories, KB articles, and sample tickets
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    Base, Users, TicketCategories, KBArticles, Tickets, 
    ResolutionSteps, TicketRootCauses, TicketKBLinks
)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://support_user:support_pass_2024@localhost:5433/support_tickets_db"
)

async def seed_database():
    """Seed the database with initial data"""
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🌱 Starting database seeding...")
        
        # Check for existing users
        from sqlalchemy import select as sql_select
        result = await session.execute(sql_select(Users))
        existing_users = result.scalars().all()
        
        if not existing_users:
            # 1. Create Users
            print("\n📝 Creating users...")
            users = [
                Users(
                    username="admin",
                    email="admin@support.local",
                    display_name="System Administrator",
                    role="admin"
                ),
                Users(
                    username="tech1",
                    email="tech1@support.local",
                    display_name="John Tech",
                    role="technician"
                ),
                Users(
                    username="tech2",
                    email="tech2@support.local",
                    display_name="Sarah Support",
                    role="technician"
                ),
                Users(
                    username="user1",
                    email="user1@company.local",
                    display_name="Alice User",
                    role="end-user"
                ),
                Users(
                    username="user2",
                    email="user2@company.local",
                    display_name="Bob Employee",
                    role="end-user"
                ),
            ]
            session.add_all(users)
            await session.commit()
            print(f"✅ Created {len(users)} users")
        else:
            print(f"\n✓ Found {len(existing_users)} existing users, skipping user creation")
        
        # Get user IDs for foreign keys
        result = await session.execute(sql_select(Users).where(Users.username == "admin"))
        admin_user = result.scalar_one_or_none()
        result = await session.execute(sql_select(Users).where(Users.username == "tech1"))
        tech1_user = result.scalar_one_or_none()
        result = await session.execute(sql_select(Users).where(Users.username == "tech2"))
        tech2_user = result.scalar_one_or_none()
        result = await session.execute(sql_select(Users).where(Users.username == "user1"))
        user1 = result.scalar_one_or_none()
        result = await session.execute(sql_select(Users).where(Users.username == "user2"))
        user2 = result.scalar_one_or_none()
        
        # Check for existing categories
        result = await session.execute(sql_select(TicketCategories))
        existing_categories = result.scalars().all()
        
        if not existing_categories:
            # 2. Create Categories
            print("\n📂 Creating ticket categories...")
            categories = [
                TicketCategories(
                    name="Platform Setup",
                    description="Installation, configuration, and deployment of the RAG Support Agent platform"
                ),
                TicketCategories(
                    name="AI & RAG",
                    description="Issues related to AI responses, RAG queries, and Vertex AI integration"
                ),
                TicketCategories(
                    name="WebSocket & Real-Time",
                    description="WebSocket connections, real-time updates, and notifications"
                ),
                TicketCategories(
                    name="Knowledge Base",
                    description="KB article management, versioning, and auto-generation"
                ),
                TicketCategories(
                    name="Analytics",
                    description="Dashboard, metrics, sentiment analysis, and reporting"
                ),
            ]
            session.add_all(categories)
            await session.commit()
            print(f"✅ Created {len(categories)} categories")
        else:
            print(f"\n✓ Found {len(existing_categories)} existing categories, skipping category creation")
        
        # 3. Create KB Articles about the project
        print("\n📚 Creating knowledge base articles...")
        kb_articles = [
            KBArticles(
                title="Getting Started with RAG Support Agent",
                summary="Quick start guide for deploying and running the RAG Support Agent platform",
                content="""# Getting Started with RAG Support Agent

## Prerequisites
- Docker & Docker Compose
- Google Cloud credentials (for Vertex AI features)

## Quick Start

1. **Clone the repository**
2. **Configure environment variables** in `.env`:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `GOOGLE_PROJECT_ID` (optional, for AI features)
   - `GOOGLE_LOCATION` (optional, default: us-central1)

3. **Add Google credentials** (optional):
   - Place service account JSON at `secrets/google-credentials.json`

4. **Start services**:
   ```bash
   docker-compose up -d
   ```

5. **Verify health**:
   ```bash
   curl http://localhost:9000/health
   ```

6. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:9000
   - API Docs: http://localhost:9000/docs

## Next Steps
- Create your first ticket
- Explore the knowledge base
- Try the voice assistant
- View analytics dashboard
""",
                created_by=admin_user.user_id if admin_user else 1,
                version=1
            ),
            KBArticles(
                title="Understanding the RAG System",
                summary="How the Retrieval-Augmented Generation system works in the support platform",
                content="""# Understanding the RAG System

## What is RAG?
RAG (Retrieval-Augmented Generation) combines vector search with large language models to provide accurate, context-aware responses.

## Architecture

### Components
1. **Vector Database** - PostgreSQL with pgvector extension
2. **Embeddings** - Vertex AI text-embedding-004 model
3. **LLM** - Gemini 2.0 Flash via Vertex AI
4. **Cache** - Redis for performance optimization

### How It Works

1. **Query Processing**
   - User submits a question
   - Query is converted to embeddings
   - Vector similarity search finds relevant KB articles

2. **Context Retrieval**
   - Top K most relevant documents retrieved
   - Context is ranked by relevance score

3. **Response Generation**
   - Context + query sent to Gemini
   - LLM generates informed response
   - Sources are cited for transparency

## API Endpoint
```
POST /rag/query
{
  "query": "How do I reset my password?"
}
```

## Performance
- Redis caching reduces latency
- Vector search is highly optimized
- Rate limiting prevents abuse (20 requests/min)
""",
                created_by=admin_user.user_id if admin_user else 1,
                version=1
            ),
            KBArticles(
                title="WebSocket Real-Time Features",
                summary="Guide to using WebSocket endpoints for live updates and notifications",
                content="""# WebSocket Real-Time Features

## Overview
The platform provides WebSocket endpoints for real-time updates on tickets and user notifications.

## Endpoints

### Ticket Updates
```
ws://localhost:9000/ws/tickets/{ticket_id}?token=YOUR_TOKEN
```

**Events:**
- `ticket.updated` - Ticket fields changed
- `ticket.comment` - New comment added
- `ticket.status_changed` - Status transition
- `ticket.assigned` - Assignment changed

### User Notifications
```
ws://localhost:9000/ws/notifications/{user_id}?token=YOUR_TOKEN
```

**Events:**
- `notification` - General notification
- `ticket.assigned` - Ticket assigned to user
- `sla.warning` - SLA approaching deadline

## Client Example

```javascript
const ws = new WebSocket('ws://localhost:9000/ws/tickets/123?token=abc');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event);
  console.log('Data:', data.data);
};
```

## Connection Management
- Automatic reconnection on disconnect
- Heartbeat/ping-pong for connection health
- Room-based subscriptions for efficient broadcasting
""",
                created_by=tech1_user.user_id if tech1_user else 2,
                version=1
            ),
            KBArticles(
                title="KB Article Versioning and Auto-Generation",
                summary="How to manage KB article versions and auto-generate articles from resolved tickets",
                content="""# KB Article Versioning and Auto-Generation

## Versioning

### Create Version Snapshot
```
POST /support/kb/{kb_id}/version?user_id=1&change_note=Updated%20troubleshooting%20steps
```

### List Versions
```
GET /support/kb/{kb_id}/versions
```

### Revert to Previous Version
```
POST /support/kb/{kb_id}/revert/{target_version}?user_id=1
```

## Auto-Generation from Tickets

### How It Works
1. Ticket is resolved with detailed resolution steps
2. Admin triggers auto-generation
3. Vertex AI analyzes ticket data:
   - Subject and description
   - Root causes
   - Resolution steps
   - Success indicators
4. Structured KB article is generated
5. Article is saved with `auto_generated=true` flag

### API Endpoint
```
POST /support/kb/generate-from-ticket/{ticket_id}?user_id=1
```

### Generated Article Structure
- **Title** - Problem-focused, searchable
- **Summary** - 2-3 sentence overview
- **Content** - Markdown formatted:
  - Problem Description
  - Root Cause
  - Solution Steps (numbered)
  - Prevention Tips

### Best Practices
- Ensure tickets have detailed resolution steps
- Review auto-generated articles before publishing
- Add manual refinements as needed
- Link generated articles back to source tickets
""",
                created_by=admin_user.user_id if admin_user else 1,
                version=1
            ),
            KBArticles(
                title="Sentiment Analysis and Trends",
                summary="Using AI-powered sentiment analysis to track customer satisfaction",
                content="""# Sentiment Analysis and Trends

## Overview
The platform uses Vertex AI to analyze sentiment in ticket descriptions and comments, providing insights into customer satisfaction.

## Features

### Text Analysis
```
POST /analytics/sentiment/analyze
{
  "text": "I'm frustrated with this recurring issue"
}
```

**Response:**
```json
{
  "sentiment": "negative",
  "confidence": 0.87,
  "keywords": ["frustrated", "recurring", "issue"]
}
```

### Sentiment Trends
```
GET /analytics/sentiment/trends?days_back=30
```

**Returns:**
- Daily sentiment breakdown (positive/neutral/negative)
- Average confidence scores
- Overall summary statistics

## Use Cases

1. **Customer Satisfaction Monitoring**
   - Track sentiment over time
   - Identify negative trends early
   - Measure impact of changes

2. **Priority Escalation**
   - Auto-escalate highly negative tickets
   - Alert managers to dissatisfaction
   - Proactive customer outreach

3. **Team Performance**
   - Measure sentiment before/after resolution
   - Identify training opportunities
   - Recognize high-performing agents

## Dashboard Integration
Sentiment trends are displayed in the analytics dashboard with visual charts and actionable insights.
""",
                created_by=tech1_user.user_id if tech1_user else 2,
                version=1
            ),
            KBArticles(
                title="Troubleshooting Common Issues",
                summary="Solutions to frequently encountered problems with the support platform",
                content="""# Troubleshooting Common Issues

## Backend Won't Start

### Symptoms
- Container exits immediately
- Import errors in logs
- Database connection failures

### Solutions

1. **Check logs:**
   ```bash
   docker logs new-support-agent-backend-1
   ```

2. **Verify environment variables:**
   - `DATABASE_URL` is set correctly
   - PostgreSQL is healthy
   - Redis is running

3. **Missing Google credentials:**
   - AI features will be disabled but service should still run
   - Check for warning messages in logs

## Slow RAG Queries

### Symptoms
- Queries take >5 seconds
- Timeout errors

### Solutions

1. **Check Redis connection:**
   ```bash
   docker exec -it new-support-agent-redis-1 redis-cli ping
   ```

2. **Verify vector database:**
   - Ensure embeddings are populated
   - Check index performance

3. **Adjust retrieval parameters:**
   - Reduce `k` value for fewer documents
   - Enable caching for repeated queries

## WebSocket Connection Issues

### Symptoms
- Cannot connect to WebSocket
- Immediate disconnection
- CORS errors

### Solutions

1. **Verify backend is running:**
   ```bash
   curl http://localhost:9000/health
   ```

2. **Check CORS settings in `main.py`:**
   - Ensure frontend URL is in `ALLOWED_ORIGINS`

3. **Use correct WebSocket URL:**
   - `ws://localhost:9000/ws/...` (not `http://`)

## Frontend Not Updating

### Symptoms
- Code changes not reflected
- Stale content displayed

### Solutions

1. **Rebuild frontend:**
   ```bash
   docker-compose build frontend
   docker-compose up -d --force-recreate frontend
   ```

2. **Clear browser cache:**
   - Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

3. **Check build logs:**
   ```bash
   docker logs new-support-agent-frontend-1
   ```
""",
                created_by=tech2_user.user_id if tech2_user else 2,
                version=1
            ),
        ]
        session.add_all(kb_articles)
        await session.commit()
        print(f"✅ Created {len(kb_articles)} KB articles")
        
        # 4. Create Sample Tickets
        print("\n🎫 Creating sample tickets...")
        now = datetime.utcnow()
        
        tickets = [
            Tickets(
                external_ticket_no="SUPP-001",
                requester_id=4,
                assigned_to_id=2,
                category_id=1,
                priority="High",
                status="Closed",
                subject="Docker container won't start",
                description="Getting error when running docker-compose up. Backend container exits immediately.",
                created_at=now - timedelta(days=5),
                closed_at=now - timedelta(days=4),
                sla_due_at=now - timedelta(days=3)
            ),
            Tickets(
                external_ticket_no="SUPP-002",
                requester_id=5,
                assigned_to_id=2,
                category_id=2,
                priority="Medium",
                status="In Progress",
                subject="RAG queries returning irrelevant results",
                description="When I ask about password reset, I'm getting articles about VPN setup instead.",
                created_at=now - timedelta(days=2),
                sla_due_at=now + timedelta(days=1)
            ),
            Tickets(
                external_ticket_no="SUPP-003",
                requester_id=4,
                assigned_to_id=3,
                category_id=3,
                priority="Low",
                status="Open",
                subject="WebSocket disconnects frequently",
                description="Real-time notifications work for a few minutes then stop. Need to refresh page.",
                created_at=now - timedelta(hours=6),
                sla_due_at=now + timedelta(days=2)
            ),
        ]
        session.add_all(tickets)
        await session.commit()
        print(f"✅ Created {len(tickets)} sample tickets")
        
        # 5. Add resolution steps to closed ticket
        print("\n🔧 Adding resolution steps...")
        resolution_steps = [
            ResolutionSteps(
                ticket_id=1,
                step_order=1,
                instructions="Checked docker logs and found missing DATABASE_URL environment variable",
                success_flag=True,
                performed_by=2,
                performed_at=now - timedelta(days=4, hours=2)
            ),
            ResolutionSteps(
                ticket_id=1,
                step_order=2,
                instructions="Added DATABASE_URL to .env file with correct PostgreSQL connection string",
                success_flag=True,
                performed_by=2,
                performed_at=now - timedelta(days=4, hours=1)
            ),
            ResolutionSteps(
                ticket_id=1,
                step_order=3,
                instructions="Restarted containers with docker-compose up -d",
                success_flag=True,
                performed_by=2,
                performed_at=now - timedelta(days=4)
            ),
        ]
        session.add_all(resolution_steps)
        await session.commit()
        print(f"✅ Created {len(resolution_steps)} resolution steps")
        
        # 6. Add root cause
        print("\n🔍 Adding root cause...")
        root_cause = TicketRootCauses(
            ticket_id=1,
            cause_code="CONFIG-001",
            description="Missing required environment variable in .env file",
            identified_at=now - timedelta(days=4, hours=2)
        )
        session.add(root_cause)
        await session.commit()
        print("✅ Created root cause")
        
        # 7. Link KB article to ticket
        print("\n🔗 Linking KB articles to tickets...")
        kb_link = TicketKBLinks(
            ticket_id=1,
            kb_id=1  # "Getting Started" article
        )
        session.add(kb_link)
        await session.commit()
        print("✅ Created KB link")
        
        print("\n✅ Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   - {len(users)} users")
        print(f"   - {len(categories)} categories")
        print(f"   - {len(kb_articles)} KB articles")
        print(f"   - {len(tickets)} tickets")
        print(f"   - {len(resolution_steps)} resolution steps")
        print(f"   - 1 root cause")
        print(f"   - 1 KB link")

if __name__ == "__main__":
    asyncio.run(seed_database())
