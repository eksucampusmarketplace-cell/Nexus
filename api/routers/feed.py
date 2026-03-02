"""Live feed and WebSocket router."""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user, verify_token
from shared.database import get_db, AsyncSessionLocal
from shared.models import Member, User
from shared.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections per group."""

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, group_id: int, websocket: WebSocket):
        await websocket.accept()
        if group_id not in self._connections:
            self._connections[group_id] = []
        self._connections[group_id].append(websocket)
        logger.info(f"WS connected for group {group_id}. Total: {len(self._connections[group_id])}")

    def disconnect(self, group_id: int, websocket: WebSocket):
        if group_id in self._connections:
            self._connections[group_id].discard(websocket) if hasattr(
                self._connections[group_id], 'discard'
            ) else None
            try:
                self._connections[group_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[group_id]:
                del self._connections[group_id]
        logger.info(f"WS disconnected for group {group_id}")

    async def broadcast(self, group_id: int, message: dict):
        if group_id not in self._connections:
            return
        dead = []
        for ws in list(self._connections[group_id]):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(group_id, ws)

    def connection_count(self, group_id: int) -> int:
        return len(self._connections.get(group_id, []))


manager = ConnectionManager()


async def _verify_ws_token(token: str) -> Optional[User]:
    """Verify a token string and return the user."""
    async with AsyncSessionLocal() as db:
        user = await verify_token(token, db)
        return user


@router.websocket("/ws/groups/{group_id}/feed")
async def websocket_feed(
    group_id: int,
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for live group feed."""
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user = await _verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Member).where(
                Member.user_id == user.id,
                Member.group_id == group_id,
            )
        )
        member = result.scalar()

    if not member or member.role not in ("owner", "admin", "mod"):
        await websocket.close(code=4003, reason="Insufficient permissions")
        return

    await manager.connect(group_id, websocket)

    redis = await get_redis()
    channel = f"nexus:g{group_id}:feed"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    async def redis_listener():
        try:
            async for raw in pubsub.listen():
                if raw["type"] == "message":
                    try:
                        data = json.loads(raw["data"])
                        await websocket.send_json(data)
                    except Exception as e:
                        logger.warning(f"WS send error: {e}")
                        break
        except Exception as e:
            logger.warning(f"Redis listener error: {e}")

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "action":
                    await _handle_ws_action(group_id, user, data, websocket)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error for group {group_id}: {e}")
    finally:
        listener_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception:
            pass
        manager.disconnect(group_id, websocket)


async def _handle_ws_action(group_id: int, user: User, data: dict, websocket: WebSocket):
    """Handle action messages sent via WebSocket."""
    action_type = data.get("action")
    target_user_id = data.get("user_id")
    reason = data.get("reason", "Action from Mini App")
    duration = data.get("duration")

    if not action_type or not target_user_id:
        await websocket.send_json({"type": "error", "message": "Missing action or user_id"})
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Member).where(
                Member.user_id == user.id,
                Member.group_id == group_id,
            )
        )
        actor = result.scalar()
        if not actor or actor.role not in ("owner", "admin", "mod"):
            await websocket.send_json({"type": "error", "message": "Permission denied"})
            return

        result = await db.execute(
            select(Member).where(
                Member.user_id == target_user_id,
                Member.group_id == group_id,
            )
        )
        target = result.scalar()
        if not target:
            await websocket.send_json({"type": "error", "message": "User not found"})
            return

        from shared.models import ModAction, Warning
        from datetime import datetime, timedelta

        if action_type == "warn":
            warning = Warning(
                group_id=group_id,
                user_id=target_user_id,
                issued_by=user.id,
                reason=reason,
            )
            db.add(warning)
            target.warn_count += 1
            mod_action = ModAction(
                group_id=group_id,
                target_user_id=target_user_id,
                actor_id=user.id,
                action_type="warn",
                reason=reason,
            )
            db.add(mod_action)

        elif action_type == "mute":
            target.is_muted = True
            if duration:
                from api.routers.members import parse_duration
                secs = parse_duration(duration)
                if secs:
                    target.mute_until = datetime.utcnow() + timedelta(seconds=secs)
            mod_action = ModAction(
                group_id=group_id,
                target_user_id=target_user_id,
                actor_id=user.id,
                action_type="mute",
                reason=reason,
            )
            db.add(mod_action)

        elif action_type == "ban":
            target.is_banned = True
            mod_action = ModAction(
                group_id=group_id,
                target_user_id=target_user_id,
                actor_id=user.id,
                action_type="ban",
                reason=reason,
            )
            db.add(mod_action)

        elif action_type == "unmute":
            target.is_muted = False
            target.mute_until = None
            mod_action = ModAction(
                group_id=group_id,
                target_user_id=target_user_id,
                actor_id=user.id,
                action_type="unmute",
            )
            db.add(mod_action)

        elif action_type == "unban":
            target.is_banned = False
            target.ban_until = None
            mod_action = ModAction(
                group_id=group_id,
                target_user_id=target_user_id,
                actor_id=user.id,
                action_type="unban",
            )
            db.add(mod_action)

        else:
            await websocket.send_json({"type": "error", "message": f"Unknown action: {action_type}"})
            return

        await db.commit()

    await websocket.send_json({
        "type": "action_result",
        "action": action_type,
        "user_id": target_user_id,
        "success": True,
    })

    await publish_feed_event(group_id, {
        "type": "mod_action",
        "action": action_type,
        "target_user_id": target_user_id,
        "actor_id": user.id,
        "reason": reason,
    })


async def publish_feed_event(group_id: int, event: dict):
    """Publish an event to the group's feed channel."""
    try:
        redis = await get_redis()
        channel = f"nexus:g{group_id}:feed"
        await redis.publish(channel, json.dumps(event))
    except Exception as e:
        logger.warning(f"Failed to publish feed event for group {group_id}: {e}")


@router.get("/groups/{group_id}/feed/recent")
async def get_recent_feed(
    group_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent feed events for a group (last N cached events)."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()
    if not member or member.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Admin access required")

    redis = await get_redis()
    key = f"nexus:g{group_id}:feed:history"
    raw_items = await redis.lrange(key, 0, limit - 1)

    events = []
    for raw in raw_items:
        try:
            events.append(json.loads(raw))
        except Exception:
            pass

    return {"events": events, "total": len(events)}


@router.get("/groups/{group_id}/feed/ws-count")
async def get_ws_connection_count(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get number of active WebSocket connections for a group."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()
    if not member or member.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"connections": manager.connection_count(group_id)}
