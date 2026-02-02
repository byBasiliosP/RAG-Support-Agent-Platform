# app/routers/websocket.py
"""
WebSocket endpoints for real-time communication.
Provides live updates for tickets and user notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional
import logging
import json

from ..services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


async def verify_ws_token(token: Optional[str] = Query(None)) -> Optional[str]:
    """
    Verify WebSocket authentication token.
    Returns user_id if valid, None otherwise.
    In production, implement proper JWT validation.
    """
    # TODO: Implement proper JWT token validation
    # For now, accept any token as user_id for development
    if token:
        return token
    return None


@router.websocket("/tickets/{ticket_id}")
async def ticket_websocket(
    websocket: WebSocket,
    ticket_id: int,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for live ticket updates.
    
    Connect to receive real-time updates for a specific ticket:
    - ticket.updated - Ticket fields changed
    - ticket.comment - New comment added
    - ticket.status_changed - Status transition
    - ticket.assigned - Ticket assigned/reassigned
    """
    user_id = await verify_ws_token(token)
    room = f"ticket:{ticket_id}"
    
    await connection_manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "connected",
            "ticket_id": ticket_id,
            "message": f"Connected to ticket {ticket_id} updates"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle ping/pong for keep-alive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"Client disconnected from ticket:{ticket_id}")


@router.websocket("/notifications/{user_id}")
async def notifications_websocket(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for user notifications.
    
    Connect to receive real-time notifications:
    - notification - New notification
    - ticket.assigned - Ticket assigned to user
    - ticket.mentioned - User mentioned in comment
    - sla.warning - SLA deadline approaching
    """
    # Verify token matches user_id in production
    authenticated_user = await verify_ws_token(token)
    room = f"user:{user_id}"
    
    await connection_manager.connect(websocket, room, user_id)
    
    try:
        await websocket.send_json({
            "event": "connected",
            "user_id": user_id,
            "message": "Connected to notification stream"
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                # Handle read receipts
                elif message.get("type") == "mark_read":
                    notification_id = message.get("notification_id")
                    # TODO: Mark notification as read in database
                    await websocket.send_json({
                        "type": "read_confirmed",
                        "notification_id": notification_id
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"Client disconnected from notifications:{user_id}")


@router.get("/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": connection_manager.get_total_connections(),
        "active_rooms": len(connection_manager.rooms)
    }
