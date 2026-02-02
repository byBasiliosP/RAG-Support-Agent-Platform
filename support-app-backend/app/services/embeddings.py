# app/services/embeddings.py
"""
Google Vertex AI embeddings service for vector operations.
"""
from langchain_google_vertexai import VertexAIEmbeddings
from ..config import settings

# Initialize Vertex AI embeddings
embeddings = None

if settings.GOOGLE_PROJECT_ID and settings.GOOGLE_PROJECT_ID != "your-project-id":
    try:
        embeddings = VertexAIEmbeddings(
            model_name=settings.GEMINI_EMBEDDING_MODEL,
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_LOCATION,
            credentials=settings.GOOGLE_APPLICATION_CREDENTIALS or None
        )
        print("✅ Vertex AI embeddings initialized")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI embeddings: {e}")
        embeddings = None
else:
    print("Warning: Google Project ID not set. RAG functionality will be limited.")
