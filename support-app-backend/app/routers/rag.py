# app/routers/rag.py
from fastapi import APIRouter, UploadFile, Depends, HTTPException, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..database import get_db
from ..models import Document
from ..services.vectorstore import vectordb
from ..services.agents import qa_chain
from ..services.enhanced_rag import enhanced_rag_service
from ..services.elevenlabs_service import elevenlabs_service
from ..services.document_processors import DocumentProcessor, get_supported_extensions
from ..langgraph_setup import ingest_document_as_nodes
import base64

router = APIRouter(prefix="/rag", tags=["rag"])

# Pydantic models for request/response
class EnhancedQueryRequest(BaseModel):
    query: str
    include_tickets: bool = True
    include_kb: bool = True
    category_filter: Optional[str] = None
    include_voice: bool = False

class VoiceQueryRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    include_tickets: bool = True
    include_kb: bool = True
    include_voice_response: bool = True

@router.get("/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get list of supported file formats"""
    return {
        "supported_formats": get_supported_extensions(),
        "message": "Upload files in any of these formats for processing"
    }

@router.post("/ingest")
async def ingest(file: UploadFile, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Ingest a document into the RAG system"""
    if vectordb is None:
        raise HTTPException(status_code=503, detail="RAG system not available - OpenAI API key not configured")
    
    try:
        # Get appropriate processor for file type
        processor = DocumentProcessor.get_processor(file)
        
        # Process the file to extract text
        processed_data = await processor.process(file)
        text = processed_data['text']
        metadata = processed_data['metadata']
        
        # Create database record with enhanced metadata
        doc = Document(
            title=file.filename, 
            content=text,
            # Store processing metadata as JSON in a metadata field if available
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        # Enhanced metadata for vector store
        vector_metadata = {
            "doc_id": doc.id, 
            "title": file.filename,
            "file_type": metadata.get('file_type', 'unknown'),
            **metadata
        }
        
        # Add to vector store
        vectordb.add_texts(
            texts=[text], 
            metadatas=[vector_metadata]
        )
        
        # Add to graph
        ingest_document_as_nodes(doc)
        
        return {
            "id": doc.id,
            "title": file.filename,
            "status": "ingested",
            "content_length": len(text),
            "file_type": metadata.get('file_type', 'unknown'),
            "processing_metadata": metadata
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like unsupported file type)
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")

@router.post("/query-enhanced")
async def query_enhanced(
    request: EnhancedQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Enhanced RAG query with ticketing system integration"""
    
    try:
        result = await enhanced_rag_service.query_with_context(
            query=request.query,
            db=db,
            include_tickets=request.include_tickets,
            include_kb=request.include_kb,
            category_filter=request.category_filter
        )
        
        # Add voice response if requested
        if request.include_voice:
            try:
                voice_response = await elevenlabs_service.create_voice_enabled_response(
                    result["answer"],
                    include_audio=True
                )
                result["voice"] = voice_response
            except Exception as e:
                result["voice"] = {"error": f"Voice generation failed: {str(e)}"}
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in enhanced query: {str(e)}")

@router.post("/query-voice")
async def query_voice(
    request: VoiceQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Process voice query with speech-to-text and text-to-speech"""
    
    try:
        # Step 1: Convert speech to text
        audio_bytes = base64.b64decode(request.audio_data)
        transcribed_text = await elevenlabs_service.speech_to_text(audio_bytes)
        
        # Step 2: Process the query with enhanced RAG
        result = await enhanced_rag_service.query_with_context(
            query=transcribed_text,
            db=db,
            include_tickets=request.include_tickets,
            include_kb=request.include_kb
        )
        
        # Step 3: Generate voice response
        if request.include_voice_response:
            voice_response = await elevenlabs_service.create_voice_enabled_response(
                result["answer"],
                include_audio=True
            )
            result["voice"] = voice_response
        
        # Add transcription info
        result["transcription"] = {
            "original_audio_size": len(audio_bytes),
            "transcribed_text": transcribed_text
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in voice query: {str(e)}")

@router.get("/voice/agent-embed")
async def get_agent_embed() -> Dict[str, Any]:
    """Get ElevenLabs ConvAI widget embed code"""
    
    embed_code = elevenlabs_service.get_agent_embed_code()
    
    return {
        "embed_code": embed_code,
        "agent_id": elevenlabs_service.agent_id,
        "instructions": "Add this HTML to your page to embed the voice assistant"
    }

@router.get("/voice/available-voices")
async def get_available_voices() -> Dict[str, Any]:
    """Get list of available ElevenLabs voices"""
    
    try:
        voices = await elevenlabs_service.get_available_voices()
        return {
            "voices": voices,
            "current_voice_id": elevenlabs_service.voice_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voices: {str(e)}")

@router.post("/voice/tts")
async def text_to_speech(
    text: str = Form(...),
    voice_id: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Convert text to speech"""
    
    try:
        audio_data = await elevenlabs_service.text_to_speech(text, voice_id=voice_id)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "text": text,
            "audio": {
                "format": "mp3",
                "data": audio_base64,
                "size_bytes": len(audio_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in text-to-speech: {str(e)}")

@router.get("/query")
async def query(q: str) -> Dict[str, Any]:
    """Query the RAG system (legacy endpoint)"""
    if vectordb is None or qa_chain is None:
        raise HTTPException(status_code=503, detail="RAG system not available - OpenAI API key not configured")
    
    try:
        result = qa_chain.invoke({"query": q})
        return {
            "query": q,
            "answer": result["result"],
            "source_documents": [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result.get("source_documents", [])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
