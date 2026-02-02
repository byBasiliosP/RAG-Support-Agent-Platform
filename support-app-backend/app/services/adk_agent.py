# app/services/adk_agent.py
"""
Google ADK (Agent Development Kit) & A2A Integration.
Provides structured agent capabilities and Agent-to-Agent (A2A) discovery.
"""
from typing import List, Dict, Any, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# ADK and A2A Imports (Handling availability)
try:
    from google import adk
    from google.adk import Agent, Tool
    from google.adk.a2a import AgentCard, A2AClient
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("Warning: Google ADK/A2A not available - agent features limited to mock")

class SupportAgent:
    """
    ADK-powered support agent with A2A capabilities.
    """
    
    def __init__(self):
        self.agent = None
        self.a2a_client = None
        self.agent_card = None
        
        if ADK_AVAILABLE and settings.GOOGLE_PROJECT_ID:
            self._initialize_agent()
            self._register_a2a()
    
    def _initialize_agent(self):
        """Initialize the ADK agent with tools."""
        try:
            # Define tools
            tools = self._create_tools()
            
            # Create the agent using Vertex AI model
            self.agent = Agent(
                model=settings.GEMINI_MODEL,
                name="IT Support Agent",
                description="Expert IT support agent for troubleshooting and ticket management",
                tools=tools,
                project=settings.GOOGLE_PROJECT_ID,
                location=settings.GOOGLE_LOCATION,
                credentials=settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            logger.info("✅ ADK Support Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ADK agent: {e}")
            self.agent = None
            
    def _register_a2a(self):
        """Register the agent with the A2A network using AgentCard."""
        try:
            self.agent_card = AgentCard(
                name="support-agent-v1",
                description="IT Support Agent capable of KB search and ticket creation",
                capabilities=["search_kb", "create_ticket", "check_status"],
                input_schema={"type": "string", "description": "User query or issue description"},
                output_schema={"type": "json", "description": "Support response and metadata"},
                version="1.0.0"
            )
            
            self.a2a_client = A2AClient(project=settings.GOOGLE_PROJECT_ID)
            self.a2a_client.register(self.agent_card)
            logger.info("✅ Agent registered with A2A network")
        except Exception as e:
            logger.warning(f"Failed to register with A2A network: {e}")

    def _create_tools(self) -> List:
        """Create tools for the agent."""
        if not ADK_AVAILABLE:
            return []
            
        @Tool(description="Search knowledge base for relevant articles")
        def search_kb(query: str) -> str:
            return f"Searching KB for: {query}"
        
        @Tool(description="Create a new support ticket")
        def create_ticket(subject: str, description: str, priority: str = "medium") -> str:
            return f"Creating ticket: {subject}"
        
        @Tool(description="Check the status of an existing ticket")
        def check_ticket_status(ticket_id: str) -> str:
            return f"Checking status of ticket: {ticket_id}"
        
        return [search_kb, create_ticket, check_ticket_status]
    
    async def handle_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle a user query using the ADK agent."""
        if not self.agent:
            return {
                "answer": "Agent not available. Please configure Google Vertex AI.",
                "agent_available": False
            }
        
        try:
            # Run the agent
            response = await self.agent.run(query)
            
            return {
                "answer": response.text,
                "agent_available": True,
                "tools_used": getattr(response, 'tools_used', []),
                "metadata": {
                    "model": settings.GEMINI_MODEL,
                    "agent_card": self.agent_card.to_dict() if self.agent_card else None
                }
            }
        except Exception as e:
            logger.error(f"ADK agent error: {e}")
            return {"answer": f"Agent error: {str(e)}", "agent_available": True}

# Global instance
support_agent = SupportAgent()
