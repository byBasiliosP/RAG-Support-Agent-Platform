# app/services/agents.py
"""
Google Vertex AI LLM and agent services.
Provides chat completion and QA chain functionality.
"""
# LangChain 1.2.7 moved chains to langchain-community
try:
    from langchain.chains import RetrievalQA
except ImportError:
    try:
        from langchain_community.chains import RetrievalQA
    except ImportError:
        RetrievalQA = None
        print("Warning: RetrievalQA not available - QA chain disabled")

from langchain_google_vertexai import ChatVertexAI
from .vectorstore import vectordb
from ..config import settings

# Initialize Vertex AI LLM
llm = None
qa_chain = None

if settings.GOOGLE_PROJECT_ID and settings.GOOGLE_PROJECT_ID != "your-project-id":
    try:
        llm = ChatVertexAI(
            model_name=settings.GEMINI_MODEL,
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_LOCATION,
            credentials=settings.GOOGLE_APPLICATION_CREDENTIALS or None,
            temperature=0,
            convert_system_message_to_human=True
        )
        print("✅ Vertex AI LLM initialized")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI LLM: {e}")
        llm = None

def make_qa_chain():
    """Create a RetrievalQA chain with Vertex AI."""
    if llm is None or vectordb is None or RetrievalQA is None:
        return None
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

# Initialize the QA chain
qa_chain = make_qa_chain()

if qa_chain is None:
    print("Warning: QA chain not initialized due to missing dependencies.")
