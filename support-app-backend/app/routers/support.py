# app/routers/support.py
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..database import get_db
from ..models import Users, Tickets, TicketCategories, KBArticles, ResolutionSteps, TicketRootCauses, TicketKBLinks, Attachments

router = APIRouter(prefix="/support", tags=["support"])

# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    username: str
    email: str
    display_name: Optional[str] = None
    role: str = "end-user"

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    display_name: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: str = "Medium"
    category_id: Optional[int] = None
    external_ticket_no: Optional[str] = None
    sla_due_at: Optional[datetime] = None
    # Contact information fields
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    preferred_contact_method: Optional[str] = "email"
    # Additional context fields
    affected_system: Optional[str] = None
    business_impact: Optional[str] = None
    steps_taken: Optional[str] = None
    error_messages: Optional[str] = None

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    assigned_to: Optional[int] = None
    external_ticket_no: Optional[str] = None
    sla_due_at: Optional[datetime] = None
    # Contact information fields
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    # Additional context fields
    affected_system: Optional[str] = None
    business_impact: Optional[str] = None
    steps_taken: Optional[str] = None
    error_messages: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: int
    external_ticket_no: Optional[str]
    subject: Optional[str]
    description: Optional[str]
    priority: str
    status: str
    created_at: datetime
    requester: UserResponse
    category: Optional[str] = None

    class Config:
        from_attributes = True

# New KB Management Models
class KBArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    url: Optional[str] = None
    category_ids: Optional[List[int]] = []

class KBArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None

class KBArticleResponse(BaseModel):
    kb_id: int
    title: str
    summary: Optional[str]
    content: Optional[str] = None  # Don't include full content in list responses
    url: Optional[str]
    created_by: int
    creator_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    linked_tickets_count: Optional[int] = 0

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    category_id: int
    name: str
    description: Optional[str]
    tickets_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Root Cause Management Models
class RootCauseCreate(BaseModel):
    ticket_id: int
    cause_code: Optional[str] = None
    description: str

class RootCauseUpdate(BaseModel):
    cause_code: Optional[str] = None
    description: Optional[str] = None

class RootCauseResponse(BaseModel):
    rootcause_id: int
    ticket_id: int
    cause_code: Optional[str]
    description: str
    identified_at: datetime

    class Config:
        from_attributes = True

# Search and Suggestion Models
class TicketSearchRequest(BaseModel):
    query: str
    category_id: Optional[int] = None
    limit: int = 5

class TicketSuggestionResponse(BaseModel):
    similar_tickets: List[TicketResponse]
    related_kb_articles: List[KBArticleResponse]
    suggestions: List[str]

    class Config:
        from_attributes = True

# Resolution Steps Management Models
class ResolutionStepCreate(BaseModel):
    instructions: str
    step_order: int
    performed_by: Optional[int] = None

class ResolutionStepUpdate(BaseModel):
    instructions: Optional[str] = None
    success_flag: Optional[bool] = None
    performed_by: Optional[int] = None
    performed_at: Optional[datetime] = None

class ResolutionStepResponse(BaseModel):
    step_id: int
    ticket_id: int
    step_order: int
    instructions: str
    success_flag: Optional[bool]
    performed_by: Optional[int]
    performer_name: Optional[str]
    performed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Attachment Management Models
class AttachmentResponse(BaseModel):
    attachment_id: int
    ticket_id: int
    filename: Optional[str]
    file_url: Optional[str]
    uploaded_by: Optional[int]
    uploader_name: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

# User Management Endpoints
@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    try:
        db_user = Users(
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            role=user.role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all users, optionally filtered by role"""
    try:
        query = select(Users)
        if role:
            query = query.where(Users.role == role)
        
        result = await db.execute(query)
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific user by ID"""
    try:
        result = await db.execute(select(Users).where(Users.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user's information"""
    try:
        result = await db.execute(select(Users).where(Users.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user fields
        user.username = user_update.username
        user.email = user_update.email
        user.display_name = user_update.display_name
        user.role = user_update.role
        
        await db.commit()
        await db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating user: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a user (only if they have no associated tickets)"""
    try:
        # Check if user has any tickets
        ticket_count_result = await db.execute(
            select(func.count(Tickets.ticket_id)).where(
                or_(
                    Tickets.requester_id == user_id,
                    Tickets.assigned_to_id == user_id
                )
            )
        )
        ticket_count = ticket_count_result.scalar()
        
        if ticket_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete user: they have {ticket_count} associated tickets"
            )
        
        # Check if user has created KB articles
        kb_count_result = await db.execute(
            select(func.count(KBArticles.kb_id)).where(KBArticles.created_by == user_id)
        )
        kb_count = kb_count_result.scalar()
        
        if kb_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete user: they have created {kb_count} KB articles"
            )
        
        # Delete the user
        result = await db.execute(select(Users).where(Users.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.delete(user)
        await db.commit()
        return {"message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

# Ticket Management Endpoints
@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate, 
    requester_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a new support ticket with enhanced schema support"""
    try:
        # Verify requester exists
        requester_result = await db.execute(select(Users).where(Users.user_id == requester_id))
        requester = requester_result.scalar_one_or_none()
        if not requester:
            raise HTTPException(status_code=404, detail="Requester not found")
        
        # Build enhanced description with structured data
        enhanced_description = ticket.description
        
        # Add structured information sections
        if ticket.affected_system or ticket.business_impact or ticket.steps_taken or ticket.error_messages:
            enhanced_description += "\n\n=== ADDITIONAL INFORMATION ==="
            
            if ticket.affected_system:
                enhanced_description += f"\n📱 Affected System: {ticket.affected_system}"
            
            if ticket.business_impact:
                enhanced_description += f"\n📊 Business Impact: {ticket.business_impact}"
            
            if ticket.steps_taken:
                enhanced_description += f"\n🔧 Steps Already Taken:\n{ticket.steps_taken}"
            
            if ticket.error_messages:
                enhanced_description += f"\n❌ Error Messages:\n{ticket.error_messages}"
        
        # Add contact information
        if ticket.contact_phone or ticket.contact_email:
            enhanced_description += "\n\n=== CONTACT INFORMATION ==="
            enhanced_description += f"\n📞 Preferred Contact: {ticket.preferred_contact_method}"
            
            if ticket.contact_phone:
                enhanced_description += f"\n📱 Phone: {ticket.contact_phone}"
            
            if ticket.contact_email:
                enhanced_description += f"\n📧 Email: {ticket.contact_email}"
        
        # Calculate SLA due date if not provided
        sla_due_at = ticket.sla_due_at
        if not sla_due_at:
            # Calculate based on priority
            from datetime import datetime, timedelta
            hours_map = {
                "Critical": 4,
                "High": 8, 
                "Medium": 24,
                "Low": 72
            }
            hours = hours_map.get(ticket.priority, 24)
            sla_due_at = datetime.utcnow() + timedelta(hours=hours)
        
        db_ticket = Tickets(
            subject=ticket.subject,
            description=enhanced_description,
            priority=ticket.priority,
            status="Open",
            requester_id=requester_id,
            category_id=ticket.category_id,
            external_ticket_no=ticket.external_ticket_no,
            sla_due_at=sla_due_at
        )
        db.add(db_ticket)
        await db.commit()
        await db.refresh(db_ticket)
        
        # Fetch with relationships
        result = await db.execute(
            select(Tickets)
            .options(selectinload(Tickets.requester), selectinload(Tickets.category))
            .where(Tickets.ticket_id == db_ticket.ticket_id)
        )
        ticket_with_relations = result.scalar_one()
        
        return TicketResponse(
            ticket_id=ticket_with_relations.ticket_id,
            external_ticket_no=ticket_with_relations.external_ticket_no,
            subject=ticket_with_relations.subject,
            description=ticket_with_relations.description,
            priority=ticket_with_relations.priority,
            status=ticket_with_relations.status,
            created_at=ticket_with_relations.created_at,
            requester=ticket_with_relations.requester,
            category=ticket_with_relations.category.name if ticket_with_relations.category else None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")

@router.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    category_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List tickets with optional filtering"""
    try:
        query = select(Tickets).options(
            selectinload(Tickets.requester),
            selectinload(Tickets.category),
            selectinload(Tickets.assigned_to)
        )
        
        # Apply filters
        conditions = []
        if status:
            conditions.append(Tickets.status == status)
        if priority:
            conditions.append(Tickets.priority == priority)
        if assigned_to:
            conditions.append(Tickets.assigned_to_id == assigned_to)
        if category_id:
            conditions.append(Tickets.category_id == category_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Tickets.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        tickets = result.scalars().all()
        
        return [
            TicketResponse(
                ticket_id=ticket.ticket_id,
                external_ticket_no=ticket.external_ticket_no,
                subject=ticket.subject,
                description=ticket.description,
                priority=ticket.priority,
                status=ticket.status,
                created_at=ticket.created_at,
                requester=ticket.requester,
                category=ticket.category.name if ticket.category else None
            )
            for ticket in tickets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tickets: {str(e)}")

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific ticket by ID"""
    try:
        result = await db.execute(
            select(Tickets)
            .options(
                selectinload(Tickets.requester),
                selectinload(Tickets.category),
                selectinload(Tickets.assigned_to),
                selectinload(Tickets.resolution_steps),
                selectinload(Tickets.root_causes)
            )
            .where(Tickets.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            external_ticket_no=ticket.external_ticket_no,
            subject=ticket.subject,
            description=ticket.description,
            priority=ticket.priority,
            status=ticket.status,
            created_at=ticket.created_at,
            requester=ticket.requester,
            category=ticket.category.name if ticket.category else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ticket: {str(e)}")

@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    updates: TicketUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a ticket"""
    try:
        result = await db.execute(select(Tickets).where(Tickets.ticket_id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Apply updates
        if updates.status is not None:
            ticket.status = updates.status
            if updates.status == "Closed":
                ticket.closed_at = func.now()
        
        if updates.assigned_to_id is not None:
            ticket.assigned_to_id = updates.assigned_to_id
        
        if updates.priority is not None:
            ticket.priority = updates.priority
        
        await db.commit()
        return {"message": "Ticket updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

# ===== KNOWLEDGE BASE MANAGEMENT ENDPOINTS =====

@router.post("/kb-articles", response_model=KBArticleResponse)
async def create_kb_article(
    article: KBArticleCreate,
    created_by: int = Query(..., description="User ID of the creator"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge base article"""
    try:
        # Create new KB article
        new_article = KBArticles(
            title=article.title,
            summary=article.summary,
            url=article.url,
            created_by=created_by,
            updated_at=datetime.now()
        )
        
        db.add(new_article)
        await db.commit()
        await db.refresh(new_article)
        
        # Get creator info
        creator_result = await db.execute(
            select(Users.display_name).where(Users.user_id == created_by)
        )
        creator_name = creator_result.scalar()
        
        return KBArticleResponse(
            kb_id=new_article.kb_id,
            title=new_article.title,
            summary=new_article.summary,
            url=new_article.url,
            created_by=new_article.created_by,
            creator_name=creator_name,
            created_at=new_article.created_at,
            updated_at=new_article.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating KB article: {str(e)}")

@router.get("/kb-articles", response_model=List[KBArticleResponse])
async def get_kb_articles(
    limit: int = Query(20, description="Number of articles to retrieve"),
    offset: int = Query(0, description="Number of articles to skip"),
    search: Optional[str] = Query(None, description="Search term for title/summary"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of knowledge base articles"""
    try:
        # Build query
        query = select(
            KBArticles,
            Users.display_name.label('creator_name'),
            func.count(TicketKBLinks.kb_id).label('linked_tickets_count')
        ).join(
            Users, KBArticles.created_by == Users.user_id
        ).outerjoin(
            TicketKBLinks, KBArticles.kb_id == TicketKBLinks.kb_id
        ).group_by(KBArticles.kb_id, Users.display_name)
        
        # Add search filter if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    KBArticles.title.ilike(search_pattern),
                    KBArticles.summary.ilike(search_pattern)
                )
            )
        
        # Add pagination
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        articles_data = result.fetchall()
        
        articles = []
        for row in articles_data:
            article = row[0]  # KBArticles object
            creator_name = row[1]
            linked_count = row[2] or 0
            
            articles.append(KBArticleResponse(
                kb_id=article.kb_id,
                title=article.title,
                summary=article.summary,
                url=article.url,
                created_by=article.created_by,
                creator_name=creator_name,
                created_at=article.created_at,
                updated_at=article.updated_at,
                linked_tickets_count=linked_count
            ))
        
        return articles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KB articles: {str(e)}")

@router.get("/kb-articles/{kb_id}", response_model=KBArticleResponse)
async def get_kb_article(kb_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific knowledge base article with full content"""
    try:
        result = await db.execute(
            select(KBArticles, Users.display_name.label('creator_name'))
            .join(Users, KBArticles.created_by == Users.user_id)
            .where(KBArticles.kb_id == kb_id)
        )
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="KB article not found")
        
        article = row[0]
        creator_name = row[1]
        
        # Get linked tickets count
        linked_count_result = await db.execute(
            select(func.count(TicketKBLinks.kb_id))
            .where(TicketKBLinks.kb_id == kb_id)
        )
        linked_count = linked_count_result.scalar() or 0
        
        return KBArticleResponse(
            kb_id=article.kb_id,
            title=article.title,
            summary=article.summary,
            content=article.url,  # For now, treating URL as content - you may want to store actual content
            url=article.url,
            created_by=article.created_by,
            creator_name=creator_name,
            created_at=article.created_at,
            updated_at=article.updated_at,
            linked_tickets_count=linked_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KB article: {str(e)}")

@router.put("/kb-articles/{kb_id}", response_model=KBArticleResponse)
async def update_kb_article(
    kb_id: int,
    updates: KBArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a knowledge base article"""
    try:
        # Get existing article
        result = await db.execute(
            select(KBArticles).where(KBArticles.kb_id == kb_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="KB article not found")
        
        # Update fields
        if updates.title is not None:
            article.title = updates.title
        if updates.summary is not None:
            article.summary = updates.summary
        if updates.content is not None:
            article.url = updates.content  # Storing as URL for now
        if updates.url is not None:
            article.url = updates.url
            
        article.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(article)
        
        # Get creator info
        creator_result = await db.execute(
            select(Users.display_name).where(Users.user_id == article.created_by)
        )
        creator_name = creator_result.scalar()
        
        return KBArticleResponse(
            kb_id=article.kb_id,
            title=article.title,
            summary=article.summary,
            url=article.url,
            created_by=article.created_by,
            creator_name=creator_name,
            created_at=article.created_at,
            updated_at=article.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating KB article: {str(e)}")

@router.delete("/kb-articles/{kb_id}")
async def delete_kb_article(kb_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a knowledge base article"""
    try:
        # Check if article exists
        result = await db.execute(
            select(KBArticles).where(KBArticles.kb_id == kb_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="KB article not found")
        
        # Delete linked tickets first (foreign key constraint)
        await db.execute(
            text("DELETE FROM ticketkblinks WHERE kb_id = :kb_id"),
            {"kb_id": kb_id}
        )
        
        # Delete the article
        await db.delete(article)
        await db.commit()
        
        return {"message": "KB article deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting KB article: {str(e)}")

# ===== ENHANCED TICKET WORKFLOW ENDPOINTS =====

@router.post("/tickets/search-suggestions", response_model=TicketSuggestionResponse)
async def search_ticket_suggestions(
    search_request: TicketSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search for existing tickets and KB articles before creating a new ticket"""
    try:
        search_pattern = f"%{search_request.query}%"
        
        # Search similar tickets
        ticket_query = select(Tickets, Users.display_name.label('requester_name')).join(
            Users, Tickets.requester_id == Users.user_id
        ).where(
            or_(
                Tickets.subject.ilike(search_pattern),
                Tickets.description.ilike(search_pattern)
            )
        )
        
        if search_request.category_id:
            ticket_query = ticket_query.where(Tickets.category_id == search_request.category_id)
            
        ticket_query = ticket_query.limit(search_request.limit)
        
        ticket_results = await db.execute(ticket_query)
        similar_tickets = []
        
        for row in ticket_results.fetchall():
            ticket = row[0]
            requester_name = row[1]
            
            similar_tickets.append(TicketResponse(
                ticket_id=ticket.ticket_id,
                external_ticket_no=ticket.external_ticket_no,
                subject=ticket.subject,
                description=ticket.description,
                priority=ticket.priority,
                status=ticket.status,
                created_at=ticket.created_at,
                requester=UserResponse(
                    user_id=ticket.requester_id,
                    username="",  # We don't need full user data for suggestions
                    email="",
                    display_name=requester_name,
                    role="",
                    created_at=ticket.created_at
                )
            ))
        
        # Search KB articles
        kb_query = select(KBArticles, Users.display_name.label('creator_name')).join(
            Users, KBArticles.created_by == Users.user_id
        ).where(
            or_(
                KBArticles.title.ilike(search_pattern),
                KBArticles.summary.ilike(search_pattern)
            )
        ).limit(search_request.limit)
        
        kb_results = await db.execute(kb_query)
        relevant_articles = []
        
        for row in kb_results.fetchall():
            article = row[0]
            creator_name = row[1]
            
            relevant_articles.append(KBArticleResponse(
                kb_id=article.kb_id,
                title=article.title,
                summary=article.summary,
                url=article.url,
                created_by=article.created_by,
                creator_name=creator_name,
                created_at=article.created_at,
                updated_at=article.updated_at
            ))
        
        return TicketSuggestionResponse(
            similar_tickets=similar_tickets,
            related_kb_articles=relevant_articles,
            suggestions=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching suggestions: {str(e)}")

@router.post("/tickets/{ticket_id}/generate-kb", response_model=KBArticleResponse)
async def generate_kb_from_ticket(
    ticket_id: int,
    created_by: int = Query(..., description="User ID creating the KB article"),
    db: AsyncSession = Depends(get_db)
):
    """Auto-generate a KB article from a resolved ticket"""
    try:
        # Get ticket with resolution steps
        ticket_result = await db.execute(
            select(Tickets)
            .options(selectinload(Tickets.resolution_steps))
            .options(selectinload(Tickets.root_causes))
            .options(selectinload(Tickets.category))
            .where(Tickets.ticket_id == ticket_id)
        )
        
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket.status != "Closed":
            raise HTTPException(status_code=400, detail="Can only generate KB from closed tickets")
        
        # Generate KB article content
        category_name = ticket.category.name if ticket.category else "General"
        
        # Build title
        kb_title = f"How to resolve: {ticket.subject}"
        
        # Build summary from root causes
        root_cause_text = ""
        if ticket.root_causes:
            causes = [rc.description for rc in ticket.root_causes if rc.description]
            root_cause_text = " Root causes: " + "; ".join(causes)
        
        kb_summary = f"Resolution guide for {category_name} issue.{root_cause_text}"
        
        # Build content from resolution steps
        steps_content = []
        if ticket.resolution_steps:
            sorted_steps = sorted(ticket.resolution_steps, key=lambda x: x.step_order)
            for i, step in enumerate(sorted_steps, 1):
                steps_content.append(f"{i}. {step.instructions}")
        
        content = f"""
# Problem Description
{ticket.description}

# Resolution Steps
{chr(10).join(steps_content) if steps_content else "No resolution steps documented."}

# Additional Notes
This article was auto-generated from ticket #{ticket.ticket_id}.
Category: {category_name}
Resolved on: {ticket.closed_at.strftime('%Y-%m-%d') if ticket.closed_at else 'Unknown'}
        """.strip()
        
        # Create KB article
        new_kb = KBArticles(
            title=kb_title,
            summary=kb_summary,
            url=content,  # Storing content in URL field for now
            created_by=created_by,
            updated_at=datetime.now()
        )
        
        db.add(new_kb)
        await db.commit()
        await db.refresh(new_kb)
        
        # Link the KB article to the original ticket
        kb_link = TicketKBLinks(ticket_id=ticket_id, kb_id=new_kb.kb_id)
        db.add(kb_link)
        await db.commit()
        
        # Get creator info
        creator_result = await db.execute(
            select(Users.display_name).where(Users.user_id == created_by)
        )
        creator_name = creator_result.scalar()
        
        return KBArticleResponse(
            kb_id=new_kb.kb_id,
            title=new_kb.title,
            summary=new_kb.summary,
            content=new_kb.url,
            url=new_kb.url,
            created_by=new_kb.created_by,
            creator_name=creator_name,
            created_at=new_kb.created_at,
            updated_at=new_kb.updated_at,
            linked_tickets_count=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating KB article: {str(e)}")

# ===== CATEGORY MANAGEMENT ENDPOINTS =====

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new ticket category"""
    try:
        new_category = TicketCategories(
            name=category.name,
            description=category.description
        )
        
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        
        return CategoryResponse(
            category_id=new_category.category_id,
            name=new_category.name,
            description=new_category.description,
            tickets_count=0
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all ticket categories with ticket counts"""
    try:
        result = await db.execute(
            select(
                TicketCategories,
                func.count(Tickets.ticket_id).label('tickets_count')
            )
            .outerjoin(Tickets, TicketCategories.category_id == Tickets.category_id)
            .group_by(TicketCategories.category_id)
            .order_by(TicketCategories.name)
        )
        
        categories = []
        for row in result.fetchall():
            category = row[0]
            ticket_count = row[1] or 0
            
            categories.append(CategoryResponse(
                category_id=category.category_id,
                name=category.name,
                description=category.description,
                tickets_count=ticket_count
            ))
        
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

# ===== EXISTING ENDPOINTS =====
# (Keep all the existing endpoints from the original file)

# ===== KB VERSIONING & AUTO-GENERATION ENDPOINTS =====

class KBVersionResponse(BaseModel):
    version: int
    title: str
    summary: Optional[str]
    modified_by: int
    modified_at: datetime
    change_note: Optional[str]
    
    class Config:
        from_attributes = True


class KBGenerateRequest(BaseModel):
    ticket_id: int
    user_id: int


@router.get("/kb/{kb_id}/versions")
async def get_kb_versions(
    kb_id: int,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get version history for a KB article."""
    from ..models import KBArticleVersion
    
    result = await db.execute(
        select(KBArticleVersion)
        .where(KBArticleVersion.kb_id == kb_id)
        .order_by(KBArticleVersion.version.desc())
    )
    versions = result.scalars().all()
    
    return [
        {
            "version": v.version,
            "title": v.title,
            "summary": v.summary,
            "modified_by": v.modified_by,
            "modified_at": v.modified_at.isoformat() if v.modified_at else None,
            "change_note": v.change_note
        }
        for v in versions
    ]


@router.post("/kb/{kb_id}/version")
async def create_kb_version(
    kb_id: int,
    user_id: int = Query(...),
    change_note: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new version snapshot of a KB article."""
    from ..services.kb_generator import kb_generator
    
    result = await kb_generator.create_version(kb_id, db, user_id, change_note)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/kb/{kb_id}/revert/{target_version}")
async def revert_kb_version(
    kb_id: int,
    target_version: int,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Revert a KB article to a previous version."""
    from ..services.kb_generator import kb_generator
    
    result = await kb_generator.revert_to_version(kb_id, target_version, db, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/kb/generate-from-ticket/{ticket_id}")
async def generate_kb_from_ticket(
    ticket_id: int,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Auto-generate a KB article from a resolved ticket.
    Uses Vertex AI to create structured content from ticket data.
    """
    from ..services.kb_generator import kb_generator
    
    result = await kb_generator.generate_from_ticket(ticket_id, db, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
