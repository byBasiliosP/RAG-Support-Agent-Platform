# ElevenLabs Analytics Integration Documentation

## Overview

The ElevenLabs Analytics integration provides comprehensive tracking and analytics for voice conversations using the ElevenLabs ConvAI widget. This system captures conversation metrics, user interactions, and provides detailed analytics dashboards.

## Architecture

### Frontend Components

#### 1. AnalyticsDashboard Component
- **Location**: `src/components/AnalyticsDashboard.tsx`
- **Purpose**: Main analytics dashboard displaying ElevenLabs conversation metrics
- **Features**:
  - Real-time analytics summary (total conversations, duration, satisfaction scores)
  - Conversation status distribution with visual progress bars
  - Top-performing agents leaderboard
  - Recent conversations table with detailed information
  - Responsive grid layout with loading states and error handling

#### 2. Enhanced Widget Component
- **Location**: `src/components/Widget.tsx`
- **Purpose**: ElevenLabs ConvAI widget with automatic analytics tracking
- **Features**:
  - Automatic conversation start tracking
  - Conversation end tracking on page unload
  - Unique conversation ID generation
  - Integration with backend analytics API

#### 3. Analytics Hooks
- **Location**: `src/hooks/useApi.ts`
- **Hooks Available**:
  - `useElevenLabsAnalytics()` - Fetches analytics summary
  - `useElevenLabsConversations(limit)` - Fetches conversation list
  - `useElevenLabsConversation(id)` - Fetches specific conversation
  - `useElevenLabsMessages(conversationId)` - Fetches conversation messages

### Backend API Endpoints

#### Analytics Summary
```
GET /analytics/elevenlabs
```
Returns comprehensive analytics including:
- Total conversations count
- Total and average conversation duration
- Conversations grouped by status
- Daily conversation trends
- Top-performing agents
- User satisfaction metrics

#### Conversation Management
```
GET /analytics/elevenlabs/conversations?limit=50
POST /analytics/elevenlabs/conversations
PUT /analytics/elevenlabs/conversations/{conversation_id}
GET /analytics/elevenlabs/conversations/{conversation_id}
GET /analytics/elevenlabs/conversations/{conversation_id}/messages
```

### Data Models

#### ElevenLabsConversation
```typescript
interface ElevenLabsConversation {
  conversation_id: string;
  agent_id: string;
  user_id?: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  messages_count: number;
  status: 'active' | 'completed' | 'abandoned';
  metadata?: Record<string, any>;
}
```

#### ElevenLabsAnalytics
```typescript
interface ElevenLabsAnalytics {
  total_conversations: number;
  total_duration_minutes: number;
  average_conversation_duration: number;
  conversations_by_status: Record<string, number>;
  conversations_by_date: Array<{date: string; count: number}>;
  top_agents: Array<{agent_id: string; conversation_count: number}>;
  user_satisfaction?: {average_rating: number; total_ratings: number};
}
```

## Features

### Dashboard Metrics
1. **Total Conversations**: All-time conversation count
2. **Total Duration**: Cumulative conversation time in minutes
3. **Average Duration**: Mean conversation length
4. **Satisfaction Score**: User rating average with total ratings count

### Visual Analytics
1. **Status Distribution**: Progress bars showing conversation status breakdown
2. **Agent Performance**: Leaderboard of top-performing agents
3. **Recent Activity**: Detailed table of latest conversations

### Real-time Tracking
- Automatic conversation start detection
- Background conversation tracking
- Page unload conversation completion
- Unique conversation ID generation

## Usage

### Accessing Analytics Dashboard
1. Navigate to the main application
2. Click on the "Analytics" tab
3. View real-time ElevenLabs conversation analytics

### Widget Integration
The ElevenLabs widget automatically tracks conversations when users interact with it:

```tsx
<ElevenLabsConvAI agentId="your-agent-id" />
```

### API Integration
```typescript
// Fetch analytics summary
const { data, loading, error } = useElevenLabsAnalytics();

// Fetch recent conversations
const { data: conversations } = useElevenLabsConversations(10);

// Track custom conversation
await ApiService.trackElevenLabsConversation({
  conversation_id: "custom_id",
  agent_id: "agent_123",
  start_time: new Date().toISOString(),
  status: "active",
  messages_count: 0
});
```

## Testing

### Backend API Testing
```bash
# Test analytics summary
curl -X GET "http://localhost:9000/analytics/elevenlabs"

# Test conversation tracking
curl -X POST "http://localhost:9000/analytics/elevenlabs/conversations" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test", "agent_id": "agent1", "start_time": "2025-06-08T12:00:00", "status": "active", "messages_count": 0}'

# Test conversation list
curl -X GET "http://localhost:9000/analytics/elevenlabs/conversations?limit=5"
```

### Frontend Testing
1. Open http://localhost:3001
2. Navigate to Analytics tab
3. Verify metrics display correctly
4. Test widget interaction tracking
5. Check conversation table updates

## Data Storage

Currently using in-memory storage for demonstration purposes. In production, replace with:
- PostgreSQL for conversation metadata
- Time-series database for metrics (e.g., InfluxDB)
- Redis for real-time caching

## Performance Considerations

1. **Pagination**: Conversation lists are paginated (default limit: 50)
2. **Loading States**: All components show loading indicators
3. **Error Handling**: Comprehensive error handling with user feedback
4. **Caching**: React hooks provide automatic caching
5. **Progressive Enhancement**: Fallback to sample data when no real data exists

## Security

1. **CORS**: Properly configured for frontend-backend communication
2. **Input Validation**: All API inputs validated using Pydantic models
3. **Error Sanitization**: Error messages sanitized before frontend display
4. **Rate Limiting**: Consider implementing for production use

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live analytics
2. **Advanced Filtering**: Date ranges, agent filters, status filters
3. **Export Functionality**: CSV/PDF export of analytics data
4. **Custom Dashboards**: User-configurable dashboard layouts
5. **Alerting**: Threshold-based notifications for conversation metrics
6. **A/B Testing**: Agent performance comparison tools

## Integration Status

✅ **Complete**:
- Backend API endpoints with sample data
- Frontend Analytics Dashboard component
- React hooks for data fetching
- Widget conversation tracking
- TypeScript type definitions
- Error handling and loading states
- Responsive UI design

✅ **Tested**:
- All API endpoints functional
- Frontend compilation without errors
- Widget tracking operational
- Analytics dashboard displaying data
- Real-time conversation tracking

## Getting Started

1. **Backend**: Ensure backend is running on http://localhost:9000
2. **Frontend**: Start frontend on http://localhost:3001
3. **Access**: Navigate to Analytics tab to view ElevenLabs metrics
4. **Interact**: Use the voice widget to generate tracked conversations
5. **Monitor**: Watch real-time analytics updates
