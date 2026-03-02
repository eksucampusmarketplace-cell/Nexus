"""
WebSocket Router - FastAPI endpoint for real-time communication.

This module provides the WebSocket endpoint for the Mini App
to connect and receive real-time updates.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel

from shared.websocket_manager import get_ws_manager, WebSocketManager, ConnectedClient
from shared.event_bus import NexusEvent, EventType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: int,
    token: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    telegram_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time communication.
    
    Connection flow:
    1. Client connects with optional auth params
    2. Server accepts connection
    3. Server subscribes to Redis pub/sub for this group
    4. Events are broadcast to the client in real-time
    5. Client can send commands (if authenticated)
    6. Heartbeat ping/pong keeps connection alive
    
    Message format:
    {
        "type": "event" | "command" | "ping" | "pong" | "error",
        "data": { ... },
        "timestamp": "2024-01-01T00:00:00"
    }
    """
    ws_manager = await get_ws_manager()
    client: Optional[ConnectedClient] = None
    
    try:
        # Accept connection
        client = await ws_manager.connect(
            websocket=websocket,
            group_id=group_id,
            user_id=user_id,
            telegram_id=telegram_id,
            username=username
        )
        
        # Main message loop
        while True:
            try:
                # Receive message
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0  # 60 second timeout
                )
                
                # Handle the message
                await ws_manager.handle_client_message(client, data)
                
            except asyncio.TimeoutError:
                # No message received in 60 seconds, send ping
                client.last_ping = client.last_ping  # Keep existing time
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": client.last_ping.isoformat()
                })
            
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: group={group_id}")
                break
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                    "timestamp": client.last_ping.isoformat()
                })
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)},
                    "timestamp": client.last_ping.isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info(f"Connection closed during handshake: group={group_id}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up connection
        if client:
            await ws_manager.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    ws_manager = await get_ws_manager()
    
    return {
        "active_connections": ws_manager.get_connection_count(),
        "groups_with_connections": ws_manager.get_group_ids()
    }


@router.get("/ws/status/{group_id}")
async def websocket_group_status(group_id: int):
    """Get WebSocket connection status for a specific group."""
    ws_manager = await get_ws_manager()
    
    return {
        "group_id": group_id,
        "active_connections": ws_manager.get_connection_count(group_id)
    }
