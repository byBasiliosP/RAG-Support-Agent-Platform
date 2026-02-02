# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, SmallInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Original Document model for RAG
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"

# Support System Models
class Users(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100))
    role = Column(String(50))  # e.g. "technician", "end-user", "manager"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    created_kb_articles = relationship("KBArticles", back_populates="creator")
    requested_tickets = relationship("Tickets", foreign_keys="[Tickets.requester_id]", back_populates="requester")
    assigned_tickets = relationship("Tickets", foreign_keys="[Tickets.assigned_to_id]", back_populates="assigned_to")

class TicketCategories(Base):
    __tablename__ = "ticketcategories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # Relationships
    tickets = relationship("Tickets", back_populates="category")

class KBArticles(Base):
    __tablename__ = "kbarticles"
    
    kb_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    content = Column(Text)  # Full article content
    url = Column(String(500))
    version = Column(Integer, default=1, nullable=False)  # Current version number
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True))
    auto_generated = Column(Boolean, default=False)  # True if generated from ticket
    source_ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=True)
    
    # Relationships
    creator = relationship("Users", back_populates="created_kb_articles")
    ticket_links = relationship("TicketKBLinks", back_populates="kb_article")
    versions = relationship("KBArticleVersion", back_populates="article", order_by="desc(KBArticleVersion.version)")


class KBArticleVersion(Base):
    """Stores version history for KB articles"""
    __tablename__ = "kb_article_versions"
    
    version_id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("kbarticles.kb_id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    url = Column(String(500))
    modified_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    change_note = Column(String(500))  # Optional description of changes
    
    # Relationships
    article = relationship("KBArticles", back_populates="versions")
    modifier = relationship("Users")

class Tickets(Base):
    __tablename__ = "tickets"
    
    ticket_id = Column(Integer, primary_key=True, index=True)
    external_ticket_no = Column(String(50), unique=True)
    requester_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.user_id"), index=True)  # Added index
    category_id = Column(Integer, ForeignKey("ticketcategories.category_id"))
    priority = Column(String(20), nullable=False, index=True)  # Added index
    status = Column(String(20), nullable=False, index=True)    # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)  # Added index
    closed_at = Column(DateTime(timezone=True))
    sla_due_at = Column(DateTime(timezone=True), index=True)  # Added index for SLA queries
    subject = Column(String(200))
    description = Column(Text)
    
    # Relationships
    requester = relationship("Users", foreign_keys=[requester_id], back_populates="requested_tickets")
    assigned_to = relationship("Users", foreign_keys=[assigned_to_id], back_populates="assigned_tickets")
    category = relationship("TicketCategories", back_populates="tickets")
    root_causes = relationship("TicketRootCauses", back_populates="ticket")
    resolution_steps = relationship("ResolutionSteps", back_populates="ticket")
    kb_links = relationship("TicketKBLinks", back_populates="ticket")
    attachments = relationship("Attachments", back_populates="ticket")

class TicketRootCauses(Base):
    __tablename__ = "ticketrootcauses"
    
    rootcause_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False)
    cause_code = Column(String(50))  # e.g. "SW-001", "HW-002"
    description = Column(Text)
    identified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("Tickets", back_populates="root_causes")

class ResolutionSteps(Base):
    __tablename__ = "resolutionsteps"
    
    step_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False)
    step_order = Column(SmallInteger, nullable=False)  # 1,2,3…
    instructions = Column(Text, nullable=False)
    success_flag = Column(Boolean, default=False)
    performed_by = Column(Integer, ForeignKey("users.user_id"))
    performed_at = Column(DateTime(timezone=True))
    
    # Relationships
    ticket = relationship("Tickets", back_populates="resolution_steps")
    performer = relationship("Users")

class TicketKBLinks(Base):
    __tablename__ = "ticketkblinks"
    
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), primary_key=True)
    kb_id = Column(Integer, ForeignKey("kbarticles.kb_id"), primary_key=True)
    
    # Relationships
    ticket = relationship("Tickets", back_populates="kb_links")
    kb_article = relationship("KBArticles", back_populates="ticket_links")

class Attachments(Base):
    __tablename__ = "attachments"
    
    attachment_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False)
    filename = Column(String(200))
    file_url = Column(String(500))
    uploaded_by = Column(Integer, ForeignKey("users.user_id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("Tickets", back_populates="attachments")
    uploader = relationship("Users")


# Voice/ElevenLabs Conversation Models for Persistent Storage
class VoiceConversation(Base):
    """Stores ElevenLabs voice conversation sessions for analytics persistence"""
    __tablename__ = "voice_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    messages_count = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, completed, abandoned
    metadata_json = Column(Text)  # JSON string for flexible metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    messages = relationship("VoiceMessage", back_populates="conversation", cascade="all, delete-orphan")


class VoiceMessage(Base):
    """Stores individual messages within voice conversations"""
    __tablename__ = "voice_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    conversation_id = Column(String(100), ForeignKey("voice_conversations.conversation_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    message_type = Column(String(20))  # user or agent
    content = Column(Text)
    duration_seconds = Column(Integer)
    metadata_json = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("VoiceConversation", back_populates="messages")

