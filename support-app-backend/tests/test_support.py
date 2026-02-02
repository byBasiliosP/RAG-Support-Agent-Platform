# tests/test_support.py
"""
Tests for support router endpoints.
Tests ticket, user, and KB article CRUD operations.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test that health endpoint returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestUserEndpoints:
    """Test user management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, sample_user_data):
        """Test creating a new user."""
        response = await client.post("/support/users", json=sample_user_data)
        # Should succeed or return conflict if user exists
        assert response.status_code in [200, 201, 409]
    
    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient):
        """Test listing all users."""
        response = await client.get("/support/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTicketEndpoints:
    """Test ticket management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_ticket(self, client: AsyncClient, sample_ticket_data):
        """Test creating a new ticket."""
        response = await client.post("/support/tickets", json=sample_ticket_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "ticket_id" in data or "id" in data
    
    @pytest.mark.asyncio
    async def test_list_tickets(self, client: AsyncClient):
        """Test listing tickets with pagination."""
        response = await client.get("/support/tickets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_filters(self, client: AsyncClient):
        """Test listing tickets with status filter."""
        response = await client.get("/support/tickets?status=Open")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_ticket_not_found(self, client: AsyncClient):
        """Test getting non-existent ticket returns 404."""
        response = await client.get("/support/tickets/99999")
        assert response.status_code == 404


class TestKBArticleEndpoints:
    """Test KB article management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_kb_articles(self, client: AsyncClient):
        """Test listing KB articles."""
        response = await client.get("/support/kb-articles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_search_kb_articles(self, client: AsyncClient):
        """Test searching KB articles."""
        response = await client.get("/support/kb-articles?search=password")
        assert response.status_code == 200


class TestCategoryEndpoints:
    """Test category management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_categories(self, client: AsyncClient):
        """Test listing ticket categories."""
        response = await client.get("/support/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
