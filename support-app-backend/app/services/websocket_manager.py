# app/services/websocket_manager.py
"""
WebSocket connection manager for real-time features.
Handles connection pooling, room subscriptions, and message broadcasting.
"""
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with room-based subscriptions.
    Supports ticket-specific and user-specific channels.
    """
    
    def __init__(self):
        # Active connections by room
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Connection to rooms mapping (for cleanup)
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}
        # User ID to connection mapping
        self.user_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, room: str, user_id: Optional[str] = None):
        """Accept a WebSocket connection and add to a room."""
        await websocket.accept()
        
        # Add to room
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        
        # Track rooms for this connection
        if websocket not in self.connection_rooms:
            self.connection_rooms[websocket] = set()
        self.connection_rooms[websocket].add(room)
        
        # Track user connection
        if user_id:
            self.user_connections[user_id] = websocket
            
        logger.info(f"WebSocket connected to room: {room}")
        
    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Remove a WebSocket connection from all rooms."""
        # Remove from all rooms
        if websocket in self.connection_rooms:
            for room in self.connection_rooms[websocket]:
                if room in self.rooms:
                    self.rooms[room].discard(websocket)
                    if not self.rooms[room]:
                        del self.rooms[room]
            del self.connection_rooms[websocket]
            
        # Remove user mapping
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
            
        logger.info("WebSocket disconnected")
        
    async def broadcast_to_room(self, room: str, message: Dict[str, Any]):
        """Broadcast a message to all connections in a room."""
        if room not in self.rooms:
            return
            
        dead_connections = set()
        message_json = json.dumps(message)
        
        for websocket in self.rooms[room]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.add(websocket)
                
        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws)
            
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to a specific user."""
        if user_id not in self.user_connections:
            return False
            
        try:
            await self.user_connections[user_id].send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.warning(f"Failed to send to user {user_id}: {e}")
            return False
            
    async def broadcast_ticket_update(self, ticket_id: int, event: str, data: Dict[str, Any]):
        """Broadcast a ticket update event."""
        room = f"ticket:{ticket_id}"
        message = {
            "event": event,
            "ticket_id": ticket_id,
            "data": data
        }
        await self.broadcast_to_room(room, message)
        
    async def broadcast_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send a notification to a user."""
        room = f"user:{user_id}"
        message = {
            "event": "notification",
            "data": notification
        }
        await self.broadcast_to_room(room, message)
        
    def get_room_count(self, room: str) -> int:
        """Get the number of connections in a room."""
        return len(self.rooms.get(room, set()))
        
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_rooms)


# Global instance
connection_manager = ConnectionManager()
