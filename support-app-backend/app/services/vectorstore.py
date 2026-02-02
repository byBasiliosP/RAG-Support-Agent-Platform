# app/services/vectorstore.py
from langchain_postgres import PGVector
from .embeddings import embeddings
from ..config import settings

# Use synchronous connection for PGVector (uses psycopg internally)
# Convert asyncpg URL to psycopg format
def get_sync_connection_string():
    """Convert asyncpg connection string to psycopg format for PGVector"""
    db_url = settings.DATABASE_URL
    if "postgresql+asyncpg://" in db_url:
        return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    return db_url

# Initialize vector database only if embeddings are available
vectordb = None
if embeddings is not None:
    try:
        connection_string = get_sync_connection_string()
        vectordb = PGVector(
            embeddings=embeddings,
            collection_name="support_system_docs",
            connection=connection_string,
            use_jsonb=True
        )
        print("✅ PGVector initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize vector database: {e}")
        vectordb = None
else:
    print("Warning: Vector database not initialized due to missing embeddings.")

