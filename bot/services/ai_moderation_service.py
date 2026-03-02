"""AI Moderation Queue Service for Nexus.

Provides AI-powered content moderation that:
- Watches messages in real-time
- Flags suspicious content with confidence scores
- Presents flagged content to admins in a review queue
- Supports auto-action for high-confidence violations
- Tracks false positives for continuous improvement
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    AIModerationConfig,
    AIModerationQueue,
    Member,
)


@dataclass
class ModerationPrediction:
    """AI moderation prediction result."""
    flagged: bool
    categories: List[str]  # spam, toxicity, harassment, etc.
    confidence: float  # 0-100
    severity: str  # low, medium, high, critical
    reasoning: str
    suggested_action: str  # delete, mute, ban, warn, review


@dataclass
class QueueItem:
    """Item in the moderation queue."""
    id: int
    user_id: int
    message_content: Optional[str]
    media_type: Optional[str]
    categories: List[str]
    confidence: float
    severity: str
    ai_reasoning: str
    suggested_action: str
    created_at: datetime
    status: str


class AIModerationService:
    """AI-powered content moderation service."""

    # Severity thresholds
    SEVERITY_THRESHOLDS = {
        "critical": 90,
        "high": 75,
        "medium": 60,
        "low": 40,
    }

    # Category definitions
    CATEGORIES = {
        "spam": "Unwanted repetitive or promotional content",
        "toxicity": "Rude, disrespectful, or unreasonable behavior",
        "harassment": "Targeting individuals with unwanted behavior",
        "hate_speech": "Attacking protected characteristics",
        "misinformation": "Factually incorrect harmful content",
        "scam": "Fraudulent or deceptive practices",
        "nsfw": "Sexually explicit content",
        "violence": "Threats or glorification of violence",
        "self_harm": "Content promoting self-harm",
        "doxxing": "Sharing private information without consent",
    }

    def __init__(self, db: AsyncSession, openai_api_key: Optional[str] = None):
        self.db = db
        self.openai_api_key = openai_api_key

    async def analyze_message(
        self,
        group_id: int,
        user_id: int,
        message_id: int,
        content: Optional[str],
        media_type: Optional[str] = None,
        media_file_id: Optional[str] = None,
        is_forwarded: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> Optional[ModerationPrediction]:
        """Analyze a message for policy violations.

        Returns prediction if content should be flagged, None if clean.
        """
        config = await self._get_config(group_id)

        if not config.enabled:
            return None

        # Check if user should bypass
        should_bypass = await self._should_bypass(group_id, user_id, config)
        if should_bypass:
            return None

        # Skip if message doesn't match scan criteria
        if not self._should_scan_message(
            content, media_type, is_forwarded, config
        ):
            return None

        # Run AI analysis
        prediction = await self._run_ai_analysis(
            content, media_type, config.categories
        )

        # Check against thresholds
        if prediction.confidence >= config.queue_threshold:
            # Add to queue
            await self._add_to_queue(
                group_id=group_id,
                user_id=user_id,
                message_id=message_id,
                message_content=content,
                media_type=media_type,
                media_file_id=media_file_id,
                prediction=prediction,
            )

            # Check for auto-action
            if (
                prediction.confidence >= config.auto_action_threshold
                and prediction.severity in ["critical", "high"]
            ):
                await self._execute_auto_action(
                    group_id, user_id, prediction, config
                )
                prediction.suggested_action = "auto_executed"

        return prediction

    async def get_queue(
        self,
        group_id: int,
        status: str = "pending",
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QueueItem]:
        """Get moderation queue for admin review."""
        query = select(AIModerationQueue).where(
            AIModerationQueue.group_id == group_id,
            AIModerationQueue.status == status,
        )

        if severity:
            query = query.where(AIModerationQueue.severity == severity)

        query = (
            query.order_by(AIModerationQueue.confidence_score.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        items = result.scalars().all()

        return [
            QueueItem(
                id=item.id,
                user_id=item.user_id,
                message_content=item.message_content,
                media_type=item.media_type,
                categories=item.flagged_categories,
                confidence=item.confidence_score,
                severity=item.severity,
                ai_reasoning=item.ai_reasoning,
                suggested_action=item.suggested_action,
                created_at=item.created_at,
                status=item.status,
            )
            for item in items
        ]

    async def review_item(
        self,
        item_id: int,
        admin_user_id: int,
        action: str,  # approve, dismiss, delete, mute, ban, warn
        reason: Optional[str] = None,
    ) -> bool:
        """Review a queued item and take action."""
        result = await self.db.execute(
            select(AIModerationQueue).where(AIModerationQueue.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item or item.status != "pending":
            return False

        # Update item
        item.status = action
        item.reviewed_by = admin_user_id
        item.reviewed_at = datetime.utcnow()
        item.action_taken = action

        # Track false positives
        if action == "dismiss":
            item.false_positive = True

        await self.db.flush()

        # Execute the action if it's a moderation action
        if action in ["delete", "mute", "ban", "warn"]:
            await self._execute_moderation_action(
                item.group_id, item.user_id, action, reason
            )

        return True

    async def get_stats(self, group_id: int, days: int = 30) -> Dict[str, Any]:
        """Get moderation statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total flagged
        result = await self.db.execute(
            select(AIModerationQueue).where(
                AIModerationQueue.group_id == group_id,
                AIModerationQueue.created_at >= start_date,
            )
        )
        all_items = result.scalars().all()

        # By status
        by_status = {}
        by_severity = {}
        by_category = {}
        false_positives = 0

        for item in all_items:
            # Status
            by_status[item.status] = by_status.get(item.status, 0) + 1

            # Severity
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

            # Categories
            for cat in item.flagged_categories:
                by_category[cat] = by_category.get(cat, 0) + 1

            # False positives
            if item.false_positive:
                false_positives += 1

        total = len(all_items)

        return {
            "total_flagged": total,
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category,
            "false_positives": false_positives,
            "accuracy": (
                (total - false_positives) / total * 100 if total > 0 else 100
            ),
            "pending_review": by_status.get("pending", 0),
            "auto_actions": by_status.get("auto_executed", 0),
            "avg_confidence": (
                sum(i.confidence_score for i in all_items) / total
                if total > 0
                else 0
            ),
        }

    async def batch_review(
        self,
        group_id: int,
        item_ids: List[int],
        action: str,
        admin_user_id: int,
    ) -> int:
        """Batch review multiple items."""
        processed = 0
        for item_id in item_ids:
            success = await self.review_item(item_id, admin_user_id, action)
            if success:
                processed += 1
        return processed

    async def _get_config(self, group_id: int) -> AIModerationConfig:
        """Get or create AI moderation config."""
        result = await self.db.execute(
            select(AIModerationConfig).where(
                AIModerationConfig.group_id == group_id
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            config = AIModerationConfig(
                group_id=group_id,
                enabled=False,  # Disabled by default
                auto_action_threshold=90,
                queue_threshold=70,
                scan_media=True,
                scan_links=True,
                scan_forwarded=True,
                categories=list(self.CATEGORIES.keys()),
                trusted_bypass=True,
                min_trust_bypass=80,
                notify_admins=True,
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def _should_bypass(
        self, group_id: int, user_id: int, config: AIModerationConfig
    ) -> bool:
        """Check if user should bypass AI moderation."""
        if not config.trusted_bypass:
            return False

        # Check trust score
        result = await self.db.execute(
            select(Member.trust_score).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        trust_score = result.scalar() or 0

        return trust_score >= config.min_trust_bypass

    def _should_scan_message(
        self,
        content: Optional[str],
        media_type: Optional[str],
        is_forwarded: bool,
        config: AIModerationConfig,
    ) -> bool:
        """Determine if message should be scanned."""
        # Skip empty messages
        if not content and not media_type:
            return False

        # Check forwarded
        if is_forwarded and not config.scan_forwarded:
            return False

        # Check media
        if media_type and not config.scan_media:
            return False

        # Check links
        if content and "http" in content and not config.scan_links:
            return False

        return True

    async def _run_ai_analysis(
        self,
        content: Optional[str],
        media_type: Optional[str],
        categories: List[str],
    ) -> ModerationPrediction:
        """Run AI analysis on content.

        Uses OpenAI API for content moderation.
        """
        if not self.openai_api_key or not content:
            # Fallback: simple keyword matching
            return self._keyword_analysis(content or "", categories)

        # Call OpenAI moderation API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/moderations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": content},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get("results", [{}])[0]

                        flagged = result.get("flagged", False)
                        category_scores = result.get("category_scores", {})

                        # Map to our categories
                        mapped_categories = []
                        confidence = 0

                        category_mapping = {
                            "sexual": "nsfw",
                            "hate": "hate_speech",
                            "harassment": "harassment",
                            "self-harm": "self_harm",
                            "sexual/minors": "nsfw",
                            "hate/threatening": "hate_speech",
                            "violence/graphic": "violence",
                            "self-harm/intent": "self_harm",
                            "self-harm/instructions": "self_harm",
                            "harassment/threatening": "harassment",
                            "violence": "violence",
                        }

                        for api_cat, score in category_scores.items():
                            if score > 0.3:  # Threshold for detection
                                our_cat = category_mapping.get(api_cat, api_cat)
                                if our_cat in categories:
                                    mapped_categories.append(our_cat)
                                    confidence = max(confidence, score * 100)

                        # Determine severity
                        severity = self._confidence_to_severity(confidence)

                        # Suggest action
                        suggested = self._suggest_action(
                            severity, mapped_categories
                        )

                        return ModerationPrediction(
                            flagged=flagged or confidence > 50,
                            categories=mapped_categories,
                            confidence=confidence,
                            severity=severity,
                            reasoning=f"OpenAI moderation detected: {', '.join(mapped_categories)}",
                            suggested_action=suggested,
                        )
        except Exception as e:
            # Fallback on error
            print(f"AI moderation error: {e}")

        return self._keyword_analysis(content or "", categories)

    def _keyword_analysis(
        self, content: str, categories: List[str]
    ) -> ModerationPrediction:
        """Fallback keyword-based analysis."""
        content_lower = content.lower()

        # Simple keyword patterns
        patterns = {
            "spam": ["buy now", "click here", "limited time", "act now", "$$$"],
            "toxicity": ["stupid", "idiot", "loser", "shut up"],
            "harassment": ["kill yourself", "kys", "harass"],
            "scam": ["send money", "wire transfer", "bitcoin", "crypto opportunity"],
        }

        detected = []
        max_confidence = 0

        for category, keywords in patterns.items():
            if category not in categories:
                continue

            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches > 0:
                detected.append(category)
                confidence = min(80, matches * 20)
                max_confidence = max(max_confidence, confidence)

        severity = self._confidence_to_severity(max_confidence)
        suggested = self._suggest_action(severity, detected)

        return ModerationPrediction(
            flagged=len(detected) > 0,
            categories=detected,
            confidence=max_confidence,
            severity=severity,
            reasoning=f"Keyword analysis detected: {', '.join(detected)}" if detected else "No violations detected",
            suggested_action=suggested,
        )

    def _confidence_to_severity(self, confidence: float) -> str:
        """Convert confidence score to severity level."""
        if confidence >= self.SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif confidence >= self.SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif confidence >= self.SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        elif confidence >= self.SEVERITY_THRESHOLDS["low"]:
            return "low"
        return "none"

    def _suggest_action(self, severity: str, categories: List[str]) -> str:
        """Suggest moderation action based on severity and categories."""
        if severity == "critical":
            return "ban"
        elif severity == "high":
            if "spam" in categories or "scam" in categories:
                return "delete"
            return "mute"
        elif severity == "medium":
            return "warn"
        return "review"

    async def _add_to_queue(
        self,
        group_id: int,
        user_id: int,
        message_id: int,
        message_content: Optional[str],
        media_type: Optional[str],
        media_file_id: Optional[str],
        prediction: ModerationPrediction,
    ):
        """Add flagged content to moderation queue."""
        queue_item = AIModerationQueue(
            group_id=group_id,
            user_id=user_id,
            message_id=message_id,
            message_content=message_content[:1000] if message_content else None,
            media_type=media_type,
            media_file_id=media_file_id,
            flagged_categories=prediction.categories,
            confidence_score=prediction.confidence,
            severity=prediction.severity,
            ai_reasoning=prediction.reasoning,
            suggested_action=prediction.suggested_action,
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.add(queue_item)
        await self.db.flush()

    async def _execute_auto_action(
        self,
        group_id: int,
        user_id: int,
        prediction: ModerationPrediction,
        config: AIModerationConfig,
    ):
        """Execute automatic moderation action."""
        # This would integrate with the moderation module
        # For now, just log it
        print(
            f"Auto-action: {prediction.suggested_action} for user {user_id} "
            f"in group {group_id} (confidence: {prediction.confidence})"
        )

        # TODO: Actually execute moderation action

    async def _execute_moderation_action(
        self,
        group_id: int,
        user_id: int,
        action: str,
        reason: Optional[str],
    ):
        """Execute moderation action from queue review."""
        # This would integrate with the moderation module
        print(
            f"Queue action: {action} for user {user_id} in group {group_id}"
        )

        # TODO: Actually execute moderation action
