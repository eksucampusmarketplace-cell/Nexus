"""
WebSocket Manager - Real-time bidirectional communication.

This module provides WebSocket connectivity for the Mini App,
enabling real-time updates for:
- Live message feed
- Instant moderation actions
- Member updates
- Module toggles
- And more

Architecture:
1. Mini App connects via WebSocket to /ws/{group_id}
2. WebSocket manager subscribes to Redis pub/sub for that group
3. Events are broadcast to all connected clients instantly
4. Clients can also send commands through the WebSocket
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, ValidationError
import redis.asyncio as aioredis

from shared.event_bus import EventBus, NexusEvent, EventType, get_event_bus
from shared.redis_client import get_redis

logger = logging.getLogger(__name__)


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # event, command, ping, pong, error, auth
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class WSCommand(BaseModel):
    """Command from Mini App to server."""
    action: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class ConnectedClient:
    """Represents a connected WebSocket client."""
    websocket: WebSocket
    group_id: int
    user_id: Optional[int] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    
    # Subscribed event types (None = all)
    subscribed_events: Optional[Set[EventType]] = None
    
    # Is authenticated
    authenticated: bool = False


class WebSocketManager:
    """
    Manages WebSocket connections and event broadcasting.
    
    Features:
    - Connection management per group
    - Event subscription filtering
    - Ping/pong heartbeat
    - Authentication
    - Command handling
    """
    
    def __init__(self, redis: aioredis.Redis, event_bus: EventBus):
        self.redis = redis
        self.event_bus = event_bus
        
        # group_id -> set of ConnectedClient
        self._connections: Dict[int, Set[ConnectedClient]] = {}
        
        # All connections by websocket for quick lookup
        self._websocket_to_client: Dict[WebSocket, ConnectedClient] = {}
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False
    
    async def start(self) -> None:
        """Start the WebSocket manager background tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Start event listener task
        task = asyncio.create_task(self._event_listener())
        self._tasks.append(task)
        
        # Start heartbeat task
        task = asyncio.create_task(self._heartbeat_checker())
        self._tasks.append(task)
        
        logger.info("WebSocket manager started")
    
    async def stop(self) -> None:
        """Stop the WebSocket manager."""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()
        
        # Close all connections
        for group_id, clients in list(self._connections.items()):
            for client in list(clients):
                try:
                    await client.websocket.close()
                except Exception:
                    pass
        
        self._connections.clear()
        self._websocket_to_client.clear()
        
        logger.info("WebSocket manager stopped")
    
    async def connect(
        self,
        websocket: WebSocket,
        group_id: int,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> ConnectedClient:
        """
        Accept a new WebSocket connection.
        
        Returns the ConnectedClient instance.
        """
        await websocket.accept()
        
        client = ConnectedClient(
            websocket=websocket,
            group_id=group_id,
            user_id=user_id,
            telegram_id=telegram_id,
            username=username,
            authenticated=user_id is not None
        )
        
        # Track the connection
        if group_id not in self._connections:
            self._connections[group_id] = set()
            # Subscribe to Redis channel for this group
            await self.event_bus.subscribe(group_id, self._handle_redis_event)
        
        self._connections[group_id].add(client)
        self._websocket_to_client[websocket] = client
        
        logger.info(
            f"WebSocket connected: group={group_id}, user={user_id}, "
            f"total_connections={sum(len(c) for c in self._connections.values())}"
        )
        
        # Send welcome message
        await self._send_to_client(client, WSMessage(
            type="connected",
            data={
                "group_id": group_id,
                "message": "Connected to Nexus real-time feed"
            }
        ))
        
        return client
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        client = self._websocket_to_client.pop(websocket, None)
        
        if client:
            group_id = client.group_id
            clients = self._connections.get(group_id)
            
            if clients:
                clients.discard(client)
                
                # If no more clients for this group, unsubscribe from Redis
                if not clients:
                    del self._connections[group_id]
                    await self.event_bus.unsubscribe(group_id, self._handle_redis_event)
            
            logger.info(
                f"WebSocket disconnected: group={group_id}, user={client.user_id}, "
                f"remaining={sum(len(c) for c in self._connections.values())}"
            )
    
    async def broadcast_to_group(
        self,
        group_id: int,
        event: NexusEvent,
        exclude: Optional[WebSocket] = None
    ) -> int:
        """
        Broadcast an event to all clients in a group.
        
        Returns the number of clients that received the message.
        """
        clients = self._connections.get(group_id, set())
        sent_count = 0
        
        for client in clients:
            if exclude and client.websocket == exclude:
                continue
            
            # Check if client is subscribed to this event type
            if client.subscribed_events and event.event_type not in client.subscribed_events:
                continue
            
            try:
                await self._send_to_client(client, WSMessage(
                    type="event",
                    data=event.to_dict()
                ))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
        
        return sent_count
    
    async def send_to_user(
        self,
        user_id: int,
        message: WSMessage
    ) -> bool:
        """Send a message to all connections from a specific user."""
        sent = False
        
        for clients in self._connections.values():
            for client in clients:
                if client.user_id == user_id:
                    try:
                        await self._send_to_client(client, message)
                        sent = True
                    except Exception as e:
                        logger.error(f"Failed to send to user {user_id}: {e}")
        
        return sent
    
    async def handle_client_message(
        self,
        client: ConnectedClient,
        message: dict
    ) -> None:
        """Handle an incoming message from a client."""
        try:
            ws_msg = WSMessage(**message)
            
            if ws_msg.type == "ping":
                client.last_ping = datetime.utcnow()
                await self._send_to_client(client, WSMessage(type="pong"))
            
            elif ws_msg.type == "command":
                if not client.authenticated:
                    await self._send_to_client(client, WSMessage(
                        type="error",
                        data={"message": "Not authenticated"}
                    ))
                    return
                
                await self._handle_command(client, ws_msg.data or {})
            
            elif ws_msg.type == "auth":
                # Handle authentication
                auth_data = ws_msg.data or {}
                if auth_data.get("token"):
                    # Validate token and update client
                    # This would integrate with your auth system
                    pass
            
            elif ws_msg.type == "subscribe":
                # Update event subscriptions
                event_types = ws_msg.data.get("events", [])
                if event_types:
                    client.subscribed_events = {
                        EventType(e) for e in event_types
                    }
                else:
                    client.subscribed_events = None
                
                await self._send_to_client(client, WSMessage(
                    type="subscribed",
                    data={
                        "events": [e.value for e in client.subscribed_events]
                        if client.subscribed_events else "all"
                    }
                ))
        
        except ValidationError as e:
            logger.error(f"Invalid WebSocket message: {e}")
            await self._send_to_client(client, WSMessage(
                type="error",
                data={"message": "Invalid message format"}
            ))
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def _handle_command(
        self,
        client: ConnectedClient,
        command: Dict[str, Any]
    ) -> None:
        """Handle a command from the Mini App."""
        action = command.get("action")
        params = command.get("params", {})
        
        try:
            # Import action executor
            from shared.action_executor import get_action_executor, ActionContext
            
            executor = await get_action_executor()
            
            # Handle different commands
            if action in ["warn", "mute", "ban", "kick", "unmute", "unban"]:
                target_id = params.get("target_id")
                if not target_id:
                    await self._send_to_client(client, WSMessage(
                        type="error",
                        data={"message": "target_id required"}
                    ))
                    return
                
                ctx = ActionContext(
                    group_id=client.group_id,
                    actor_id=client.user_id,
                    target_id=target_id,
                    group_telegram_id=0,  # Will be filled by executor
                    actor_telegram_id=client.telegram_id,
                    target_telegram_id=params.get("target_telegram_id", 0),
                    action_type=action,
                    reason=params.get("reason"),
                    duration_seconds=params.get("duration_seconds"),
                    source="api"
                )
                
                result = await getattr(executor, action)(ctx)
                
                await self._send_to_client(client, WSMessage(
                    type="command_result",
                    data={
                        "action": action,
                        "success": result.success,
                        "message": result.message,
                        "error": result.error
                    }
                ))
            
            elif action == "toggle_module":
                # Handle module toggle
                module_name = params.get("module")
                enabled = params.get("enabled", True)
                
                # This would update the database and broadcast the change
                # For now, just acknowledge
                await self._send_to_client(client, WSMessage(
                    type="command_result",
                    data={
                        "action": "toggle_module",
                        "success": True,
                        "module": module_name,
                        "enabled": enabled
                    }
                ))
            
            else:
                await self._send_to_client(client, WSMessage(
                    type="error",
                    data={"message": f"Unknown action: {action}"}
                ))
        
        except Exception as e:
            logger.error(f"Command handling failed: {e}")
            await self._send_to_client(client, WSMessage(
                type="error",
                data={"message": str(e)}
            ))
    
    async def _send_to_client(
        self,
        client: ConnectedClient,
        message: WSMessage
    ) -> None:
        """Send a message to a specific client."""
        try:
            await client.websocket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            # Connection might be broken
            await self.disconnect(client.websocket)
    
    async def _handle_redis_event(self, event: NexusEvent) -> None:
        """Handle events from Redis pub/sub and broadcast to WebSocket clients."""
        await self.broadcast_to_group(event.group_id, event)
    
    async def _event_listener(self) -> None:
        """Background task to listen for Redis events."""
        await self.event_bus.start_listener()
    
    async def _heartbeat_checker(self) -> None:
        """Background task to check client heartbeats."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = datetime.utcnow()
                timeout = 60  # 60 second timeout
                
                for group_id, clients in list(self._connections.items()):
                    for client in list(clients):
                        if (now - client.last_ping).total_seconds() > timeout:
                            logger.info(
                                f"Client timeout: group={group_id}, user={client.user_id}"
                            )
                            try:
                                await client.websocket.close()
                            except Exception:
                                pass
                            await self.disconnect(client.websocket)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat check error: {e}")
    
    def get_connection_count(self, group_id: Optional[int] = None) -> int:
        """Get the number of active connections."""
        if group_id:
            return len(self._connections.get(group_id, set()))
        return sum(len(clients) for clients in self._connections.values())
    
    def get_group_ids(self) -> List[int]:
        """Get all group IDs with active connections."""
        return list(self._connections.keys())


# Global WebSocket manager
_ws_manager: Optional[WebSocketManager] = None


async def get_ws_manager() -> WebSocketManager:
    """Get or create the global WebSocket manager."""
    global _ws_manager
    
    if _ws_manager is None:
        redis = await get_redis()
        event_bus = await get_event_bus()
        _ws_manager = WebSocketManager(redis, event_bus)
        await _ws_manager.start()
    
    return _ws_manager


async def shutdown_ws_manager() -> None:
    """Shutdown the WebSocket manager."""
    global _ws_manager
    
    if _ws_manager:
        await _ws_manager.stop()
        _ws_manager = None
