"""
Message Threading and Conversation Context System

Telegram has reply threads but bots have no native concept of a conversation
thread as a unit. This system builds thread-aware context where the bot
understands that multiple messages are part of the same conversation.

Features:
- Thread detection and tracking
- Conversation summarization
- Thread-level moderation
- Context-aware responses
- Thread archival and search
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Coroutine
from collections import deque

from aiogram.types import Message, Update

from shared.redis_client import GroupScopedRedis, get_group_redis


class ThreadStatus(str, Enum):
    """Status of a conversation thread."""
    ACTIVE = "active"
    INACTIVE = "inactive"  # No activity for a while
    LOCKED = "locked"  # Thread locked by mod
    ARCHIVED = "archived"  # Archived
    MODERATED = "moderated"  # Under moderation review


class ThreadType(str, Enum):
    """Types of conversation threads."""
    GENERAL = "general"
    QUESTION = "question"
    DISCUSSION = "discussion"
    DEBATE = "debate"
    SUPPORT = "support"
    ANNOUNCEMENT = "announcement"
    EVENT = "event"
    POLICY = "policy"


@dataclass
class ThreadParticipant:
    """Participant in a thread."""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    role: str = "member"
    join_time: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    last_active: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThreadMessage:
    """A message within a thread context."""
    message_id: int
    user_id: int
    text: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    is_reply: bool = False
    reply_to_message_id: Optional[int] = None
    media_type: Optional[str] = None
    has_entities: bool = False
    sentiment_score: Optional[float] = None
    
    # Moderation
    was_edited: bool = False
    was_deleted: bool = False
    moderation_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "is_reply": self.is_reply,
            "reply_to_message_id": self.reply_to_message_id,
            "media_type": self.media_type,
            "has_entities": self.has_entities,
            "sentiment_score": self.sentiment_score,
            "was_edited": self.was_edited,
            "was_deleted": self.was_deleted,
            "moderation_flags": self.moderation_flags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadMessage":
        return cls(
            message_id=data["message_id"],
            user_id=data["user_id"],
            text=data.get("text"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_reply=data.get("is_reply", False),
            reply_to_message_id=data.get("reply_to_message_id"),
            media_type=data.get("media_type"),
            has_entities=data.get("has_entities", False),
            sentiment_score=data.get("sentiment_score"),
            was_edited=data.get("was_edited", False),
            was_deleted=data.get("was_deleted", False),
            moderation_flags=data.get("moderation_flags", []),
        )


@dataclass
class ThreadSummary:
    """Summary of a conversation thread."""
    thread_id: str
    created_at: datetime
    summary_text: str
    key_points: List[str] = field(default_factory=list)
    participants_mentioned: List[int] = field(default_factory=list)
    sentiment_overall: str = "neutral"  # positive, negative, neutral, mixed
    topic_keywords: List[str] = field(default_factory=list)
    message_count: int = 0
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "created_at": self.created_at.isoformat(),
            "summary_text": self.summary_text,
            "key_points": self.key_points,
            "participants_mentioned": self.participants_mentioned,
            "sentiment_overall": self.sentiment_overall,
            "topic_keywords": self.topic_keywords,
            "message_count": self.message_count,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class ConversationThread:
    """
    A conversation thread - multiple messages that form a coherent discussion.
    """
    # Identity
    thread_id: str
    group_id: int
    root_message_id: int  # The message that started the thread
    
    # Thread properties
    thread_type: ThreadType = ThreadType.GENERAL
    status: ThreadStatus = ThreadStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # Participants
    participants: Dict[int, ThreadParticipant] = field(default_factory=dict)
    participant_order: List[int] = field(default_factory=list)  # Order of first participation
    
    # Messages (circular buffer - limited history)
    messages: deque = field(default_factory=lambda: deque(maxlen=1000))
    message_count: int = 0
    
    # Thread metadata
    title: Optional[str] = None
    topic: Optional[str] = None
    
    # Engagement metrics
    reply_count: int = 0
    reaction_count: int = 0
    unique_participants: int = 0
    
    # Moderation
    is_pinned: bool = False
    is_announcement: bool = False
    slow_mode_delay: int = 0  # Seconds between messages
    restricted_users: Set[int] = field(default_factory=set)
    
    # Summary
    summary: Optional[ThreadSummary] = None
    last_summarized: Optional[datetime] = None
    
    # Tags and classification
    tags: Set[str] = field(default_factory=set)
    auto_classified: bool = False
    
    # Related threads (forks, merges)
    parent_thread_id: Optional[str] = None
    forked_from_message_id: Optional[int] = None
    child_thread_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "thread_id": self.thread_id,
            "group_id": self.group_id,
            "root_message_id": self.root_message_id,
            "thread_type": self.thread_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "participants": {
                str(uid): {
                    "user_id": p.user_id,
                    "username": p.username,
                    "first_name": p.first_name,
                    "role": p.role,
                    "join_time": p.join_time.isoformat(),
                    "message_count": p.message_count,
                    "last_active": p.last_active.isoformat(),
                }
                for uid, p in self.participants.items()
            },
            "participant_order": self.participant_order,
            "messages": [m.to_dict() for m in self.messages],
            "message_count": self.message_count,
            "title": self.title,
            "topic": self.topic,
            "reply_count": self.reply_count,
            "reaction_count": self.reaction_count,
            "unique_participants": self.unique_participants,
            "is_pinned": self.is_pinned,
            "is_announcement": self.is_announcement,
            "slow_mode_delay": self.slow_mode_delay,
            "restricted_users": list(self.restricted_users),
            "summary": self.summary.to_dict() if self.summary else None,
            "last_summarized": self.last_summarized.isoformat() if self.last_summarized else None,
            "tags": list(self.tags),
            "auto_classified": self.auto_classified,
            "parent_thread_id": self.parent_thread_id,
            "forked_from_message_id": self.forked_from_message_id,
            "child_thread_ids": self.child_thread_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationThread":
        """Create from dictionary."""
        thread = cls(
            thread_id=data["thread_id"],
            group_id=data["group_id"],
            root_message_id=data["root_message_id"],
            thread_type=ThreadType(data.get("thread_type", "general")),
            status=ThreadStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            message_count=data.get("message_count", 0),
            title=data.get("title"),
            topic=data.get("topic"),
            reply_count=data.get("reply_count", 0),
            reaction_count=data.get("reaction_count", 0),
            unique_participants=data.get("unique_participants", 0),
            is_pinned=data.get("is_pinned", False),
            is_announcement=data.get("is_announcement", False),
            slow_mode_delay=data.get("slow_mode_delay", 0),
            restricted_users=set(data.get("restricted_users", [])),
            last_summarized=datetime.fromisoformat(data["last_summarized"]) if data.get("last_summarized") else None,
            tags=set(data.get("tags", [])),
            auto_classified=data.get("auto_classified", False),
            parent_thread_id=data.get("parent_thread_id"),
            forked_from_message_id=data.get("forked_from_message_id"),
            child_thread_ids=data.get("child_thread_ids", []),
        )
        
        # Restore participants
        for uid_str, pdata in data.get("participants", {}).items():
            uid = int(uid_str)
            thread.participants[uid] = ThreadParticipant(
                user_id=pdata["user_id"],
                username=pdata.get("username"),
                first_name=pdata.get("first_name"),
                role=pdata.get("role", "member"),
                join_time=datetime.fromisoformat(pdata["join_time"]),
                message_count=pdata.get("message_count", 0),
                last_active=datetime.fromisoformat(pdata["last_active"]),
            )
        
        thread.participant_order = data.get("participant_order", [])
        
        # Restore messages
        for mdata in data.get("messages", []):
            thread.messages.append(ThreadMessage.from_dict(mdata))
        
        # Restore summary
        if data.get("summary"):
            sdata = data["summary"]
            thread.summary = ThreadSummary(
                thread_id=sdata["thread_id"],
                created_at=datetime.fromisoformat(sdata["created_at"]),
                summary_text=sdata["summary_text"],
                key_points=sdata.get("key_points", []),
                participants_mentioned=sdata.get("participants_mentioned", []),
                sentiment_overall=sdata.get("sentiment_overall", "neutral"),
                topic_keywords=sdata.get("topic_keywords", []),
                message_count=sdata.get("message_count", 0),
                generated_at=datetime.fromisoformat(sdata["generated_at"]),
            )
        
        return thread
    
    def add_message(self, message: ThreadMessage) -> bool:
        """
        Add a message to the thread.
        
        Returns:
            True if message was added, False if thread is locked/restricted
        """
        if self.status in (ThreadStatus.LOCKED, ThreadStatus.ARCHIVED):
            return False
        
        if message.user_id in self.restricted_users:
            return False
        
        # Check slow mode
        if self.slow_mode_delay > 0 and message.user_id in self.participants:
            last_active = self.participants[message.user_id].last_active
            if (datetime.utcnow() - last_active).total_seconds() < self.slow_mode_delay:
                return False
        
        # Add message
        self.messages.append(message)
        self.message_count += 1
        self.last_activity = message.timestamp
        
        # Update participant
        if message.user_id not in self.participants:
            self.participants[message.user_id] = ThreadParticipant(
                user_id=message.user_id,
            )
            self.participant_order.append(message.user_id)
            self.unique_participants = len(self.participants)
        
        participant = self.participants[message.user_id]
        participant.message_count += 1
        participant.last_active = message.timestamp
        
        if message.is_reply:
            self.reply_count += 1
        
        return True
    
    def get_participant_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for each participant."""
        return {
            uid: {
                "message_count": p.message_count,
                "percentage": (p.message_count / self.message_count * 100) if self.message_count > 0 else 0,
                "first_post": p.join_time.isoformat(),
                "last_active": p.last_active.isoformat(),
            }
            for uid, p in self.participants.items()
        }
    
    def get_conversation_flow(self) -> List[Dict[str, Any]]:
        """Get the conversation flow with reply chains."""
        flow = []
        message_map = {m.message_id: m for m in self.messages}
        
        for msg in self.messages:
            entry = {
                "message_id": msg.message_id,
                "user_id": msg.user_id,
                "timestamp": msg.timestamp.isoformat(),
                "is_reply": msg.is_reply,
            }
            
            if msg.is_reply and msg.reply_to_message_id in message_map:
                parent = message_map[msg.reply_to_message_id]
                entry["reply_to"] = {
                    "message_id": parent.message_id,
                    "user_id": parent.user_id,
                }
            
            flow.append(entry)
        
        return flow
    
    def get_active_branch(self, lookback: int = 50) -> List[ThreadMessage]:
        """
        Get the active conversation branch - the most recent messages
        that form a coherent sub-conversation.
        """
        if not self.messages:
            return []
        
        recent = list(self.messages)[-lookback:]
        
        # Find messages that are replies to each other
        message_ids = {m.message_id for m in recent}
        branch = []
        
        for msg in reversed(recent):
            if not msg.is_reply:
                # Root of a sub-conversation
                branch.insert(0, msg)
            elif msg.reply_to_message_id in message_ids:
                # Part of the chain
                branch.insert(0, msg)
        
        return branch


class ThreadContextManager:
    """
    Manages conversation threads using Redis for active threads
    and database for archival.
    """
    
    # Thread detection settings
    THREAD_TIMEOUT_SECONDS = 3600  # 1 hour of inactivity
    MAX_THREAD_DEPTH = 10  # Max reply chain depth
    MIN_THREAD_MESSAGES = 3  # Minimum messages to form a thread
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
        self._classification_handlers: List[Callable] = []
        self._moderation_handlers: List[Callable] = []
    
    def _thread_key(self, thread_id: str) -> str:
        return f"thread:{thread_id}"
    
    def _message_thread_map_key(self) -> str:
        return "thread:message_map"
    
    def _active_threads_key(self) -> str:
        return "threads:active"
    
    def _user_threads_key(self, user_id: int) -> str:
        return f"threads:user:{user_id}"
    
    def _generate_thread_id(self, group_id: int, root_message_id: int) -> str:
        """Generate a unique thread ID."""
        hash_input = f"{group_id}:{root_message_id}:{datetime.utcnow().timestamp()}"
        hash_val = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"t_{group_id}_{root_message_id}_{hash_val}"
    
    async def detect_or_create_thread(
        self,
        group_id: int,
        message: Message,
        user_role: str = "member"
    ) -> Tuple[Optional[ConversationThread], bool]:
        """
        Detect if message belongs to existing thread or create new one.
        
        Returns:
            (thread, is_new) - thread may be None if message doesn't form thread
        """
        # Check if message is a reply
        if message.reply_to_message:
            parent_id = message.reply_to_message.message_id
            
            # Check if parent is part of a thread
            thread_id = await self._get_thread_for_message(parent_id)
            
            if thread_id:
                # Add to existing thread
                thread = await self.get_thread(thread_id)
                if thread:
                    thread_msg = self._convert_message(message)
                    if thread.add_message(thread_msg):
                        await self._save_thread(thread)
                        await self._map_message_to_thread(message.message_id, thread_id)
                        return thread, False
            else:
                # Check if we should create a thread from this reply chain
                parent_thread = await self._check_thread_worthy(group_id, message.reply_to_message)
                if parent_thread:
                    thread_msg = self._convert_message(message)
                    parent_thread.add_message(thread_msg)
                    await self._save_thread(parent_thread)
                    await self._map_message_to_thread(message.message_id, parent_thread.thread_id)
                    return parent_thread, False
        
        # Check if this message starts a thread-worthy conversation
        # (e.g., question, poll, announcement)
        thread_type = self._classify_message_intent(message)
        
        if thread_type:
            thread = await self.create_thread(
                group_id=group_id,
                root_message=message,
                thread_type=thread_type,
            )
            return thread, True
        
        return None, False
    
    async def create_thread(
        self,
        group_id: int,
        root_message: Message,
        thread_type: ThreadType = ThreadType.GENERAL,
        title: Optional[str] = None,
    ) -> ConversationThread:
        """Create a new conversation thread."""
        thread_id = self._generate_thread_id(group_id, root_message.message_id)
        
        thread = ConversationThread(
            thread_id=thread_id,
            group_id=group_id,
            root_message_id=root_message.message_id,
            thread_type=thread_type,
            title=title,
        )
        
        # Add root message
        root_msg = self._convert_message(root_message)
        thread.add_message(root_msg)
        
        await self._save_thread(thread)
        await self._map_message_to_thread(root_message.message_id, thread_id)
        await self.redis.sadd(self._active_threads_key(), thread_id)
        
        return thread
    
    async def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a thread by ID."""
        data = await self.redis.get_json(self._thread_key(thread_id))
        if not data:
            return None
        return ConversationThread.from_dict(data)
    
    async def update_thread(self, thread: ConversationThread) -> bool:
        """Update a thread."""
        await self._save_thread(thread)
        return True
    
    async def add_message_to_thread(
        self,
        thread_id: str,
        message: Message
    ) -> bool:
        """Add a message to an existing thread."""
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        thread_msg = self._convert_message(message)
        success = thread.add_message(thread_msg)
        
        if success:
            await self._save_thread(thread)
            await self._map_message_to_thread(message.message_id, thread_id)
        
        return success
    
    async def fork_thread(
        self,
        parent_thread_id: str,
        from_message_id: int,
        new_title: Optional[str] = None,
    ) -> Optional[ConversationThread]:
        """
        Fork a thread from a specific message.
        Creates a new thread with the parent thread's messages from that point.
        """
        parent = await self.get_thread(parent_thread_id)
        if not parent:
            return None
        
        # Find the fork point
        fork_idx = None
        for i, msg in enumerate(parent.messages):
            if msg.message_id == from_message_id:
                fork_idx = i
                break
        
        if fork_idx is None:
            return None
        
        # Create new thread
        thread_id = self._generate_thread_id(parent.group_id, from_message_id)
        
        child = ConversationThread(
            thread_id=thread_id,
            group_id=parent.group_id,
            root_message_id=from_message_id,
            parent_thread_id=parent_thread_id,
            forked_from_message_id=from_message_id,
            title=new_title or f"Fork of: {parent.title or 'Thread'}",
        )
        
        # Copy messages from fork point
        for msg in list(parent.messages)[fork_idx:]:
            child.messages.append(msg)
            child.message_count += 1
            if msg.user_id not in child.participants:
                child.participants[msg.user_id] = ThreadParticipant(user_id=msg.user_id)
                child.participant_order.append(msg.user_id)
        
        child.unique_participants = len(child.participants)
        
        # Update parent
        parent.child_thread_ids.append(thread_id)
        await self._save_thread(parent)
        await self._save_thread(child)
        
        return child
    
    async def get_thread_for_message(self, message_id: int) -> Optional[str]:
        """Get thread ID for a specific message."""
        return await self.redis.hget(self._message_thread_map_key(), str(message_id))
    
    async def get_active_threads(self, limit: int = 100) -> List[ConversationThread]:
        """Get all active threads."""
        thread_ids = await self.redis.smembers(self._active_threads_key())
        threads = []
        
        for tid in list(thread_ids)[:limit]:
            thread = await self.get_thread(tid)
            if thread and thread.status == ThreadStatus.ACTIVE:
                threads.append(thread)
        
        return threads
    
    async def get_threads_by_user(self, user_id: int) -> List[ConversationThread]:
        """Get all threads a user has participated in."""
        thread_ids = await self.redis.smembers(self._user_threads_key(user_id))
        threads = []
        
        for tid in thread_ids:
            thread = await self.get_thread(tid)
            if thread:
                threads.append(thread)
        
        return threads
    
    async def lock_thread(
        self,
        thread_id: str,
        locked_by: int,
        reason: Optional[str] = None
    ) -> bool:
        """Lock a thread to prevent new messages."""
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        thread.status = ThreadStatus.LOCKED
        thread.restricted_users = set(thread.participants.keys())  # Lock everyone
        
        if reason:
            thread.tags.add(f"locked:{reason}")
        
        await self._save_thread(thread)
        return True
    
    async def unlock_thread(self, thread_id: str) -> bool:
        """Unlock a thread."""
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        thread.status = ThreadStatus.ACTIVE
        thread.restricted_users.clear()
        thread.tags.discard("locked")
        
        await self._save_thread(thread)
        return True
    
    async def archive_thread(self, thread_id: str) -> bool:
        """Archive a thread."""
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        thread.status = ThreadStatus.ARCHIVED
        await self._save_thread(thread)
        await self.redis.srem(self._active_threads_key(), thread_id)
        
        # Generate summary if not exists
        if not thread.summary:
            await self.summarize_thread(thread_id)
        
        # Persist to database
        await self._persist_to_database(thread)
        
        return True
    
    async def moderate_thread(
        self,
        thread_id: str,
        action: str,
        moderator_id: int,
        reason: str,
        target_user_id: Optional[int] = None,
    ) -> bool:
        """
        Perform moderation action on a thread.
        
        Actions: lock, archive, delete, restrict_user, pin
        """
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        if action == "lock":
            await self.lock_thread(thread_id, moderator_id, reason)
        elif action == "archive":
            await self.archive_thread(thread_id)
        elif action == "restrict_user" and target_user_id:
            thread.restricted_users.add(target_user_id)
            await self._save_thread(thread)
        elif action == "unrestrict_user" and target_user_id:
            thread.restricted_users.discard(target_user_id)
            await self._save_thread(thread)
        elif action == "pin":
            thread.is_pinned = True
            await self._save_thread(thread)
        elif action == "unpin":
            thread.is_pinned = False
            await self._save_thread(thread)
        elif action == "set_slow_mode":
            # Parse delay from reason
            try:
                delay = int(reason)
                thread.slow_mode_delay = delay
                await self._save_thread(thread)
            except ValueError:
                pass
        
        # Log moderation action
        thread.tags.add(f"mod:{action}")
        await self._save_thread(thread)
        
        return True
    
    async def summarize_thread(self, thread_id: str) -> Optional[ThreadSummary]:
        """Generate a summary of a thread."""
        thread = await self.get_thread(thread_id)
        if not thread or thread.message_count < self.MIN_THREAD_MESSAGES:
            return None
        
        # Build summary
        summary = ThreadSummary(
            thread_id=thread_id,
            created_at=thread.created_at,
            summary_text=self._generate_summary_text(thread),
            key_points=self._extract_key_points(thread),
            participants_mentioned=list(thread.participants.keys())[:10],
            message_count=thread.message_count,
        )
        
        # Simple sentiment analysis
        positive_words = {"good", "great", "awesome", "love", "thanks", "helpful", "agree"}
        negative_words = {"bad", "terrible", "hate", "wrong", "disagree", "annoying"}
        
        positive_count = 0
        negative_count = 0
        
        for msg in thread.messages:
            if msg.text:
                text_lower = msg.text.lower()
                positive_count += sum(1 for w in positive_words if w in text_lower)
                negative_count += sum(1 for w in negative_words if w in text_lower)
        
        if positive_count > negative_count * 2:
            summary.sentiment_overall = "positive"
        elif negative_count > positive_count * 2:
            summary.sentiment_overall = "negative"
        elif positive_count > 0 or negative_count > 0:
            summary.sentiment_overall = "mixed"
        else:
            summary.sentiment_overall = "neutral"
        
        # Extract keywords (simple frequency)
        word_freq = {}
        for msg in thread.messages:
            if msg.text:
                for word in msg.text.lower().split():
                    if len(word) > 4:
                        word_freq[word] = word_freq.get(word, 0) + 1
        
        summary.topic_keywords = sorted(word_freq.keys(), key=lambda w: word_freq[w], reverse=True)[:10]
        
        thread.summary = summary
        thread.last_summarized = datetime.utcnow()
        await self._save_thread(thread)
        
        return summary
    
    async def cleanup_inactive_threads(self, max_age_hours: int = 24) -> int:
        """Mark inactive threads and archive old ones."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        thread_ids = await self.redis.smembers(self._active_threads_key())
        
        cleaned = 0
        for tid in thread_ids:
            thread = await self.get_thread(tid)
            if thread and thread.last_activity < cutoff:
                if thread.status == ThreadStatus.INACTIVE:
                    # Archive if already inactive
                    await self.archive_thread(tid)
                else:
                    # Mark as inactive
                    thread.status = ThreadStatus.INACTIVE
                    await self._save_thread(thread)
                cleaned += 1
        
        return cleaned
    
    def register_classification_handler(self, handler: Callable):
        """Register a handler for message classification."""
        self._classification_handlers.append(handler)
    
    def register_moderation_handler(self, handler: Callable):
        """Register a handler for thread moderation events."""
        self._moderation_handlers.append(handler)
    
    def _convert_message(self, message: Message) -> ThreadMessage:
        """Convert aiogram Message to ThreadMessage."""
        return ThreadMessage(
            message_id=message.message_id,
            user_id=message.from_user.id if message.from_user else 0,
            text=message.text or message.caption,
            timestamp=message.date,
            is_reply=message.reply_to_message is not None,
            reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
            media_type=message.content_type if message.content_type != "text" else None,
            has_entities=bool(message.entities or message.caption_entities),
        )
    
    def _classify_message_intent(self, message: Message) -> Optional[ThreadType]:
        """Classify message to determine if it should start a thread."""
        text = (message.text or message.caption or "").lower()
        
        # Question detection
        if any(text.startswith(w) for w in ["what", "how", "why", "when", "where", "who", "?", "does", "can", "is"]) or "?" in text:
            return ThreadType.QUESTION
        
        # Event detection
        if any(w in text for w in ["event", "meetup", "schedule", "plan", "when:", "date:"]):
            return ThreadType.EVENT
        
        # Policy/announcement detection
        if any(w in text for w in ["rule", "policy", "announcement", "update", "notice", "important"]):
            return ThreadType.ANNOUNCEMENT
        
        # Check custom handlers
        for handler in self._classification_handlers:
            result = handler(message)
            if result:
                return result
        
        return None
    
    async def _check_thread_worthy(
        self,
        group_id: int,
        message: Message
    ) -> Optional[ConversationThread]:
        """Check if a message has enough replies to form a thread."""
        # This would check message history
        # For now, create thread if message looks important
        thread_type = self._classify_message_intent(message)
        if thread_type:
            return await self.create_thread(group_id, message, thread_type)
        return None
    
    async def _get_thread_for_message(self, message_id: int) -> Optional[str]:
        """Get thread ID for a message."""
        return await self.redis.hget(self._message_thread_map_key(), str(message_id))
    
    async def _map_message_to_thread(self, message_id: int, thread_id: str):
        """Map a message to its thread."""
        await self.redis.hset(
            self._message_thread_map_key(),
            str(message_id),
            thread_id
        )
        # Expire mapping after a while
        await self.redis.expire(self._message_thread_map_key(), 86400 * 7)
    
    async def _save_thread(self, thread: ConversationThread):
        """Save thread to Redis."""
        key = self._thread_key(thread.thread_id)
        ttl = 86400 * 2 if thread.status == ThreadStatus.ACTIVE else 3600
        await self.redis.set_json(key, thread.to_dict(), expire=ttl)
    
    async def _persist_to_database(self, thread: ConversationThread):
        """Persist thread to database for long-term storage."""
        # Implementation depends on your DB layer
        pass
    
    def _generate_summary_text(self, thread: ConversationThread) -> str:
        """Generate a text summary of the thread."""
        if thread.title:
            return f"Discussion about: {thread.title}"
        
        # Get first and last messages
        messages = list(thread.messages)
        if not messages:
            return "Empty thread"
        
        first = messages[0].text or "[Media]"
        return f"Thread starting with: {first[:100]}..."
    
    def _extract_key_points(self, thread: ConversationThread) -> List[str]:
        """Extract key points from the thread."""
        points = []
        
        # Look for messages with reactions or replies
        reply_targets = set()
        for msg in thread.messages:
            if msg.reply_to_message_id:
                reply_targets.add(msg.reply_to_message_id)
        
        # Messages that get replies are often key points
        for msg in thread.messages:
            if msg.message_id in reply_targets and msg.text:
                points.append(msg.text[:200])
        
        return points[:5]  # Top 5 key points


class ThreadAwareContext:
    """
    Context wrapper that adds thread awareness to NexusContext.
    
    This allows handlers to understand the conversation thread context
    and make decisions based on thread state.
    """
    
    def __init__(self, base_context: "NexusContext", thread_manager: ThreadContextManager):
        self.ctx = base_context
        self.thread_manager = thread_manager
        self._current_thread: Optional[ConversationThread] = None
    
    async def get_current_thread(self) -> Optional[ConversationThread]:
        """Get the thread for the current message."""
        if self._current_thread:
            return self._current_thread
        
        if not self.ctx.message:
            return None
        
        thread_id = await self.thread_manager.get_thread_for_message(
            self.ctx.message.message_id
        )
        
        if not thread_id and self.ctx.message.reply_to_message:
            thread_id = await self.thread_manager.get_thread_for_message(
                self.ctx.message.reply_to_message.message_id
            )
        
        if thread_id:
            self._current_thread = await self.thread_manager.get_thread(thread_id)
        
        return self._current_thread
    
    async def ensure_thread(self) -> Optional[ConversationThread]:
        """Ensure current message is part of a thread, creating one if needed."""
        thread = await self.get_current_thread()
        if thread:
            return thread
        
        if not self.ctx.message:
            return None
        
        thread, is_new = await self.thread_manager.detect_or_create_thread(
            group_id=self.ctx.group.id,
            message=self.ctx.message,
            user_role=self.ctx.user.role.value if self.ctx.user else "member",
        )
        
        if thread:
            self._current_thread = thread
        
        return thread
    
    def is_thread_root(self) -> bool:
        """Check if current message is the root of its thread."""
        if not self._current_thread or not self.ctx.message:
            return False
        return self.ctx.message.message_id == self._current_thread.root_message_id
    
    def get_thread_depth(self) -> int:
        """Get how deep in the reply chain this message is."""
        if not self._current_thread or not self.ctx.message:
            return 0
        
        depth = 0
        for msg in self._current_thread.messages:
            if msg.message_id == self.ctx.message.message_id:
                # Count reply chain
                current = msg
                while current.is_reply:
                    depth += 1
                    # Find parent
                    for m in self._current_thread.messages:
                        if m.message_id == current.reply_to_message_id:
                            current = m
                            break
                    else:
                        break
                break
        
        return depth
    
    async def reply_in_thread(self, text: str, **kwargs) -> Message:
        """Reply in the current thread context."""
        if self._current_thread and self.ctx.message:
            # Reply to the last message in thread or current message
            return await self.ctx.reply(text, **kwargs)
        return await self.ctx.reply(text, **kwargs)
    
    async def summarize_current_thread(self) -> Optional[str]:
        """Generate and return a summary of the current thread."""
        thread = await self.get_current_thread()
        if not thread:
            return None
        
        summary = await self.thread_manager.summarize_thread(thread.thread_id)
        if summary:
            return summary.summary_text
        return None
    
    async def moderate_thread(self, action: str, reason: str) -> bool:
        """Perform moderation on the current thread."""
        thread = await self.get_current_thread()
        if not thread or not self.ctx.user:
            return False
        
        return await self.thread_manager.moderate_thread(
            thread_id=thread.thread_id,
            action=action,
            moderator_id=self.ctx.user.user_id,
            reason=reason,
        )
