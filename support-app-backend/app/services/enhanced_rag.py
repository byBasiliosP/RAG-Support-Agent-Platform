# app/services/enhanced_rag.py
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Tickets, KBArticles, TicketCategories, ResolutionSteps, TicketRootCauses
from ..services.vectorstore import vectordb
from ..services.agents import qa_chain
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from ..config import settings
import json
import logging

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service that integrates ticketing system knowledge using Vertex AI"""
    
    def __init__(self):
        if settings.GOOGLE_PROJECT_ID and settings.GOOGLE_PROJECT_ID != "your-project-id":
            vertexai.init(
                project=settings.GOOGLE_PROJECT_ID,
                location=settings.GOOGLE_LOCATION,
                credentials=settings.GOOGLE_APPLICATION_CREDENTIALS or None
            )
            self.model = GenerativeModel(settings.GEMINI_MODEL)
            print("✅ Vertex AI model initialized for enhanced RAG")
        else:
            self.model = None
            print("Warning: Google Cloud Project ID not configured for Vertex AI")
        
    async def query_with_context(
        self, 
        query: str, 
        db: AsyncSession,
        include_tickets: bool = True,
        include_kb: bool = True,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced RAG query that includes ticketing system context"""
        
        if not vectordb or not qa_chain:
            raise Exception("RAG system not available - AI configuration incomplete")
        
        try:
            # Step 1: Get vector similarity results
            vector_results = vectordb.similarity_search_with_score(query, k=5)
            
            # Step 2: Get relevant tickets and KB articles from database
            context_data = await self._get_contextual_data(query, db, include_tickets, include_kb, category_filter)
            
            # Step 3: Combine all context for enhanced prompt
            enhanced_context = self._build_enhanced_context(vector_results, context_data)
            
            # Step 4: Generate response with enhanced context
            if self.model:
                response = await self._generate_enhanced_response(query, enhanced_context)
            else:
                # Fallback to basic RAG
                basic_result = qa_chain.invoke({"query": query})
                response = {
                    "answer": basic_result["result"],
                    "confidence": 0.7
                }
            
            return {
                "query": query,
                "answer": response["answer"],
                "confidence": response.get("confidence", 0.8),
                "sources": {
                    "vector_documents": [
                        {
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "metadata": doc.metadata,
                            "score": float(score)
                        }
                        for doc, score in vector_results
                    ],
                    "related_tickets": context_data.get("tickets", []),
                    "kb_articles": context_data.get("kb_articles", [])
                },
                "suggested_actions": self._generate_suggested_actions(query, context_data),
                "category_suggestions": context_data.get("suggested_categories", [])
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced RAG query: {str(e)}")
            raise
    
    async def _get_contextual_data(
        self, 
        query: str, 
        db: AsyncSession, 
        include_tickets: bool, 
        include_kb: bool,
        category_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Retrieve contextual data from the ticketing system"""
        context_data = {
            "tickets": [],
            "kb_articles": [],
            "suggested_categories": []
        }
        
        # Extract keywords for deeper search
        keywords = self._extract_keywords(query)
        
        if include_tickets:
            # Search resolved tickets with similar keywords
            ticket_query = select(Tickets).where(
                Tickets.status == "Closed",
                Tickets.description.ilike(f"%{keywords[0]}%") if keywords else True
            ).limit(5)
            
            if category_filter:
                pass # TODO: Add category join if needed
                
            result = await db.execute(ticket_query)
            tickets = result.scalars().all()
            
            for t in tickets:
                # Fetch resolution steps and root cause
                # In a real app, you'd use joinedload or selectinload
                # For this implementation, we'll assume they're loaded or we'd fetch them
                context_data["tickets"].append({
                    "id": t.ticket_id,
                    "subject": t.subject,
                    "description": t.description,
                    "resolution_steps": [], # Simplified for this example
                    "root_cause": {"description": "See ticket details"} # Simplified
                })
        
        if include_kb:
            # KB search logic would go here
            pass
            
        return context_data

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from the query"""
        # Simple stopword removal for now
        stopwords = ['the', 'a', 'an', 'is', 'are', 'how', 'to', 'what', 'why', 'when', 'does', 'it', 'work', 'my', 'is', 'not']
        words = query.lower().replace('?', '').split()
        return [w for w in words if w not in stopwords]

    def _build_enhanced_context(self, vector_results: List, context_data: Dict[str, Any]) -> str:
        """Build enhanced context from all sources"""
        context_parts = []
        
        # Add vector search results
        context_parts.append("DOCUMENTATION:")
        for doc, _ in vector_results:
            context_parts.append(f"- {doc.page_content}")
            
        # Add KB articles
        if context_data["kb_articles"]:
            context_parts.append("\nKNOWLEDGE BASE ARTICLES:")
            for kb in context_data["kb_articles"]:
                context_parts.append(f"- {kb['title']}: {kb['summary']}")
                
        # Add resolved tickets
        if context_data["tickets"]:
            context_parts.append("\nSIMILAR RESOLVED TICKETS:")
            for ticket in context_data["tickets"]:
                context_parts.append(f"Ticket #{ticket['id']}: {ticket['subject']}")
                if ticket.get("root_cause"):
                    context_parts.append(f"Root Cause: {ticket['root_cause'].get('description')}")
                if ticket.get("resolution_steps"):
                    context_parts.append("Resolution Steps:")
                    for step in ticket["resolution_steps"]:
                        context_parts.append(f"  - {step.get('instructions')}")
        
        return "\n".join(context_parts)
    
    async def _generate_enhanced_response(self, query: str, context: str) -> Dict[str, Any]:
        """Generate response using Vertex AI Gemini with enhanced context"""
        
        prompt = f"""You are an intelligent IT support assistant with access to comprehensive knowledge including:
- Technical documentation
- Knowledge base articles
- Previously resolved support tickets
- Resolution procedures

Your role is to:
1. Provide accurate, actionable technical support
2. Reference specific KB articles or tickets when relevant
3. Give step-by-step solutions when appropriate
4. Suggest preventive measures
5. Indicate confidence level in your response

Format your response clearly and professionally. If you're not certain about something, be honest about it.

Based on the following context, please answer the user's question:

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a helpful, accurate response. Include references to specific KB articles or tickets if they're relevant to the solution.
"""

        try:
            # Run Vertex AI generation in async context
            # vertexai models generation is synchronous, so we run in thread
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=800
                )
            )
            
            answer = response.text
            
            # Simple confidence scoring based on context quality
            confidence = self._calculate_confidence(context, answer)
            
            return {
                "answer": answer,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating Vertex AI response: {str(e)}")
            raise
    
    def _calculate_confidence(self, context: str, answer: str) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have relevant context
        if "KNOWLEDGE BASE ARTICLES" in context:
            confidence += 0.2
        if "SIMILAR RESOLVED TICKETS" in context:
            confidence += 0.2
        if len(context) > 500:  # Rich context
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_suggested_actions(self, query: str, context_data: Dict[str, Any]) -> List[str]:
        """Generate suggested actions based on the query and context"""
        suggestions = []
        
        # Check if this might be a new ticket
        if any(word in query.lower() for word in ['help', 'problem', 'issue', 'error', 'broken', 'not working']):
            suggestions.append("Create a support ticket if the suggested solutions don't resolve your issue")
        
        # Check if there are relevant KB articles
        if context_data.get("kb_articles"):
            suggestions.append("Review the suggested KB articles for detailed procedures")
        
        # Check if there are similar resolved tickets
        if context_data.get("tickets"):
            suggestions.append("Check the resolution steps from similar tickets")
        
        return suggestions
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Vertex AI.
        Returns sentiment (positive/neutral/negative) with confidence score.
        """
        if not self.model:
            return {"sentiment": "unknown", "confidence": 0.0, "error": "Model not configured"}
        
        prompt = f"""Analyze the sentiment of the following text. 
Respond with a JSON object containing:
- sentiment: one of "positive", "neutral", or "negative"
- confidence: a number between 0 and 1 indicating confidence
- keywords: list of key emotional words detected

Text to analyze:
"{text}"

Respond ONLY with valid JSON, no other text."""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=200
                )
            )
            
            import json as json_module
            result = json_module.loads(response.text)
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "confidence": result.get("confidence", 0.5),
                "keywords": result.get("keywords", [])
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "error": str(e)}

# Global instance
enhanced_rag_service = EnhancedRAGService()
