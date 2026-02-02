# RAG Support Agent - API Reference

## Base URL
```
http://localhost:9000
```

---

## Health & Status

### GET /health
Check service health.

**Response:**
```json
{"status": "healthy", "service": "RAG-Support-Agent", "version": "1.0.0"}
```

---

## Support Tickets

### POST /support/tickets
Create a new ticket.

**Body:**
```json
{
  "subject": "Email not syncing",
  "description": "Outlook fails to sync since this morning",
  "priority": "High",
  "category_id": 1
}
```

### GET /support/tickets
List tickets with pagination.

**Query Params:** `skip`, `limit`, `status`, `priority`

### GET /support/tickets/{ticket_id}
Get ticket details.

### PUT /support/tickets/{ticket_id}
Update ticket fields.

---

## Knowledge Base

### GET /support/kb
List KB articles.

### POST /support/kb
Create KB article.

**Body:**
```json
{
  "title": "How to reset password",
  "summary": "Step-by-step guide",
  "content": "# Steps\n1. Go to...",
  "url": "https://kb.example.com/reset"
}
```

### GET /support/kb/{kb_id}/versions
List version history.

### POST /support/kb/{kb_id}/version
Create version snapshot.

**Query Params:** `user_id` (required), `change_note` (optional)

### POST /support/kb/{kb_id}/revert/{target_version}
Revert to previous version.

**Query Params:** `user_id` (required)

### POST /support/kb/generate-from-ticket/{ticket_id}
Auto-generate KB from resolved ticket (Vertex AI).

**Query Params:** `user_id` (required)

---

## RAG / AI

### POST /rag/query
Query the RAG system.

**Body:**
```json
{"query": "How do I fix VPN connection issues?"}
```

**Response:**
```json
{
  "query": "...",
  "answer": "...",
  "confidence": 0.85,
  "sources": {...}
}
```

---

## Analytics

### GET /analytics/comprehensive
Full analytics dashboard.

### GET /analytics/sentiment/trends
Sentiment trends over time.

**Query Params:** `days_back` (default: 30)

### POST /analytics/sentiment/analyze
Analyze text sentiment.

**Body:**
```json
{"text": "I'm frustrated with this recurring issue"}
```

---

## WebSocket Endpoints

### WS /ws/tickets/{ticket_id}
Real-time ticket updates.

**Events:** `ticket.updated`, `ticket.comment`, `ticket.status_changed`

### WS /ws/notifications/{user_id}
User notifications stream.

**Events:** `notification`, `ticket.assigned`, `sla.warning`

---

## Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Default | 100/min |
| RAG/AI | 20/min |
| Analytics | 60/min |
| Write (POST/PUT) | 50/min |
| Voice | 30/min |
