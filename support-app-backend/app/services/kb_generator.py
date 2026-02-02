# app/services/kb_generator.py
"""
Knowledge Base article auto-generation service.
Generates KB article drafts from resolved tickets using Vertex AI.
"""
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from ..models import Tickets, KBArticles, KBArticleVersion, ResolutionSteps, TicketRootCauses
from ..config import settings

logger = logging.getLogger(__name__)

# Import Vertex AI (with fallback)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    logger.warning("Vertex AI not available for KB generation")


class KBGeneratorService:
    """Service for auto-generating KB articles from resolved tickets."""
    
    def __init__(self):
        self.model = None
        if VERTEXAI_AVAILABLE and settings.GOOGLE_PROJECT_ID and settings.GOOGLE_PROJECT_ID != "your-project-id":
            try:
                vertexai.init(
                    project=settings.GOOGLE_PROJECT_ID,
                    location=settings.GOOGLE_LOCATION
                )
                self.model = GenerativeModel(settings.GEMINI_MODEL)
                logger.info("✅ KB Generator initialized with Vertex AI")
            except Exception as e:
                logger.error(f"Failed to initialize KB Generator: {e}")
    
    async def generate_from_ticket(
        self,
        ticket_id: int,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Generate a KB article draft from a resolved ticket.
        
        Args:
            ticket_id: ID of the resolved ticket
            db: Database session
            user_id: User creating the article
            
        Returns:
            Dict with generated article data or error
        """
        # Fetch ticket with related data
        result = await db.execute(
            select(Tickets).where(Tickets.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return {"error": "Ticket not found", "success": False}
        
        if ticket.status != "Closed":
            return {"error": "Only closed tickets can be converted to KB articles", "success": False}
        
        # Fetch resolution steps
        steps_result = await db.execute(
            select(ResolutionSteps)
            .where(ResolutionSteps.ticket_id == ticket_id)
            .order_by(ResolutionSteps.step_order)
        )
        resolution_steps = steps_result.scalars().all()
        
        # Fetch root causes
        causes_result = await db.execute(
            select(TicketRootCauses).where(TicketRootCauses.ticket_id == ticket_id)
        )
        root_causes = causes_result.scalars().all()
        
        # Build context for generation
        context = self._build_ticket_context(ticket, resolution_steps, root_causes)
        
        # Generate article content
        article_data = await self._generate_article_content(context)
        
        if "error" in article_data:
            return article_data
        
        # Create the KB article
        kb_article = KBArticles(
            title=article_data["title"],
            summary=article_data["summary"],
            content=article_data["content"],
            version=1,
            created_by=user_id,
            created_at=datetime.utcnow(),
            auto_generated=True,
            source_ticket_id=ticket_id
        )
        
        db.add(kb_article)
        await db.commit()
        await db.refresh(kb_article)
        
        return {
            "success": True,
            "kb_id": kb_article.kb_id,
            "title": kb_article.title,
            "summary": kb_article.summary,
            "content": kb_article.content,
            "message": "KB article generated successfully"
        }
    
    def _build_ticket_context(
        self,
        ticket: Tickets,
        resolution_steps: list,
        root_causes: list
    ) -> str:
        """Build context string from ticket data for AI generation."""
        context_parts = [
            f"TICKET SUBJECT: {ticket.subject}",
            f"DESCRIPTION: {ticket.description}",
        ]
        
        if root_causes:
            context_parts.append("\nROOT CAUSES:")
            for rc in root_causes:
                context_parts.append(f"- {rc.cause_code}: {rc.description}")
        
        if resolution_steps:
            context_parts.append("\nRESOLUTION STEPS:")
            for step in resolution_steps:
                status = "✓" if step.success_flag else "•"
                context_parts.append(f"{status} Step {step.step_order}: {step.instructions}")
        
        return "\n".join(context_parts)
    
    async def _generate_article_content(self, context: str) -> Dict[str, Any]:
        """Generate KB article content using Vertex AI."""
        if not self.model:
            # Fallback to simple extraction
            return self._simple_extraction(context)
        
        prompt = f"""Based on the following resolved support ticket, create a knowledge base article.

{context}

Generate a structured KB article with:
1. A clear, searchable title (problem-focused)
2. A brief summary (2-3 sentences)
3. Detailed content in markdown format including:
   - Problem Description
   - Root Cause (if identified)
   - Solution Steps (numbered)
   - Prevention Tips (if applicable)

Respond in JSON format:
{{
    "title": "...",
    "summary": "...",
    "content": "..."
}}"""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1500
                )
            )
            
            import json
            # Extract JSON from response
            text = response.text
            # Handle potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            result = json.loads(text.strip())
            return result
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._simple_extraction(context)
    
    def _simple_extraction(self, context: str) -> Dict[str, Any]:
        """Fallback simple extraction when AI is not available."""
        lines = context.split("\n")
        title = "Knowledge Base Article"
        summary = ""
        
        for line in lines:
            if line.startswith("TICKET SUBJECT:"):
                title = f"How to resolve: {line.replace('TICKET SUBJECT:', '').strip()}"
            elif line.startswith("DESCRIPTION:"):
                summary = line.replace("DESCRIPTION:", "").strip()[:200]
        
        return {
            "title": title,
            "summary": summary or "Generated from resolved ticket",
            "content": f"# {title}\n\n## Details\n\n{context}"
        }
    
    async def create_version(
        self,
        kb_id: int,
        db: AsyncSession,
        user_id: int,
        change_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new version snapshot of a KB article."""
        result = await db.execute(
            select(KBArticles).where(KBArticles.kb_id == kb_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            return {"error": "Article not found", "success": False}
        
        # Create version snapshot
        version = KBArticleVersion(
            kb_id=kb_id,
            version=article.version,
            title=article.title,
            summary=article.summary,
            content=article.content,
            url=article.url,
            modified_by=user_id,
            modified_at=datetime.utcnow(),
            change_note=change_note
        )
        
        db.add(version)
        
        # Increment article version
        article.version += 1
        article.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "version": article.version,
            "message": f"Version {version.version} saved"
        }
    
    async def revert_to_version(
        self,
        kb_id: int,
        target_version: int,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Revert a KB article to a previous version."""
        # Find the target version
        result = await db.execute(
            select(KBArticleVersion).where(
                KBArticleVersion.kb_id == kb_id,
                KBArticleVersion.version == target_version
            )
        )
        version = result.scalar_one_or_none()
        
        if not version:
            return {"error": f"Version {target_version} not found", "success": False}
        
        # Get current article
        article_result = await db.execute(
            select(KBArticles).where(KBArticles.kb_id == kb_id)
        )
        article = article_result.scalar_one_or_none()
        
        if not article:
            return {"error": "Article not found", "success": False}
        
        # First, save current state as a new version
        await self.create_version(kb_id, db, user_id, f"Before revert to v{target_version}")
        
        # Restore from target version
        article.title = version.title
        article.summary = version.summary
        article.content = version.content
        article.url = version.url
        article.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "current_version": article.version,
            "reverted_to": target_version,
            "message": f"Reverted to version {target_version}"
        }


# Global instance
kb_generator = KBGeneratorService()
