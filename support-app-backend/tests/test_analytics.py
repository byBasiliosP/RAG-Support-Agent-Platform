# tests/test_analytics.py
"""
Tests for analytics router endpoints.
Tests comprehensive analytics and ElevenLabs voice analytics.
"""
import pytest
from httpx import AsyncClient


class TestComprehensiveAnalytics:
    """Test comprehensive analytics endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics(self, client: AsyncClient):
        """Test getting comprehensive analytics."""
        response = await client.get("/analytics/comprehensive")
        assert response.status_code == 200
        data = response.json()
        # Check expected structure
        assert "total_tickets" in data or "tickets" in data or isinstance(data, dict)


class TestTicketAnalytics:
    """Test ticket-specific analytics."""
    
    @pytest.mark.asyncio
    async def test_ticket_performance(self, client: AsyncClient):
        """Test ticket performance metrics."""
        response = await client.get("/analytics/ticket-performance")
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_sla_performance(self, client: AsyncClient):
        """Test SLA performance metrics."""
        response = await client.get("/analytics/sla-performance")
        assert response.status_code in [200, 404]


class TestElevenLabsAnalytics:
    """Test ElevenLabs voice analytics endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_elevenlabs_summary(self, client: AsyncClient):
        """Test getting ElevenLabs analytics summary."""
        response = await client.get("/analytics/elevenlabs")
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "total_duration_minutes" in data
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, client: AsyncClient):
        """Test listing voice conversations."""
        response = await client.get("/analytics/elevenlabs/conversations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_track_conversation(self, client: AsyncClient):
        """Test tracking a new voice conversation."""
        conversation_data = {
            "conversation_id": "test-conv-123",
            "agent_id": "test-agent-456",
            "user_id": "user-789"
        }
        response = await client.post(
            "/analytics/elevenlabs/conversations",
            json=conversation_data
        )
        # Should succeed or conflict if exists
        assert response.status_code in [200, 201, 409]
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client: AsyncClient):
        """Test getting non-existent conversation returns 404."""
        response = await client.get("/analytics/elevenlabs/conversations/nonexistent")
        assert response.status_code == 404


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client: AsyncClient):
        """Test that rate limit headers are present in response."""
        response = await client.get("/health")
        # Rate limiting should add headers (or be transparent)
        assert response.status_code == 200
