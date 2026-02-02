# app/routers/voice_support.py
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..database import get_db
from ..models import Users, Tickets, TicketCategories
from ..services.elevenlabs_service import elevenlabs_service
from ..services.enhanced_rag import enhanced_rag_service
# from .support import ApiService  # Removed problematic import
import base64
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-support", tags=["voice-support"])

# Pydantic models
class VoiceTicketRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    requester_id: int
    priority: str = "Medium"
    category_id: Optional[int] = None

class VoiceInteractionRequest(BaseModel):
    audio_data: str
    conversation_id: Optional[str] = None
    user_id: Optional[int] = None

class VoiceGuidedStepsRequest(BaseModel):
    ticket_id: int
    current_step: int = 0
    include_audio: bool = True

@router.post("/create-ticket")
async def create_ticket_from_voice(
    request: VoiceTicketRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create a support ticket from voice input"""
    
    try:
        # Step 1: Convert speech to text
        audio_bytes = base64.b64decode(request.audio_data)
        transcribed_text = await elevenlabs_service.speech_to_text(audio_bytes)
        
        # Step 2: Use AI to extract ticket information
        ticket_info = await _extract_ticket_info_from_text(transcribed_text, db)
        
        # Step 3: Search for similar issues before creating ticket
        suggestions = await enhanced_rag_service.query_with_context(
            query=transcribed_text,
            db=db,
            include_tickets=True,
            include_kb=True
        )
        
        # Step 4: If no similar solutions found, create the ticket
        if not suggestions.get("sources", {}).get("kb_articles") and \
           not suggestions.get("sources", {}).get("related_tickets"):
            
            # Create ticket using extracted information
            # from ..routers.support import ApiService  # Removed problematic import
            # from ..lib.api import CreateTicketRequest  # Removed problematic import
            
            # Create ticket directly using database
            from ..models import Tickets
            from datetime import datetime
            
            new_ticket = Tickets(
                subject=ticket_info.get("subject", "Voice-created ticket"),
                description=f"Original voice input: {transcribed_text}\n\nExtracted details:\n{ticket_info.get('description', '')}",
                priority=request.priority,
                status="Open",
                requester_id=request.requester_id,
                category_id=request.category_id or ticket_info.get("suggested_category_id"),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            db.add(new_ticket)
            await db.commit()
            await db.refresh(new_ticket)
            
            # Generate voice confirmation
            confirmation_text = f"I've created ticket #{new_ticket.ticket_id} for your {ticket_info.get('issue_type', 'issue')}. A technician will be assigned shortly."
            voice_response = await elevenlabs_service.create_voice_enabled_response(
                confirmation_text,
                include_audio=True
            )
            
            return {
                "ticket_created": True,
                "ticket": new_ticket.__dict__,
                "transcription": transcribed_text,
                "extracted_info": ticket_info,
                "voice_response": voice_response
            }
        
        else:
            # Suggest existing solutions instead
            solution_text = f"I found some existing solutions that might help with your issue. Let me share them with you."
            
            # Add specific suggestions
            if suggestions.get("sources", {}).get("kb_articles"):
                kb_article = suggestions["sources"]["kb_articles"][0]
                solution_text += f" First, check out the knowledge base article: {kb_article['title']}."
            
            if suggestions.get("sources", {}).get("related_tickets"):
                related_ticket = suggestions["sources"]["related_tickets"][0]
                solution_text += f" Also, we've resolved a similar issue before in ticket #{related_ticket['ticket_id']}."
            
            solution_text += " Would you like me to create a ticket anyway, or try these solutions first?"
            
            voice_response = await elevenlabs_service.create_voice_enabled_response(
                solution_text,
                include_audio=True
            )
            
            return {
                "ticket_created": False,
                "suggestions": suggestions,
                "transcription": transcribed_text,
                "voice_response": voice_response,
                "message": "Found existing solutions - no ticket created yet"
            }
    
    except Exception as e:
        logger.error(f"Error creating voice ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing voice ticket: {str(e)}")

@router.post("/interactive-support")
async def interactive_voice_support(
    request: VoiceInteractionRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Interactive voice support session"""
    
    try:
        # Convert speech to text
        audio_bytes = base64.b64decode(request.audio_data)
        user_input = await elevenlabs_service.speech_to_text(audio_bytes)
        
        # Get enhanced response with context
        rag_response = await enhanced_rag_service.query_with_context(
            query=user_input,
            db=db,
            include_tickets=True,
            include_kb=True
        )
        
        # Create conversational response
        response_text = await _create_conversational_response(
            user_input, 
            rag_response, 
            request.conversation_id
        )
        
        # Generate voice response
        voice_response = await elevenlabs_service.create_voice_enabled_response(
            response_text,
            include_audio=True
        )
        
        return {
            "conversation_id": request.conversation_id or "new_session",
            "user_input": user_input,
            "response": response_text,
            "voice_response": voice_response,
            "rag_context": rag_response,
            "suggested_actions": rag_response.get("suggested_actions", [])
        }
        
    except Exception as e:
        logger.error(f"Error in interactive support: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in interactive support: {str(e)}")

@router.get("/guided-resolution/{ticket_id}")
async def get_guided_resolution_steps(
    ticket_id: int,
    current_step: int = 0,
    include_audio: bool = True,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get voice-guided resolution steps for a ticket"""
    
    try:
        # Get ticket and resolution steps
        from sqlalchemy import select
        from ..models import Tickets, ResolutionSteps
        
        ticket_result = await db.execute(
            select(Tickets).where(Tickets.ticket_id == ticket_id)
        )
        ticket = ticket_result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        steps_result = await db.execute(
            select(ResolutionSteps)
            .where(ResolutionSteps.ticket_id == ticket_id)
            .order_by(ResolutionSteps.step_order)
        )
        steps = steps_result.scalars().all()
        
        if not steps:
            return {
                "ticket_id": ticket_id,
                "message": "No resolution steps available for this ticket",
                "voice_response": await elevenlabs_service.create_voice_enabled_response(
                    "No resolution steps are available for this ticket yet.",
                    include_audio=include_audio
                ) if include_audio else None
            }
        
        # Get current step
        if current_step >= len(steps):
            completion_text = f"You've completed all {len(steps)} resolution steps for ticket #{ticket_id}. The issue should now be resolved."
            return {
                "ticket_id": ticket_id,
                "completed": True,
                "total_steps": len(steps),
                "message": completion_text,
                "voice_response": await elevenlabs_service.create_voice_enabled_response(
                    completion_text,
                    include_audio=include_audio
                ) if include_audio else None
            }
        
        current_step_obj = steps[current_step]
        step_text = f"Step {current_step + 1} of {len(steps)}: {current_step_obj.instructions}"
        
        if current_step + 1 < len(steps):
            step_text += f" When you're ready, I'll guide you through the next step."
        else:
            step_text += " This is the final step."
        
        return {
            "ticket_id": ticket_id,
            "current_step": current_step,
            "total_steps": len(steps),
            "step": {
                "order": current_step_obj.step_order,
                "instructions": current_step_obj.instructions,
                "success_flag": current_step_obj.success_flag
            },
            "has_next": current_step + 1 < len(steps),
            "voice_response": await elevenlabs_service.create_voice_enabled_response(
                step_text,
                include_audio=include_audio
            ) if include_audio else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guided resolution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting guided resolution: {str(e)}")

@router.post("/elevenlabs-webhook")
async def elevenlabs_webhook(
    conversation_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Handle webhooks from ElevenLabs ConvAI"""
    
    try:
        # Log the conversation for analytics
        logger.info(f"ElevenLabs conversation event: {conversation_data.get('event_type', 'unknown')}")
        
        # Extract useful information
        conversation_id = conversation_data.get("conversation_id")
        event_type = conversation_data.get("event_type")
        
        if event_type == "conversation_ended":
            # Process completed conversation
            transcript = conversation_data.get("transcript", [])
            
            # Check if user requested ticket creation
            if any("create ticket" in msg.get("text", "").lower() or 
                   "help" in msg.get("text", "").lower() 
                   for msg in transcript if msg.get("role") == "user"):
                
                # Extract last user message for ticket creation
                user_messages = [msg for msg in transcript if msg.get("role") == "user"]
                if user_messages:
                    last_message = user_messages[-1].get("text", "")
                    
                    # Create ticket from conversation
                    # This would need to be implemented based on your specific needs
                    logger.info(f"Creating ticket from conversation: {last_message}")
        
        return {"status": "webhook_processed", "conversation_id": conversation_id}
        
    except Exception as e:
        logger.error(f"Error processing ElevenLabs webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

# Helper functions
async def _extract_ticket_info_from_text(text: str, db: AsyncSession) -> Dict[str, Any]:
    """Extract ticket information from transcribed text using AI"""
    
    from openai import AsyncOpenAI
    from ..config import settings
    
    if not settings.OPENAI_API_KEY:
        return {
            "subject": text[:50] + "..." if len(text) > 50 else text,
            "description": text,
            "issue_type": "general"
        }
    
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Get available categories for classification
    from sqlalchemy import select
    categories_result = await db.execute(select(TicketCategories))
    categories = categories_result.scalars().all()
    category_list = ", ".join([f"{cat.category_id}: {cat.name}" for cat in categories])
    
    prompt = f"""Extract ticket information from this user request:
"{text}"

Available categories: {category_list}

Return a JSON object with:
- subject: Brief descriptive title (max 100 chars)
- description: Detailed description of the issue
- issue_type: Type of issue (hardware, software, network, etc.)
- urgency_level: Low, Medium, or High based on the language used
- suggested_category_id: ID from available categories that best matches

Only return valid JSON, no other text."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"Error extracting ticket info: {str(e)}")
        return {
            "subject": text[:50] + "..." if len(text) > 50 else text,
            "description": text,
            "issue_type": "general"
        }

async def _create_conversational_response(
    user_input: str, 
    rag_response: Dict[str, Any], 
    conversation_id: Optional[str]
) -> str:
    """Create a conversational response from RAG results"""
    
    answer = rag_response.get("answer", "I'm not sure how to help with that.")
    confidence = rag_response.get("confidence", 0.5)
    
    # Make response more conversational
    if confidence > 0.8:
        conversational_response = f"I can help you with that. {answer}"
    elif confidence > 0.6:
        conversational_response = f"I think I can help. {answer} If this doesn't solve your issue, I can create a support ticket for you."
    else:
        conversational_response = f"I'm not entirely sure, but here's what I found: {answer} Would you like me to create a support ticket to get you more specific help?"
    
    # Add suggested actions
    suggested_actions = rag_response.get("suggested_actions", [])
    if suggested_actions:
        conversational_response += f" Some things you might want to try: {', '.join(suggested_actions[:2])}."
    
    return conversational_response
