# tests/conftest.py
"""
Pytest fixtures for New-Support-Agent backend tests.
Provides database, client, and mock service fixtures.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Test database URL (uses same schema but different database)
TEST_DATABASE_URL = "postgresql+asyncpg://support_user:support_pass_2024@localhost:5433/support_tickets_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_openai():
    """Mock OpenAI API for tests."""
    with patch("app.services.embeddings.OpenAIEmbeddings") as mock:
        mock_instance = MagicMock()
        mock_instance.embed_query.return_value = [0.1] * 1536  # text-embedding-3-small dimensions
        mock_instance.embed_documents.return_value = [[0.1] * 1536]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_vectordb():
    """Mock vector database for tests."""
    with patch("app.services.vectorstore.vectordb") as mock:
        mock.similarity_search.return_value = []
        mock.add_documents.return_value = None
        yield mock


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for API testing."""
    # Import here to avoid circular imports
    from main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Sample test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "display_name": "Test User",
        "role": "technician"
    }


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "subject": "Test Ticket",
        "description": "This is a test ticket description",
        "priority": "medium",
        "requester_name": "John Doe",
        "requester_email": "john@example.com",
        "requester_phone": "555-1234",
        "preferred_contact": "email",
        "affected_system": "Email",
        "business_impact": "Low",
        "steps_taken": "Restarted application",
        "error_messages": "Connection timeout"
    }


@pytest.fixture
def sample_kb_article_data():
    """Sample KB article data for testing."""
    return {
        "title": "How to Reset Password",
        "summary": "Step-by-step guide for password reset",
        "url": "https://kb.example.com/password-reset"
    }
