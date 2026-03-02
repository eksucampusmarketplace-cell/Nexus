"""
Content Moderation Pipeline

Multi-stage content filtering and analysis system that processes
all messages through configurable stages with pluggable analyzers.

Stages:
1. Pre-filter (fast regex, allowlist/blocklist)
2. Content extraction (entities, links, mentions)
3. Feature analysis (spam detection, toxicity, etc.)
4. Policy enforcement (actions based on scores)
5. Post-processing (logging, notifications)

Features:
- Async pipeline processing
- Configurable per-group policies
- Pluggable analyzers
- Real-time and batch processing modes
- Confidence scoring
- Appeal system
"""

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple
from abc import ABC, abstractmethod

from aiogram.types import Message, ContentType

from shared.redis_client import GroupScopedRedis


class ContentType_(str, Enum):
    """Extended content types."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ANIMATION = "animation"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"
    LINK = "link"
    HASHTAG = "hashtag"
    MENTION = "mention"
    COMMAND = "command"
    EMAIL = "email"
    PHONE = "phone"


class RiskLevel(str, Enum):
    """Risk levels for content."""
    NONE = "none"  # No risk
    LOW = "low"  # Minor issue
    MEDIUM = "medium"  # Moderate concern
    HIGH = "high"  # Serious issue
    CRITICAL = "critical"  # Immediate action required


class ActionDecision(str, Enum):
    """Possible moderation decisions."""
    ALLOW = "allow"  # No action
    FLAG = "flag"  # Mark for review
    DELETE = "delete"  # Delete message
    RESTRICT = "restrict"  # Restrict user
    MUTE = "mute"  # Mute user
    KICK = "kick"  # Kick user
    BAN = "ban"  # Ban user
    SHADOWBAN = "shadowban"  # Shadowban (messages hidden)


@dataclass
class ContentFeatures:
    """Extracted features from content."""
    # Text features
    text_length: int = 0
    word_count: int = 0
    emoji_count: int = 0
    caps_ratio: float = 0.0
    digit_ratio: float = 0.0
    special_char_ratio: float = 0.0
    
    # Linguistic
    language: Optional[str] = None
    sentiment_score: float = 0.0  # -1 to 1
    
    # Links and media
    url_count: int = 0
    urls: List[str] = field(default_factory=list)
    file_types: List[str] = field(default_factory=list)
    file_hashes: List[str] = field(default_factory=list)
    
    # Entities
    mention_count: int = 0
    mentions: List[int] = field(default_factory=list)
    hashtag_count: int = 0
    hashtags: List[str] = field(default_factory=list)
    command_count: int = 0
    
    # Behavioral
    message_frequency: float = 0.0  # messages per minute
    duplicate_count: int = 0  # Similar messages seen
    forwarded: bool = False
    forward_from_chat: Optional[int] = None
    
    # Context
    thread_depth: int = 0
    reply_time_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_length": self.text_length,
            "word_count": self.word_count,
            "emoji_count": self.emoji_count,
            "caps_ratio": self.caps_ratio,
            "digit_ratio": self.digit_ratio,
            "special_char_ratio": self.special_char_ratio,
            "language": self.language,
            "sentiment_score": self.sentiment_score,
            "url_count": self.url_count,
            "urls": self.urls,
            "file_types": self.file_types,
            "file_hashes": self.file_hashes,
            "mention_count": self.mention_count,
            "mentions": self.mentions,
            "hashtag_count": self.hashtag_count,
            "hashtags": self.hashtags,
            "command_count": self.command_count,
            "message_frequency": self.message_frequency,
            "duplicate_count": self.duplicate_count,
            "forwarded": self.forwarded,
            "forward_from_chat": self.forward_from_chat,
            "thread_depth": self.thread_depth,
            "reply_time_seconds": self.reply_time_seconds,
        }


@dataclass
class AnalysisResult:
    """Result from a single analyzer."""
    analyzer_name: str
    analyzer_version: str
    risk_level: RiskLevel
    confidence: float  # 0.0 to 1.0
    score: float  # Raw score
    category: str  # spam, toxicity, etc.
    flagged: bool
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "analyzer_version": self.analyzer_version,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "score": self.score,
            "category": self.category,
            "flagged": self.flagged,
            "reasons": self.reasons,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class PipelineDecision:
    """Final decision from the pipeline."""
    decision: ActionDecision
    risk_level: RiskLevel
    confidence: float
    primary_reason: str
    all_reasons: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    requires_review: bool = False
    review_priority: int = 0  # 1-10
    
    # For appeals
    appealable: bool = False
    appeal_deadline: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "primary_reason": self.primary_reason,
            "all_reasons": self.all_reasons,
            "actions_taken": self.actions_taken,
            "requires_review": self.requires_review,
            "review_priority": self.review_priority,
            "appealable": self.appealable,
            "appeal_deadline": self.appeal_deadline.isoformat() if self.appeal_deadline else None,
        }


@dataclass
class ContentRecord:
    """A content item being processed."""
    # Identity
    record_id: str
    message_id: int
    chat_id: int
    user_id: int
    group_id: int
    
    # Content
    content_type: ContentType_
    text: Optional[str] = None
    raw_message: Optional[Dict[str, Any]] = None
    
    # Processing
    features: ContentFeatures = field(default_factory=ContentFeatures)
    analysis_results: List[AnalysisResult] = field(default_factory=list)
    decision: Optional[PipelineDecision] = None
    
    # Metadata
    received_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0
    
    # Status
    status: str = "pending"  # pending, processing, completed, error
    error_message: Optional[str] = None
    
    # Moderation
    moderated_by: Optional[int] = None
    moderated_at: Optional[datetime] = None
    appeal_status: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "content_type": self.content_type.value,
            "text": self.text,
            "features": self.features.to_dict(),
            "analysis_results": [r.to_dict() for r in self.analysis_results],
            "decision": self.decision.to_dict() if self.decision else None,
            "received_at": self.received_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time_ms": self.processing_time_ms,
            "status": self.status,
            "error_message": self.error_message,
            "moderated_by": self.moderated_by,
            "moderated_at": self.moderated_at.isoformat() if self.moderated_at else None,
            "appeal_status": self.appeal_status,
        }


class ContentAnalyzer(ABC):
    """Base class for content analyzers."""
    
    name: str = "base"
    version: str = "1.0.0"
    categories: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    async def analyze(self, record: ContentRecord) -> AnalysisResult:
        """Analyze content and return result."""
        pass
    
    async def initialize(self):
        """Initialize the analyzer (load models, etc)."""
        pass
    
    async def shutdown(self):
        """Cleanup resources."""
        pass


class SpamAnalyzer(ContentAnalyzer):
    """Analyzer for spam detection."""
    
    name = "spam_detector"
    version = "2.1.0"
    categories = ["spam", "promotion"]
    
    # Patterns
    URL_SHORTENERS = ["bit.ly", "t.co", "goo.gl", "tinyurl", "ow.ly"]
    SPAM_KEYWORDS = [
        "click here", "limited time", "act now", "free money",
        "make money", "earn $", "100% free", "no obligation",
    ]
    
    async def analyze(self, record: ContentRecord) -> AnalysisResult:
        start_time = datetime.utcnow()
        
        score = 0.0
        reasons = []
        
        # Check URL shorteners
        for url in record.features.urls:
            if any(shortener in url.lower() for shortener in self.URL_SHORTENERS):
                score += 0.3
                reasons.append(f"Uses URL shortener: {url}")
        
        # Check keyword density
        text_lower = (record.text or "").lower()
        keyword_matches = sum(1 for kw in self.SPAM_KEYWORDS if kw in text_lower)
        if keyword_matches > 0:
            score += min(keyword_matches * 0.15, 0.5)
            reasons.append(f"Contains {keyword_matches} spam keywords")
        
        # Check mention spam
        if record.features.mention_count > 5:
            score += 0.2
            reasons.append(f"Excessive mentions ({record.features.mention_count})")
        
        # Check forwarding patterns
        if record.features.forwarded and record.features.forward_from_chat:
            score += 0.15
            reasons.append("Forwarded from channel")
        
        # High frequency posting
        if record.features.message_frequency > 10:  # More than 10 msg/min
            score += 0.25
            reasons.append("High message frequency")
        
        # Determine risk level
        if score >= 0.8:
            risk = RiskLevel.CRITICAL
        elif score >= 0.6:
            risk = RiskLevel.HIGH
        elif score >= 0.4:
            risk = RiskLevel.MEDIUM
        elif score >= 0.2:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.NONE
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AnalysisResult(
            analyzer_name=self.name,
            analyzer_version=self.version,
            risk_level=risk,
            confidence=min(score + 0.2, 1.0),
            score=score,
            category="spam",
            flagged=score >= 0.4,
            reasons=reasons,
            processing_time_ms=processing_time,
        )


class ToxicityAnalyzer(ContentAnalyzer):
    """Analyzer for toxic/harmful content."""
    
    name = "toxicity_detector"
    version = "1.5.0"
    categories = ["toxicity", "harassment", "hate_speech"]
    
    # Simple pattern-based detection (in production, use ML model)
    TOXIC_PATTERNS = [
        (r"\b(hate|stupid|idiot|dumb|moron)\b", 0.3),
        (r"\b(kill\s+yourself|kys)\b", 0.9),
        (r"\b(racial\s+slur|n-word)\b", 1.0),
        (r"\b(ugly|fat|loser)\b", 0.4),
        (r"[!?]{3,}", 0.1),  # Excessive punctuation
        (r"[A-Z]{5,}", 0.15),  # SHOUTING
    ]
    
    async def analyze(self, record: ContentRecord) -> AnalysisResult:
        start_time = datetime.utcnow()
        
        score = 0.0
        reasons = []
        
        text = record.text or ""
        
        for pattern, weight in self.TOXIC_PATTERNS:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                score += weight * min(matches, 3)
                reasons.append(f"Pattern match: {pattern[:20]}...")
        
        # Consider sentiment
        if record.features.sentiment_score < -0.5:
            score += 0.2
            reasons.append("Very negative sentiment")
        
        # Check for targeted harassment (mentions + toxicity)
        if record.features.mention_count > 0 and score > 0.3:
            score += 0.2
            reasons.append("Targeted negativity")
        
        # Cap score
        score = min(score, 1.0)
        
        # Determine risk
        if score >= 0.7:
            risk = RiskLevel.CRITICAL
        elif score >= 0.5:
            risk = RiskLevel.HIGH
        elif score >= 0.3:
            risk = RiskLevel.MEDIUM
        elif score > 0:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.NONE
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AnalysisResult(
            analyzer_name=self.name,
            analyzer_version=self.version,
            risk_level=risk,
            confidence=min(score + 0.1, 1.0),
            score=score,
            category="toxicity",
            flagged=score >= 0.4,
            reasons=reasons,
            processing_time_ms=processing_time,
        )


class DuplicateAnalyzer(ContentAnalyzer):
    """Analyzer for duplicate/repetitive content."""
    
    name = "duplicate_detector"
    version = "1.0.0"
    categories = ["spam", "flooding"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.recent_hashes: Set[str] = set()
        self.hash_timestamps: Dict[str, datetime] = {}
    
    async def analyze(self, record: ContentRecord) -> AnalysisResult:
        start_time = datetime.utcnow()
        
        # Generate content hash
        content = (record.text or "").lower().strip()
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        
        # Check for duplicates
        is_duplicate = content_hash in self.recent_hashes
        
        # Update tracking
        self.recent_hashes.add(content_hash)
        self.hash_timestamps[content_hash] = datetime.utcnow()
        
        # Cleanup old hashes
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        old_hashes = [h for h, ts in self.hash_timestamps.items() if ts < cutoff]
        for h in old_hashes:
            self.recent_hashes.discard(h)
            del self.hash_timestamps[h]
        
        score = 0.7 if is_duplicate else 0.0
        reasons = ["Duplicate content detected"] if is_duplicate else []
        
        # Also check file hashes
        for file_hash in record.features.file_hashes:
            if file_hash in self.recent_hashes:
                score = 0.8
                reasons.append("Duplicate media detected")
                break
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AnalysisResult(
            analyzer_name=self.name,
            analyzer_version=self.version,
            risk_level=RiskLevel.HIGH if is_duplicate else RiskLevel.NONE,
            confidence=0.9 if is_duplicate else 0.0,
            score=score,
            category="duplicate",
            flagged=is_duplicate,
            reasons=reasons,
            processing_time_ms=processing_time,
        )


@dataclass
class PolicyRule:
    """A rule in the moderation policy."""
    name: str
    condition: str  # Expression to evaluate
    action: ActionDecision
    risk_threshold: RiskLevel = RiskLevel.MEDIUM
    confidence_threshold: float = 0.7
    weight: float = 1.0
    
    def matches(self, record: ContentRecord) -> bool:
        """Check if rule matches the content record."""
        # Simple condition evaluation
        # In production, use a proper expression engine
        try:
            # Example conditions:
            # "spam.score > 0.7"
            # "toxicity.risk_level == 'high'"
            # "features.url_count > 3"
            
            parts = self.condition.split()
            if len(parts) >= 3:
                field = parts[0]
                operator = parts[1]
                value = " ".join(parts[2:])
                
                # Get field value
                field_value = self._get_field_value(record, field)
                
                # Compare
                if operator == ">":
                    return float(field_value) > float(value)
                elif operator == ">=":
                    return float(field_value) >= float(value)
                elif operator == "<":
                    return float(field_value) < float(value)
                elif operator == "<=":
                    return float(field_value) <= float(value)
                elif operator == "==":
                    return str(field_value) == value.strip("'\"")
                elif operator == "in":
                    return value.strip("'\"") in str(field_value)
            
            return False
        except Exception:
            return False
    
    def _get_field_value(self, record: ContentRecord, field: str) -> Any:
        """Get a field value from the record."""
        # Handle nested fields like "spam.score"
        parts = field.split(".")
        
        if parts[0] == "features":
            return getattr(record.features, parts[1], 0)
        
        # Check analysis results
        for result in record.analysis_results:
            if result.analyzer_name == parts[0]:
                return getattr(result, parts[1], 0)
        
        return 0


class ContentPipeline:
    """
    Multi-stage content moderation pipeline.
    """
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
        self.analyzers: List[ContentAnalyzer] = []
        self.policy_rules: List[PolicyRule] = []
        self.pre_filters: List[Callable] = []
        self.post_handlers: List[Callable] = []
        
        # Default analyzers
        self.add_analyzer(SpamAnalyzer())
        self.add_analyzer(ToxicityAnalyzer())
        self.add_analyzer(DuplicateAnalyzer())
    
    def add_analyzer(self, analyzer: ContentAnalyzer):
        """Add an analyzer to the pipeline."""
        self.analyzers.append(analyzer)
    
    def add_policy_rule(self, rule: PolicyRule):
        """Add a policy rule."""
        self.policy_rules.append(rule)
    
    def add_pre_filter(self, filter_fn: Callable[[ContentRecord], Coroutine]):
        """Add a pre-processing filter."""
        self.pre_filters.append(filter_fn)
    
    def add_post_handler(self, handler_fn: Callable[[ContentRecord], Coroutine]):
        """Add a post-processing handler."""
        self.post_handlers.append(handler_fn)
    
    async def process_message(self, message: Message, group_id: int) -> ContentRecord:
        """
        Process a message through the pipeline.
        """
        # Create record
        record_id = f"msg_{group_id}_{message.message_id}_{datetime.utcnow().timestamp()}"
        
        content_type = self._detect_content_type(message)
        
        record = ContentRecord(
            record_id=record_id,
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=message.from_user.id if message.from_user else 0,
            group_id=group_id,
            content_type=content_type,
            text=message.text or message.caption,
            raw_message=message.model_dump() if hasattr(message, 'model_dump') else {},
        )
        
        # Extract features
        record.features = await self._extract_features(record, message)
        
        # Run pre-filters
        for filter_fn in self.pre_filters:
            try:
                should_continue = await filter_fn(record)
                if not should_continue:
                    record.status = "filtered"
                    return record
            except Exception as e:
                print(f"Pre-filter error: {e}")
        
        # Run analyzers
        start_time = datetime.utcnow()
        record.status = "processing"
        
        analysis_tasks = [analyzer.analyze(record) for analyzer in self.analyzers]
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Analyzer error: {result}")
                continue
            record.analysis_results.append(result)
        
        # Apply policy
        record.decision = self._apply_policy(record)
        
        record.processed_at = datetime.utcnow()
        record.processing_time_ms = (record.processed_at - start_time).total_seconds() * 1000
        record.status = "completed"
        
        # Store result
        await self._store_record(record)
        
        # Run post-handlers
        for handler_fn in self.post_handlers:
            try:
                await handler_fn(record)
            except Exception as e:
                print(f"Post-handler error: {e}")
        
        return record
    
    async def _extract_features(self, record: ContentRecord, message: Message) -> ContentFeatures:
        """Extract features from a message."""
        features = ContentFeatures()
        
        text = record.text or ""
        
        # Text features
        features.text_length = len(text)
        features.word_count = len(text.split())
        features.emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
        
        if text:
            caps_count = sum(1 for c in text if c.isupper())
            features.caps_ratio = caps_count / len(text)
            
            digit_count = sum(1 for c in text if c.isdigit())
            features.digit_ratio = digit_count / len(text)
            
            special_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
            features.special_char_ratio = special_count / len(text)
        
        # Extract URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        features.urls = re.findall(url_pattern, text)
        features.url_count = len(features.urls)
        
        # Extract entities
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    features.mention_count += 1
                elif entity.type == "hashtag":
                    features.hashtag_count += 1
                elif entity.type == "bot_command":
                    features.command_count += 1
        
        # Check forwarding
        if message.forward_date:
            features.forwarded = True
            if message.forward_from_chat:
                features.forward_from_chat = message.forward_from_chat.id
        
        # File types
        if message.content_type != "text":
            features.file_types.append(message.content_type)
        
        return features
    
    def _apply_policy(self, record: ContentRecord) -> PipelineDecision:
        """Apply policy rules to determine action."""
        # Aggregate risk
        max_risk = RiskLevel.NONE
        max_confidence = 0.0
        primary_reason = ""
        all_reasons = []
        
        for result in record.analysis_results:
            if result.flagged:
                risk_order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
                if risk_order.index(result.risk_level) > risk_order.index(max_risk):
                    max_risk = result.risk_level
                    max_confidence = result.confidence
                    primary_reason = f"{result.analyzer_name}: {', '.join(result.reasons[:2])}"
                
                all_reasons.extend([f"{result.analyzer_name}: {r}" for r in result.reasons])
        
        # Check policy rules
        for rule in self.policy_rules:
            if rule.matches(record):
                return PipelineDecision(
                    decision=rule.action,
                    risk_level=max_risk,
                    confidence=max_confidence,
                    primary_reason=f"Policy rule: {rule.name}",
                    all_reasons=all_reasons,
                    requires_review=max_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL),
                    review_priority=8 if max_risk == RiskLevel.CRITICAL else 5,
                )
        
        # Default decision based on risk
        decision_map = {
            RiskLevel.NONE: ActionDecision.ALLOW,
            RiskLevel.LOW: ActionDecision.FLAG,
            RiskLevel.MEDIUM: ActionDecision.RESTRICT,
            RiskLevel.HIGH: ActionDecision.DELETE,
            RiskLevel.CRITICAL: ActionDecision.BAN,
        }
        
        return PipelineDecision(
            decision=decision_map.get(max_risk, ActionDecision.ALLOW),
            risk_level=max_risk,
            confidence=max_confidence,
            primary_reason=primary_reason or "No issues detected",
            all_reasons=all_reasons,
            requires_review=max_risk in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL),
            review_priority=5 if max_risk == RiskLevel.HIGH else 3,
        )
    
    def _detect_content_type(self, message: Message) -> ContentType_:
        """Detect content type from message."""
        type_map = {
            "text": ContentType_.TEXT,
            "photo": ContentType_.PHOTO,
            "video": ContentType_.VIDEO,
            "audio": ContentType_.AUDIO,
            "document": ContentType_.DOCUMENT,
            "animation": ContentType_.ANIMATION,
            "sticker": ContentType_.STICKER,
            "location": ContentType_.LOCATION,
            "contact": ContentType_.CONTACT,
        }
        return type_map.get(message.content_type, ContentType_.TEXT)
    
    async def _store_record(self, record: ContentRecord):
        """Store record in Redis."""
        key = f"content:record:{record.record_id}"
        await self.redis.set_json(key, record.to_dict(), expire=86400 * 7)
    
    async def get_record(self, record_id: str) -> Optional[ContentRecord]:
        """Get a stored record."""
        key = f"content:record:{record_id}"
        data = await self.redis.get_json(key)
        if not data:
            return None
        
        # Reconstruct record
        return ContentRecord(
            record_id=data["record_id"],
            message_id=data["message_id"],
            chat_id=data["chat_id"],
            user_id=data["user_id"],
            group_id=data["group_id"],
            content_type=ContentType_(data["content_type"]),
            text=data.get("text"),
            status=data.get("status", "completed"),
            decision=PipelineDecision(**data["decision"]) if data.get("decision") else None,
        )
    
    async def appeal_decision(
        self,
        record_id: str,
        user_id: int,
        reason: str,
    ) -> bool:
        """Submit an appeal for a moderation decision."""
        record = await self.get_record(record_id)
        if not record:
            return False
        
        if record.user_id != user_id:
            return False
        
        if not record.decision or not record.decision.appealable:
            return False
        
        record.appeal_status = "pending"
        await self._store_record(record)
        
        # Store appeal
        appeal_key = f"content:appeal:{record_id}"
        await self.redis.set_json(appeal_key, {
            "record_id": record_id,
            "user_id": user_id,
            "reason": reason,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }, expire=86400 * 30)
        
        return True
