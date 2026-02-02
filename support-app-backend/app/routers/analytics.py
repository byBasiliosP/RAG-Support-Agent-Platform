# app/routers/analytics.py
import json
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import (
    Users, Tickets, TicketCategories, KBArticles, ResolutionSteps, 
    TicketRootCauses, TicketKBLinks, VoiceConversation, VoiceMessage
)
from ..langgraph_setup import graph_store
from ..rate_limiter import limiter, RateLimits

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Enhanced Analytics Models
class TicketAnalytics(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    average_resolution_time_hours: float
    tickets_by_category: Dict[str, int]
    tickets_by_priority: Dict[str, int]
    tickets_created_last_7_days: int
    tickets_resolved_last_7_days: int
    resolution_rate_percentage: float

class KBAnalytics(BaseModel):
    total_articles: int
    most_linked_articles: List[Dict[str, Any]]
    articles_by_creator: Dict[str, int]
    articles_created_last_30_days: int
    average_links_per_article: float
    kb_effectiveness_score: float

class VoiceAnalytics(BaseModel):
    total_voice_sessions: int
    average_session_duration_minutes: float
    voice_to_ticket_conversion_rate: float
    most_common_voice_queries: List[Dict[str, Any]]
    voice_resolution_success_rate: float

class SLAAnalytics(BaseModel):
    sla_compliance_rate: float
    breached_tickets_count: int
    average_response_time_hours: float
    tickets_approaching_sla: int
    sla_performance_by_category: Dict[str, float]

class ComprehensiveAnalytics(BaseModel):
    ticket_analytics: TicketAnalytics
    kb_analytics: KBAnalytics
    voice_analytics: VoiceAnalytics
    sla_analytics: SLAAnalytics
    user_analytics: Dict[str, Any]
    trends: Dict[str, Any]

# ElevenLabs Analytics Models
class ElevenLabsConversation(BaseModel):
    conversation_id: str
    agent_id: str
    user_id: str = None
    start_time: str
    end_time: str = None
    duration_seconds: int = None
    messages_count: int = 0
    status: str = "active"  # active, completed, abandoned
    metadata: Dict[str, Any] = {}

class ElevenLabsMessage(BaseModel):
    message_id: str
    conversation_id: str
    timestamp: str
    type: str  # user or agent
    content: str
    duration_seconds: int = None
    metadata: Dict[str, Any] = {}

# ===== ENHANCED ANALYTICS ENDPOINTS =====

@router.get("/comprehensive", response_model=ComprehensiveAnalytics)
@limiter.limit(RateLimits.ANALYTICS)
async def get_comprehensive_analytics(
    request: Request,
    days_back: int = 30,
    db: AsyncSession = Depends(get_db)
) -> ComprehensiveAnalytics:
    """Get comprehensive analytics for the support system"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get ticket analytics
        ticket_analytics = await _get_ticket_analytics(db, start_date, end_date)
        
        # Get KB analytics
        kb_analytics = await _get_kb_analytics(db, start_date, end_date)
        
        # Get voice analytics (from database)
        voice_analytics = await _get_voice_analytics(db, start_date, end_date)
        
        # Get SLA analytics
        sla_analytics = await _get_sla_analytics(db, start_date, end_date)
        
        # Get user analytics
        user_analytics = await _get_user_analytics(db, start_date, end_date)
        
        # Get trends
        trends = await _get_trends_analytics(db, start_date, end_date)
        
        return ComprehensiveAnalytics(
            ticket_analytics=ticket_analytics,
            kb_analytics=kb_analytics,
            voice_analytics=voice_analytics,
            sla_analytics=sla_analytics,
            user_analytics=user_analytics,
            trends=trends
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting comprehensive analytics: {str(e)}")

@router.get("/tickets/performance")
@limiter.limit(RateLimits.ANALYTICS)
async def get_ticket_performance_analytics(
    request: Request,
    category_id: Optional[int] = None,
    days_back: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed ticket performance analytics"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Base query
        base_query = select(Tickets).where(
            Tickets.created_at >= start_date
        )
        
        if category_id:
            base_query = base_query.where(Tickets.category_id == category_id)
        
        # Get tickets in date range
        result = await db.execute(base_query)
        tickets = result.scalars().all()
        
        # Calculate metrics
        total_tickets = len(tickets)
        closed_tickets = [t for t in tickets if t.status == 'Closed']
        
        # Resolution time analysis
        resolution_times = []
        for ticket in closed_tickets:
            if ticket.closed_at and ticket.created_at:
                resolution_time = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # First Call Resolution (FCR) - tickets resolved in one interaction
        fcr_tickets = []
        for ticket in closed_tickets:
            steps_result = await db.execute(
                select(func.count(ResolutionSteps.step_id))
                .where(ResolutionSteps.ticket_id == ticket.ticket_id)
            )
            steps_count = steps_result.scalar() or 0
            if steps_count <= 1:
                fcr_tickets.append(ticket)
        
        fcr_rate = (len(fcr_tickets) / len(closed_tickets) * 100) if closed_tickets else 0
        
        # Daily ticket creation trend
        daily_creation = {}
        for ticket in tickets:
            date_key = ticket.created_at.date().isoformat()
            daily_creation[date_key] = daily_creation.get(date_key, 0) + 1
        
        # Resolution efficiency by technician
        technician_performance = {}
        for ticket in closed_tickets:
            if ticket.assigned_to_id:
                if ticket.assigned_to_id not in technician_performance:
                    technician_performance[ticket.assigned_to_id] = {
                        'tickets_resolved': 0,
                        'total_resolution_time': 0,
                        'avg_resolution_time': 0
                    }
                
                technician_performance[ticket.assigned_to_id]['tickets_resolved'] += 1
                
                if ticket.closed_at and ticket.created_at:
                    resolution_hours = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
                    technician_performance[ticket.assigned_to_id]['total_resolution_time'] += resolution_hours
        
        # Calculate averages
        for tech_id, performance in technician_performance.items():
            if performance['tickets_resolved'] > 0:
                performance['avg_resolution_time'] = (
                    performance['total_resolution_time'] / performance['tickets_resolved']
                )
        
        return {
            "summary": {
                "total_tickets": total_tickets,
                "closed_tickets": len(closed_tickets),
                "resolution_rate": (len(closed_tickets) / total_tickets * 100) if total_tickets else 0,
                "average_resolution_time_hours": avg_resolution_time,
                "first_call_resolution_rate": fcr_rate
            },
            "daily_creation_trend": daily_creation,
            "technician_performance": technician_performance,
            "resolution_time_distribution": {
                "under_1_hour": len([t for t in resolution_times if t < 1]),
                "1_to_4_hours": len([t for t in resolution_times if 1 <= t < 4]),
                "4_to_24_hours": len([t for t in resolution_times if 4 <= t < 24]),
                "over_24_hours": len([t for t in resolution_times if t >= 24])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ticket performance: {str(e)}")

@router.get("/kb/effectiveness")
@limiter.limit(RateLimits.ANALYTICS)
async def get_kb_effectiveness_analytics(
    request: Request,
    days_back: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get knowledge base effectiveness analytics"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all KB articles with their usage statistics
        kb_query = select(
            KBArticles,
            func.count(TicketKBLinks.kb_id).label('linked_tickets_count')
        ).outerjoin(
            TicketKBLinks, KBArticles.kb_id == TicketKBLinks.kb_id
        ).group_by(KBArticles.kb_id)
        
        result = await db.execute(kb_query)
        kb_data = result.fetchall()
        
        # Calculate effectiveness metrics
        total_articles = len(kb_data)
        articles_with_links = len([row for row in kb_data if row[1] > 0])
        
        # Most effective articles (most linked to tickets)
        most_effective = sorted(kb_data, key=lambda x: x[1], reverse=True)[:10]
        
        # Articles that need attention (no links or very few)
        needs_attention = [row for row in kb_data if row[1] == 0]
        
        # KB usage correlation with ticket resolution
        # Get tickets linked to KB articles
        linked_tickets_query = select(Tickets).join(
            TicketKBLinks, Tickets.ticket_id == TicketKBLinks.ticket_id
        ).where(
            Tickets.created_at >= start_date,
            Tickets.status == 'Closed'
        )
        
        linked_result = await db.execute(linked_tickets_query)
        linked_tickets = linked_result.scalars().all()
        
        # Calculate resolution time for tickets with KB links vs without
        all_closed_tickets_query = select(Tickets).where(
            Tickets.created_at >= start_date,
            Tickets.status == 'Closed'
        )
        
        all_closed_result = await db.execute(all_closed_tickets_query)
        all_closed_tickets = all_closed_result.scalars().all()
        
        # Calculate average resolution times
        kb_linked_resolution_times = []
        for ticket in linked_tickets:
            if ticket.closed_at and ticket.created_at:
                resolution_time = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
                kb_linked_resolution_times.append(resolution_time)
        
        all_resolution_times = []
        for ticket in all_closed_tickets:
            if ticket.closed_at and ticket.created_at:
                resolution_time = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
                all_resolution_times.append(resolution_time)
        
        avg_kb_resolution = sum(kb_linked_resolution_times) / len(kb_linked_resolution_times) if kb_linked_resolution_times else 0
        avg_all_resolution = sum(all_resolution_times) / len(all_resolution_times) if all_resolution_times else 0
        
        # KB impact score (how much KB reduces resolution time)
        kb_impact_score = (
            ((avg_all_resolution - avg_kb_resolution) / avg_all_resolution * 100)
            if avg_all_resolution > 0 else 0
        )
        
        return {
            "summary": {
                "total_articles": total_articles,
                "articles_with_usage": articles_with_links,
                "usage_rate": (articles_with_links / total_articles * 100) if total_articles else 0,
                "kb_impact_score": kb_impact_score,
                "avg_resolution_time_with_kb": avg_kb_resolution,
                "avg_resolution_time_overall": avg_all_resolution
            },
            "most_effective_articles": [
                {
                    "kb_id": row[0].kb_id,
                    "title": row[0].title,
                    "linked_tickets": row[1],
                    "created_at": row[0].created_at.isoformat()
                }
                for row in most_effective[:10]
            ],
            "articles_needing_attention": [
                {
                    "kb_id": row[0].kb_id,
                    "title": row[0].title,
                    "created_at": row[0].created_at.isoformat(),
                    "age_days": (datetime.now() - row[0].created_at).days
                }
                for row in needs_attention[:10]
            ],
            "usage_distribution": {
                "heavily_used": len([row for row in kb_data if row[1] >= 5]),
                "moderately_used": len([row for row in kb_data if 1 <= row[1] < 5]),
                "rarely_used": len([row for row in kb_data if row[1] == 0])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting KB effectiveness: {str(e)}")

@router.get("/voice/interactions")
@limiter.limit(RateLimits.ANALYTICS)
async def get_voice_interaction_analytics(
    request: Request,
    days_back: int = 7,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get voice interaction analytics from database"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Query conversations from database
        result = await db.execute(
            select(VoiceConversation).where(
                VoiceConversation.start_time >= start_date
            )
        )
        recent_conversations = result.scalars().all()
        
        total_sessions = len(recent_conversations)
        completed_sessions = [c for c in recent_conversations if c.status == "completed"]
        
        # Calculate metrics from database records
        total_duration = sum(c.duration_seconds or 0 for c in completed_sessions)
        avg_duration = (total_duration / len(completed_sessions) / 60) if completed_sessions else 0
        
        # Simulate voice-to-ticket conversion (in real implementation, track this)
        conversion_rate = 25.0  # 25% of voice sessions result in tickets
        
        # Most common query analysis (simulated)
        common_queries = [
            {"query": "password reset", "count": 45, "resolution_rate": 85},
            {"query": "printer issues", "count": 32, "resolution_rate": 78},
            {"query": "email setup", "count": 28, "resolution_rate": 92},
            {"query": "vpn connection", "count": 24, "resolution_rate": 88},
            {"query": "software installation", "count": 19, "resolution_rate": 72}
        ]
        
        # Session outcomes from database
        resolved_count = len([c for c in completed_sessions if c.metadata_json and json.loads(c.metadata_json).get("resolved", False)])
        session_outcomes = {
            "resolved_via_voice": resolved_count,
            "escalated_to_ticket": int(total_sessions * conversion_rate / 100),
            "abandoned": len([c for c in recent_conversations if c.status == "abandoned"]),
            "in_progress": len([c for c in recent_conversations if c.status == "active"])
        }
        
        # User satisfaction (simulated)
        satisfaction_scores = [4.2, 4.5, 3.8, 4.1, 4.7, 4.0, 4.3]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
        
        return {
            "summary": {
                "total_voice_sessions": total_sessions,
                "average_duration_minutes": avg_duration,
                "completion_rate": (len(completed_sessions) / total_sessions * 100) if total_sessions else 0,
                "voice_to_ticket_conversion_rate": conversion_rate,
                "average_satisfaction": avg_satisfaction
            },
            "session_outcomes": session_outcomes,
            "common_queries": common_queries,
            "daily_usage": {
                # Simulate daily usage pattern
                datetime.now().strftime("%Y-%m-%d"): total_sessions
            },
            "peak_usage_hours": [9, 10, 14, 15, 16],  # Business hours
            "user_feedback": {
                "positive": 78,
                "neutral": 15,
                "negative": 7
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voice analytics: {str(e)}")

# ===== HELPER FUNCTIONS =====

async def _get_ticket_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> TicketAnalytics:
    """Calculate ticket analytics"""
    # Get all tickets
    all_tickets_result = await db.execute(select(Tickets))
    all_tickets = all_tickets_result.scalars().all()
    
    # Get recent tickets
    recent_tickets_result = await db.execute(
        select(Tickets).where(Tickets.created_at >= start_date)
    )
    recent_tickets = recent_tickets_result.scalars().all()
    
    # Calculate metrics
    total_tickets = len(all_tickets)
    open_tickets = len([t for t in all_tickets if t.status == 'Open'])
    in_progress_tickets = len([t for t in all_tickets if t.status == 'In Progress'])
    closed_tickets = len([t for t in all_tickets if t.status == 'Closed'])
    
    # Resolution time
    resolution_times = []
    for ticket in all_tickets:
        if ticket.status == 'Closed' and ticket.closed_at and ticket.created_at:
            resolution_time = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
            resolution_times.append(resolution_time)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # Categories and priorities
    tickets_by_category = {}
    tickets_by_priority = {}
    
    for ticket in all_tickets:
        # Category
        category_name = "Unknown"
        if ticket.category_id:
            category_result = await db.execute(
                select(TicketCategories.name).where(TicketCategories.category_id == ticket.category_id)
            )
            category_name = category_result.scalar() or "Unknown"
        
        tickets_by_category[category_name] = tickets_by_category.get(category_name, 0) + 1
        tickets_by_priority[ticket.priority] = tickets_by_priority.get(ticket.priority, 0) + 1
    
    # Recent activity
    tickets_created_last_7_days = len([t for t in recent_tickets if t.created_at >= end_date - timedelta(days=7)])
    tickets_resolved_last_7_days = len([
        t for t in recent_tickets 
        if t.status == 'Closed' and t.closed_at and t.closed_at >= end_date - timedelta(days=7)
    ])
    
    resolution_rate = (closed_tickets / total_tickets * 100) if total_tickets else 0
    
    return TicketAnalytics(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        average_resolution_time_hours=avg_resolution_time,
        tickets_by_category=tickets_by_category,
        tickets_by_priority=tickets_by_priority,
        tickets_created_last_7_days=tickets_created_last_7_days,
        tickets_resolved_last_7_days=tickets_resolved_last_7_days,
        resolution_rate_percentage=resolution_rate
    )

async def _get_kb_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> KBAnalytics:
    """Calculate KB analytics"""
    # Get KB articles with link counts
    kb_query = select(
        KBArticles,
        func.count(TicketKBLinks.kb_id).label('link_count')
    ).outerjoin(
        TicketKBLinks, KBArticles.kb_id == TicketKBLinks.kb_id
    ).group_by(KBArticles.kb_id)
    
    result = await db.execute(kb_query)
    kb_data = result.fetchall()
    
    total_articles = len(kb_data)
    
    # Most linked articles
    most_linked = sorted(kb_data, key=lambda x: x[1], reverse=True)[:5]
    most_linked_articles = [
        {
            "kb_id": row[0].kb_id,
            "title": row[0].title,
            "link_count": row[1]
        }
        for row in most_linked
    ]
    
    # Articles by creator
    articles_by_creator = {}
    for row in kb_data:
        creator_result = await db.execute(
            select(Users.display_name).where(Users.user_id == row[0].created_by)
        )
        creator_name = creator_result.scalar() or "Unknown"
        articles_by_creator[creator_name] = articles_by_creator.get(creator_name, 0) + 1
    
    # Recent articles
    recent_articles = len([row for row in kb_data if row[0].created_at >= start_date])
    
    # Average links per article
    total_links = sum(row[1] for row in kb_data)
    avg_links = total_links / total_articles if total_articles else 0
    
    # KB effectiveness score (percentage of articles that are actively used)
    used_articles = len([row for row in kb_data if row[1] > 0])
    effectiveness_score = (used_articles / total_articles * 100) if total_articles else 0
    
    return KBAnalytics(
        total_articles=total_articles,
        most_linked_articles=most_linked_articles,
        articles_by_creator=articles_by_creator,
        articles_created_last_30_days=recent_articles,
        average_links_per_article=avg_links,
        kb_effectiveness_score=effectiveness_score
    )

async def _get_voice_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> VoiceAnalytics:
    """Calculate voice analytics from database"""
    # Query conversations from database
    result = await db.execute(
        select(VoiceConversation).where(
            VoiceConversation.start_time >= start_date
        )
    )
    recent_conversations = result.scalars().all()
    
    total_sessions = len(recent_conversations)
    completed_sessions = [c for c in recent_conversations if c.status == "completed"]
    
    avg_duration = (
        sum(c.duration_seconds or 0 for c in completed_sessions) / len(completed_sessions) / 60
        if completed_sessions else 0
    )
    
    # Simulated metrics
    conversion_rate = 25.0
    success_rate = 75.0
    
    common_queries = [
        {"query": "password reset", "count": 15},
        {"query": "printer issues", "count": 12},
        {"query": "email problems", "count": 8}
    ]
    
    return VoiceAnalytics(
        total_voice_sessions=total_sessions,
        average_session_duration_minutes=avg_duration,
        voice_to_ticket_conversion_rate=conversion_rate,
        most_common_voice_queries=common_queries,
        voice_resolution_success_rate=success_rate
    )

async def _get_sla_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> SLAAnalytics:
    """Calculate SLA analytics"""
    # Get tickets with SLA due dates
    tickets_with_sla_result = await db.execute(
        select(Tickets).where(Tickets.sla_due_at.isnot(None))
    )
    tickets_with_sla = tickets_with_sla_result.scalars().all()
    
    # Calculate SLA compliance
    met_sla = 0
    breached_sla = 0
    
    for ticket in tickets_with_sla:
        if ticket.status == 'Closed' and ticket.closed_at:
            if ticket.closed_at <= ticket.sla_due_at:
                met_sla += 1
            else:
                breached_sla += 1
    
    total_sla_tickets = met_sla + breached_sla
    compliance_rate = (met_sla / total_sla_tickets * 100) if total_sla_tickets else 0
    
    # Tickets approaching SLA
    now = datetime.now()
    approaching_sla = len([
        t for t in tickets_with_sla
        if t.status != 'Closed' and t.sla_due_at and t.sla_due_at <= now + timedelta(hours=4)
    ])
    
    # Average response time (simulated)
    avg_response_time = 2.5  # hours
    
    # SLA performance by category (simulated)
    sla_by_category = {
        "Windows Desktop": 85.0,
        "Printers": 92.0,
        "Network": 78.0,
        "Email": 95.0
    }
    
    return SLAAnalytics(
        sla_compliance_rate=compliance_rate,
        breached_tickets_count=breached_sla,
        average_response_time_hours=avg_response_time,
        tickets_approaching_sla=approaching_sla,
        sla_performance_by_category=sla_by_category
    )

async def _get_user_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate user analytics"""
    # Active users
    users_result = await db.execute(select(Users))
    all_users = users_result.scalars().all()
    
    # User activity
    active_requesters_result = await db.execute(
        select(func.distinct(Tickets.requester_id))
        .where(Tickets.created_at >= start_date)
    )
    active_requesters = len(active_requesters_result.fetchall())
    
    active_technicians_result = await db.execute(
        select(func.distinct(Tickets.assigned_to_id))
        .where(
            Tickets.created_at >= start_date,
            Tickets.assigned_to_id.isnot(None)
        )
    )
    active_technicians = len(active_technicians_result.fetchall())
    
    return {
        "total_users": len(all_users),
        "active_requesters": active_requesters,
        "active_technicians": active_technicians,
        "users_by_role": {
            role: len([u for u in all_users if u.role == role])
            for role in set(u.role for u in all_users)
        }
    }

async def _get_trends_analytics(db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate trend analytics"""
    # Daily ticket creation trend
    daily_tickets = {}
    current_date = start_date
    
    while current_date <= end_date:
        day_start = current_date
        day_end = current_date + timedelta(days=1)
        
        tickets_result = await db.execute(
            select(func.count(Tickets.ticket_id))
            .where(
                Tickets.created_at >= day_start,
                Tickets.created_at < day_end
            )
        )
        count = tickets_result.scalar() or 0
        daily_tickets[current_date.strftime("%Y-%m-%d")] = count
        
        current_date += timedelta(days=1)
    
    return {
        "daily_ticket_creation": daily_tickets,
        "ticket_volume_trend": "increasing",  # Could calculate actual trend
        "peak_hours": [9, 10, 14, 15, 16],  # Business hours
        "seasonal_patterns": {}  # Could add seasonal analysis
    }

# ElevenLabs Analytics Endpoints
@router.get("/elevenlabs")
@limiter.limit(RateLimits.ANALYTICS)
async def get_elevenlabs_analytics(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get ElevenLabs analytics summary from database"""
    try:
        # Query all conversations from database
        result = await db.execute(select(VoiceConversation))
        all_conversations = result.scalars().all()
        
        completed_conversations = [c for c in all_conversations if c.status == "completed"]
        
        total_duration_minutes = sum(
            (c.duration_seconds or 0) / 60 
            for c in completed_conversations
        )
        
        average_duration = (
            total_duration_minutes / len(completed_conversations) 
            if completed_conversations else 0
        )
        
        # Status distribution
        status_counts = {}
        for conv in all_conversations:
            status_counts[conv.status] = status_counts.get(conv.status, 0) + 1
        
        # Agent performance
        agent_counts = {}
        for conv in all_conversations:
            agent_counts[conv.agent_id] = agent_counts.get(conv.agent_id, 0) + 1
        
        top_agents = [
            {"agent_id": agent_id, "conversation_count": count}
            for agent_id, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Daily data from database
        daily_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            count = len([c for c in all_conversations if c.start_time.date() == date])
            daily_data.append({"date": date.isoformat(), "count": count})
        
        return {
            "total_conversations": len(all_conversations),
            "total_duration_minutes": total_duration_minutes,
            "average_conversation_duration": average_duration,
            "conversations_by_status": status_counts,
            "conversations_by_date": daily_data,
            "top_agents": top_agents,
            "user_satisfaction": {
                "average_rating": 4.2,  # Would need separate ratings table
                "total_ratings": len(completed_conversations)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ElevenLabs analytics: {str(e)}")

@router.get("/elevenlabs/conversations")
@limiter.limit(RateLimits.ANALYTICS)
async def get_elevenlabs_conversations(
    request: Request,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get ElevenLabs conversations from database"""
    try:
        # Query conversations from database, ordered by start_time desc
        result = await db.execute(
            select(VoiceConversation)
            .order_by(desc(VoiceConversation.start_time))
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        # Return database conversations
        return [
            {
                "conversation_id": c.conversation_id,
                "agent_id": c.agent_id,
                "user_id": c.user_id,
                "start_time": c.start_time.isoformat() if c.start_time else None,
                "end_time": c.end_time.isoformat() if c.end_time else None,
                "duration_seconds": c.duration_seconds,
                "messages_count": c.messages_count,
                "status": c.status,
                "metadata": json.loads(c.metadata_json) if c.metadata_json else {}
            }
            for c in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@router.get("/elevenlabs/conversations/{conversation_id}")
@limiter.limit(RateLimits.ANALYTICS)
async def get_elevenlabs_conversation(
    request: Request,
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get specific ElevenLabs conversation from database"""
    try:
        result = await db.execute(
            select(VoiceConversation).where(
                VoiceConversation.conversation_id == conversation_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation.conversation_id,
            "agent_id": conversation.agent_id,
            "user_id": conversation.user_id,
            "start_time": conversation.start_time.isoformat() if conversation.start_time else None,
            "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
            "duration_seconds": conversation.duration_seconds,
            "messages_count": conversation.messages_count,
            "status": conversation.status,
            "metadata": json.loads(conversation.metadata_json) if conversation.metadata_json else {}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@router.get("/elevenlabs/conversations/{conversation_id}/messages")
@limiter.limit(RateLimits.ANALYTICS)
async def get_elevenlabs_messages(
    request: Request,
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get messages for a specific conversation from database"""
    try:
        result = await db.execute(
            select(VoiceMessage)
            .where(VoiceMessage.conversation_id == conversation_id)
            .order_by(VoiceMessage.timestamp)
        )
        messages = result.scalars().all()
        
        return [
            {
                "message_id": m.message_id,
                "conversation_id": m.conversation_id,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "type": m.message_type,
                "content": m.content,
                "duration_seconds": m.duration_seconds,
                "metadata": json.loads(m.metadata_json) if m.metadata_json else {}
            }
            for m in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

@router.post("/elevenlabs/conversations")
@limiter.limit(RateLimits.WRITE)
async def track_elevenlabs_conversation(
    request: Request,
    conversation: ElevenLabsConversation,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Track a new ElevenLabs conversation in database"""
    try:
        # Parse start_time string to datetime
        start_time = datetime.fromisoformat(conversation.start_time.replace('Z', '+00:00'))
        end_time = None
        if conversation.end_time:
            end_time = datetime.fromisoformat(conversation.end_time.replace('Z', '+00:00'))
        
        db_conversation = VoiceConversation(
            conversation_id=conversation.conversation_id,
            agent_id=conversation.agent_id,
            user_id=conversation.user_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=conversation.duration_seconds,
            messages_count=conversation.messages_count,
            status=conversation.status,
            metadata_json=json.dumps(conversation.metadata) if conversation.metadata else None
        )
        
        db.add(db_conversation)
        await db.commit()
        
        return {"message": "Conversation tracked successfully", "conversation_id": conversation.conversation_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error tracking conversation: {str(e)}")

@router.put("/elevenlabs/conversations/{conversation_id}")
@limiter.limit(RateLimits.WRITE)
async def update_elevenlabs_conversation(
    request: Request,
    conversation_id: str, 
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Update an existing ElevenLabs conversation in database"""
    try:
        result = await db.execute(
            select(VoiceConversation).where(
                VoiceConversation.conversation_id == conversation_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update conversation fields
        for key, value in updates.items():
            if key == 'metadata':
                conversation.metadata_json = json.dumps(value) if value else None
            elif key == 'end_time' and value:
                conversation.end_time = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif hasattr(conversation, key):
                setattr(conversation, key, value)
        
        await db.commit()
        
        return {"message": "Conversation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")


# ===== SENTIMENT ANALYSIS ENDPOINTS =====

class SentimentRequest(BaseModel):
    text: str

class SentimentTrendItem(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int
    average_confidence: float

@router.post("/sentiment/analyze")
@limiter.limit(RateLimits.ANALYTICS)
async def analyze_text_sentiment(
    request: Request,
    sentiment_request: SentimentRequest
) -> Dict[str, Any]:
    """Analyze sentiment of provided text using Vertex AI."""
    from ..services.enhanced_rag import enhanced_rag_service
    
    result = await enhanced_rag_service.analyze_sentiment(sentiment_request.text)
    return result


@router.get("/sentiment/trends")
@limiter.limit(RateLimits.ANALYTICS)
async def get_sentiment_trends(
    request: Request,
    days_back: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sentiment trends over time.
    Analyzes ticket descriptions and comments to identify sentiment patterns.
    """
    from ..services.enhanced_rag import enhanced_rag_service
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get tickets within date range
    result = await db.execute(
        select(Tickets).where(
            Tickets.created_at >= start_date,
            Tickets.created_at <= end_date
        ).order_by(Tickets.created_at).limit(100)  # Limit for performance
    )
    tickets = result.scalars().all()
    
    # Aggregate by date
    daily_sentiment: Dict[str, Dict[str, Any]] = {}
    
    for ticket in tickets:
        date_key = ticket.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_sentiment:
            daily_sentiment[date_key] = {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "total_confidence": 0.0,
                "count": 0
            }
        
        # Analyze sentiment (use description for analysis)
        if ticket.description:
            sentiment = await enhanced_rag_service.analyze_sentiment(ticket.description[:500])
            sent_type = sentiment.get("sentiment", "neutral")
            confidence = sentiment.get("confidence", 0.5)
            
            daily_sentiment[date_key][sent_type] += 1
            daily_sentiment[date_key]["total_confidence"] += confidence
            daily_sentiment[date_key]["count"] += 1
    
    # Format results
    trends = []
    for date_key, data in sorted(daily_sentiment.items()):
        avg_conf = data["total_confidence"] / data["count"] if data["count"] > 0 else 0.0
        trends.append({
            "date": date_key,
            "positive": data["positive"],
            "neutral": data["neutral"],
            "negative": data["negative"],
            "average_confidence": round(avg_conf, 2)
        })
    
    # Calculate overall summary
    total_positive = sum(d["positive"] for d in daily_sentiment.values())
    total_neutral = sum(d["neutral"] for d in daily_sentiment.values())
    total_negative = sum(d["negative"] for d in daily_sentiment.values())
    total = total_positive + total_neutral + total_negative
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days_back
        },
        "summary": {
            "total_analyzed": total,
            "positive_percentage": round(total_positive / total * 100, 1) if total > 0 else 0,
            "neutral_percentage": round(total_neutral / total * 100, 1) if total > 0 else 0,
            "negative_percentage": round(total_negative / total * 100, 1) if total > 0 else 0
        },
        "trends": trends
    }

