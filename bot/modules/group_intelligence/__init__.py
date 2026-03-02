"""Group Intelligence Module - Predictive Moderation, Conversation Graph, Anomaly Detection."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule
from shared.database import get_db
from shared.models_intelligence import (
    AnomalyEvent,
    BehaviorPattern,
    ChurnPrediction,
    ConversationEdge,
    ConversationNode,
    MemberBehaviorLog,
    MemberJourney,
    PredictiveScore,
    TopicCluster,
)


class GroupIntelligenceModule(NexusModule):
    """Group Intelligence Module for advanced community analytics."""

    name = "group_intelligence"
    version = "1.0.0"
    description = "Predictive moderation, conversation graphs, anomaly detection, and member intelligence"
    category = ModuleCategory.AI

    commands = [
        CommandDef(
            name="risk",
            description="Check member risk score",
            admin_only=True,
            args="[@user|user_id]",
            category="intelligence",
        ),
        CommandDef(
            name="predict",
            description="View predictions for member behavior",
            admin_only=True,
            args="[@user|user_id]",
            category="intelligence",
        ),
        CommandDef(
            name="anomalies",
            description="View recent anomalies in the group",
            admin_only=True,
            args="[hours]",
            category="intelligence",
        ),
        CommandDef(
            name="influencers",
            description="View most influential members",
            admin_only=False,
            category="intelligence",
        ),
        CommandDef(
            name="churn_risk",
            description="View members at risk of leaving",
            admin_only=True,
            category="intelligence",
        ),
        CommandDef(
            name="journey",
            description="View member journey analysis",
            admin_only=True,
            args="[@user|user_id]",
            category="intelligence",
        ),
        CommandDef(
            name="topics",
            description="View trending topics",
            admin_only=False,
            category="intelligence",
        ),
        CommandDef(
            name="graph",
            description="Generate conversation graph link",
            admin_only=True,
            category="intelligence",
        ),
    ]

    listeners = [
        EventType.MESSAGE,
        EventType.NEW_MEMBER,
        EventType.LEFT_MEMBER,
        EventType.REACTION,
    ]

    def __init__(self):
        super().__init__()
        self._behavior_buffer: Dict[int, List[Dict]] = {}  # user_id -> behaviors
        self._message_buffer: Dict[int, List[Dict]] = {}  # group_id -> messages

    async def on_message(self, ctx: NexusContext) -> bool:
        """Process message for intelligence gathering."""
        if not ctx.group_id or not ctx.user_id:
            return False

        # Log behavior
        await self._log_behavior(
            user_id=ctx.user_id,
            group_id=ctx.group_id,
            behavior_type="message",
            behavior_data={
                "message_type": ctx.message.content_type if ctx.message else "text",
                "has_media": ctx.message and hasattr(ctx.message, "photo") and ctx.message.photo is not None,
                "has_link": bool(ctx.text and ("http://" in ctx.text or "https://" in ctx.text)),
                "length": len(ctx.text) if ctx.text else 0,
            },
            message_id=ctx.message.message_id if ctx.message else None,
        )

        # Check for pattern matches
        await self._check_patterns(ctx)

        # Update conversation graph
        await self._update_conversation_graph(ctx)

        # Check for anomalies
        await self._check_anomalies(ctx)

        return False  # Don't consume the message

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Track new member for journey analysis."""
        if not ctx.group_id or not ctx.user_id:
            return False

        # Create journey record
        async with get_db() as db:
            # Check if journey exists
            existing = await db.execute(
                select(MemberJourney).where(
                    MemberJourney.user_id == ctx.user_id,
                    MemberJourney.group_id == ctx.group_id,
                )
            )
            journey = existing.scalar_one_or_none()

            if not journey:
                journey = MemberJourney(
                    user_id=ctx.user_id,
                    group_id=ctx.group_id,
                    joined_at=datetime.utcnow(),
                    welcomed_by_bot=True,
                )
                db.add(journey)
                await db.commit()

        # Log behavior
        await self._log_behavior(
            user_id=ctx.user_id,
            group_id=ctx.group_id,
            behavior_type="join",
            behavior_data={"source": "new_member_event"},
        )

        # Estimate account age from user_id
        await self._estimate_account_age(ctx)

        return False

    async def on_left_member(self, ctx: NexusContext) -> bool:
        """Track member departure for churn analysis."""
        if not ctx.group_id or not ctx.user_id:
            return False

        # Update journey record
        async with get_db() as db:
            journey = await db.execute(
                select(MemberJourney).where(
                    MemberJourney.user_id == ctx.user_id,
                    MemberJourney.group_id == ctx.group_id,
                )
            )
            journey_record = journey.scalar_one_or_none()

            if journey_record:
                journey_record.churned_at = datetime.utcnow()
                await db.commit()

        return False

    async def on_reaction(self, ctx: NexusContext) -> bool:
        """Track reactions for engagement metrics."""
        if not ctx.group_id or not ctx.user_id:
            return False

        await self._log_behavior(
            user_id=ctx.user_id,
            group_id=ctx.group_id,
            behavior_type="reaction",
            behavior_data={
                "emoji": ctx.event.reaction.emoji if hasattr(ctx.event, "reaction") else None,
            },
        )

        return False

    async def _log_behavior(
        self,
        user_id: int,
        group_id: int,
        behavior_type: str,
        behavior_data: Optional[Dict] = None,
        message_id: Optional[int] = None,
    ):
        """Log a member behavior."""
        async with get_db() as db:
            log = MemberBehaviorLog(
                user_id=user_id,
                group_id=group_id,
                behavior_type=behavior_type,
                behavior_data=behavior_data or {},
                message_id=message_id,
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            await db.commit()

    async def _check_patterns(self, ctx: NexusContext):
        """Check if current behavior matches known patterns."""
        async with get_db() as db:
            # Get active patterns
            patterns = await db.execute(
                select(BehaviorPattern).where(BehaviorPattern.is_active == True)
            )
            active_patterns = patterns.scalars().all()

            # Get recent behaviors for this user
            recent = await db.execute(
                select(MemberBehaviorLog)
                .where(
                    MemberBehaviorLog.user_id == ctx.user_id,
                    MemberBehaviorLog.group_id == ctx.group_id,
                    MemberBehaviorLog.timestamp >= datetime.utcnow() - timedelta(hours=1),
                )
                .order_by(desc(MemberBehaviorLog.timestamp))
                .limit(20)
            )
            recent_behaviors = recent.scalars().all()

            # Check each pattern
            matched_patterns = []
            for pattern in active_patterns:
                if await self._match_pattern(pattern, recent_behaviors, ctx):
                    matched_patterns.append(pattern.pattern_id)

                    # Update predictive score
                    await self._update_predictive_score(
                        db, ctx.user_id, ctx.group_id, pattern, matched_patterns
                    )

            if matched_patterns:
                # Update the log with matched patterns
                await db.execute(
                    MemberBehaviorLog.__table__.update()
                    .where(MemberBehaviorLog.user_id == ctx.user_id)
                    .values(matched_patterns=matched_patterns)
                )
                await db.commit()

    async def _match_pattern(
        self, pattern: BehaviorPattern, behaviors: List[MemberBehaviorLog], ctx: NexusContext
    ) -> bool:
        """Check if behaviors match a pattern."""
        if not behaviors:
            return False

        pattern_sequence = pattern.sequence
        if not pattern_sequence:
            return False

        # Simple pattern matching based on behavior types
        behavior_types = [b.behavior_type for b in behaviors[:len(pattern_sequence)]]
        
        matches = 0
        for i, expected in enumerate(pattern_sequence[:len(behavior_types)]):
            if behavior_types[i] == expected.get("type"):
                matches += 1

        return matches >= pattern.min_occurrences

    async def _update_predictive_score(
        self,
        db: AsyncSession,
        user_id: int,
        group_id: int,
        pattern: BehaviorPattern,
        matched_patterns: List[str],
    ):
        """Update predictive risk score for a member."""
        # Get or create score
        result = await db.execute(
            select(PredictiveScore).where(
                PredictiveScore.user_id == user_id,
                PredictiveScore.group_id == group_id,
            )
        )
        score = result.scalar_one_or_none()

        if not score:
            score = PredictiveScore(
                user_id=user_id,
                group_id=group_id,
                risk_score=0,
                matched_patterns=[],
                behavioral_flags=[],
            )
            db.add(score)

        # Update score based on pattern
        score.risk_score = min(100, score.risk_score + pattern.base_risk_score)
        score.matched_patterns = list(set(score.matched_patterns + matched_patterns))

        # Update likelihoods based on pattern category
        if pattern.category == "spam":
            score.spam_likelihood = min(1.0, score.spam_likelihood + 0.1)
        elif pattern.category == "raid":
            score.raid_likelihood = min(1.0, score.raid_likelihood + 0.1)
        elif pattern.category == "abuse":
            score.abuse_likelihood = min(1.0, score.abuse_likelihood + 0.1)

        # Set first flagged if new
        if not score.first_flagged:
            score.first_flagged = datetime.utcnow()

        # Update monitoring level based on risk
        if score.risk_score >= 70:
            score.monitoring_level = 2
        elif score.risk_score >= 40:
            score.monitoring_level = 1
        else:
            score.monitoring_level = 0

        await db.commit()

    async def _estimate_account_age(self, ctx: NexusContext):
        """Estimate account age from Telegram user ID."""
        # Telegram user IDs are sequential, so we can estimate age
        # Lower IDs = older accounts
        user_id = ctx.user_id
        
        # Very rough estimation based on ID ranges
        if user_id < 100_000_000:
            estimated_days = 365 * 5  # 5+ years
        elif user_id < 1_000_000_000:
            estimated_days = 365 * 3  # 3+ years
        elif user_id < 5_000_000_000:
            estimated_days = 365  # 1+ year
        else:
            estimated_days = 30  # New account

        # Update predictive score
        async with get_db() as db:
            result = await db.execute(
                select(PredictiveScore).where(
                    PredictiveScore.user_id == ctx.user_id,
                    PredictiveScore.group_id == ctx.group_id,
                )
            )
            score = result.scalar_one_or_none()

            if not score:
                score = PredictiveScore(
                    user_id=ctx.user_id,
                    group_id=ctx.group_id,
                    risk_score=0 if estimated_days > 365 else 20,
                    matched_patterns=[],
                    behavioral_flags=[],
                )
                db.add(score)

            # New accounts start with higher risk
            if estimated_days < 7:
                score.behavioral_flags = list(set(score.behavioral_flags + ["new_account"]))
                score.risk_score = max(score.risk_score, 30)

            await db.commit()

    async def _update_conversation_graph(self, ctx: NexusContext):
        """Update the conversation graph with message data."""
        if not ctx.message:
            return

        # Check if this is a reply
        reply_to = ctx.message.reply_to_message
        if reply_to and reply_to.from_user:
            target_user_id = reply_to.from_user.id
            source_user_id = ctx.user_id

            if source_user_id != target_user_id:
                await self._create_or_update_edge(
                    ctx.group_id, source_user_id, target_user_id, "reply"
                )

        # Check for mentions
        entities = ctx.message.entities or []
        for entity in entities:
            if entity.type == "mention" or entity.type == "text_mention":
                if hasattr(entity, "user") and entity.user:
                    target_user_id = entity.user.id
                    if target_user_id != ctx.user_id:
                        await self._create_or_update_edge(
                            ctx.group_id, ctx.user_id, target_user_id, "mention"
                        )

        # Update node metrics
        await self._update_node(ctx.group_id, ctx.user_id)

    async def _create_or_update_edge(
        self, group_id: int, source_id: int, target_id: int, interaction_type: str
    ):
        """Create or update a conversation edge."""
        async with get_db() as db:
            result = await db.execute(
                select(ConversationEdge).where(
                    ConversationEdge.group_id == group_id,
                    ConversationEdge.source_user_id == source_id,
                    ConversationEdge.target_user_id == target_id,
                )
            )
            edge = result.scalar_one_or_none()

            if not edge:
                edge = ConversationEdge(
                    group_id=group_id,
                    source_user_id=source_id,
                    target_user_id=target_id,
                    reply_count=0,
                    mention_count=0,
                    reaction_count=0,
                    forward_count=0,
                    strength=0.0,
                    reciprocity=0.0,
                    avg_sentiment=0.0,
                )
                db.add(edge)

            # Increment appropriate counter
            if interaction_type == "reply":
                edge.reply_count += 1
            elif interaction_type == "mention":
                edge.mention_count += 1
            elif interaction_type == "reaction":
                edge.reaction_count += 1

            # Update strength
            edge.strength = (edge.reply_count + edge.mention_count * 0.5 + edge.reaction_count * 0.3) / 10
            edge.last_interaction = datetime.utcnow()

            await db.commit()

    async def _update_node(self, group_id: int, user_id: int):
        """Update conversation node metrics."""
        async with get_db() as db:
            result = await db.execute(
                select(ConversationNode).where(
                    ConversationNode.group_id == group_id,
                    ConversationNode.user_id == user_id,
                )
            )
            node = result.scalar_one_or_none()

            if not node:
                node = ConversationNode(
                    group_id=group_id,
                    user_id=user_id,
                    influence_score=0.0,
                    centrality_score=0.0,
                    trust_score_normalized=0.5,
                    total_interactions=0,
                    messages_sent=0,
                    replies_received=0,
                    reactions_received=0,
                    clique_membership=[],
                    bridges_to=[],
                    is_isolated=False,
                )
                db.add(node)

            node.messages_sent += 1
            node.total_interactions += 1
            node.last_updated = datetime.utcnow()

            await db.commit()

    async def _check_anomalies(self, ctx: NexusContext):
        """Check for anomalies in group activity."""
        group_id = ctx.group_id

        # Buffer recent messages
        if group_id not in self._message_buffer:
            self._message_buffer[group_id] = []

        self._message_buffer[group_id].append({
            "timestamp": datetime.utcnow(),
            "user_id": ctx.user_id,
        })

        # Keep only last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._message_buffer[group_id] = [
            m for m in self._message_buffer[group_id] if m["timestamp"] > cutoff
        ]

        # Check for message volume anomaly
        recent_count = len(self._message_buffer[group_id])
        baseline = 100  # This should be calculated from historical data

        if recent_count > baseline * 4:  # 400% above normal
            await self._create_anomaly(
                ctx,
                anomaly_type="high_volume",
                title="Unusual Message Volume",
                description=f"Message volume is {recent_count} in the last hour, which is {int((recent_count / baseline - 1) * 100)}% above normal",
                severity=3,
                deviation_score=(recent_count / baseline) - 1,
                baseline_value=baseline,
                actual_value=recent_count,
            )

        # Check for rapid join anomaly
        # This would be done separately in a scheduled task

    async def _create_anomaly(
        self,
        ctx: NexusContext,
        anomaly_type: str,
        title: str,
        description: str,
        severity: int,
        deviation_score: float,
        baseline_value: float,
        actual_value: float,
    ):
        """Create an anomaly event."""
        async with get_db() as db:
            anomaly_id = f"anom_{uuid.uuid4().hex[:12]}"

            anomaly = AnomalyEvent(
                anomaly_id=anomaly_id,
                group_id=ctx.group_id,
                anomaly_type=anomaly_type,
                title=title,
                description=description,
                severity=severity,
                deviation_score=deviation_score,
                baseline_value=baseline_value,
                actual_value=actual_value,
                detected_at=datetime.utcnow(),
            )
            db.add(anomaly)
            await db.commit()

    # Command handlers
    async def handle_command(self, name: str, ctx: NexusContext) -> bool:
        """Handle commands."""
        handlers = {
            "risk": self._cmd_risk,
            "predict": self._cmd_predict,
            "anomalies": self._cmd_anomalies,
            "influencers": self._cmd_influencers,
            "churn_risk": self._cmd_churn_risk,
            "journey": self._cmd_journey,
            "topics": self._cmd_topics,
            "graph": self._cmd_graph,
        }

        handler = handlers.get(name)
        if handler:
            await handler(ctx)
            return True
        return False

    async def _cmd_risk(self, ctx: NexusContext):
        """Check member risk score."""
        # Parse target user
        target_id = await self._parse_user(ctx)
        if not target_id:
            await ctx.reply("Usage: !risk [@user|user_id]")
            return

        async with get_db() as db:
            result = await db.execute(
                select(PredictiveScore).where(
                    PredictiveScore.user_id == target_id,
                    PredictiveScore.group_id == ctx.group_id,
                )
            )
            score = result.scalar_one_or_none()

            if not score:
                await ctx.reply("No risk data available for this member.")
                return

            # Build response
            risk_emoji = "🟢" if score.risk_score < 30 else "🟡" if score.risk_score < 70 else "🔴"
            response = f"""{risk_emoji} **Risk Assessment**

**Risk Score:** {score.risk_score}/100
**Monitoring Level:** {["Normal", "Enhanced", "Intensive"][score.monitoring_level]}

**Likelihoods:**
• Spam: {score.spam_likelihood * 100:.1f}%
• Raid: {score.raid_likelihood * 100:.1f}%
• Abuse: {score.abuse_likelihood * 100:.1f}%

**Flags:** {", ".join(score.behavioral_flags) or "None"}
**Patterns Matched:** {len(score.matched_patterns)}
**First Flagged:** {score.first_flagged.strftime("%Y-%m-%d %H:%M") if score.first_flagged else "N/A"}
"""
            await ctx.reply(response)

    async def _cmd_predict(self, ctx: NexusContext):
        """View predictions for member behavior."""
        target_id = await self._parse_user(ctx)
        if not target_id:
            await ctx.reply("Usage: !predict [@user|user_id]")
            return

        async with get_db() as db:
            result = await db.execute(
                select(PredictiveScore).where(
                    PredictiveScore.user_id == target_id,
                    PredictiveScore.group_id == ctx.group_id,
                )
            )
            score = result.scalar_one_or_none()

            if not score or not score.predicted_action:
                await ctx.reply("No predictions available for this member.")
                return

            response = f"""🔮 **Behavioral Prediction**

**Predicted Action:** {score.predicted_action.replace("_", " ").title()}
**Confidence:** {score.prediction_confidence * 100:.1f}%

Based on behavioral patterns and risk indicators.
"""
            await ctx.reply(response)

    async def _cmd_anomalies(self, ctx: NexusContext):
        """View recent anomalies."""
        # Parse hours
        args = ctx.args or []
        hours = int(args[0]) if args else 24

        async with get_db() as db:
            result = await db.execute(
                select(AnomalyEvent)
                .where(
                    AnomalyEvent.group_id == ctx.group_id,
                    AnomalyEvent.detected_at >= datetime.utcnow() - timedelta(hours=hours),
                )
                .order_by(desc(AnomalyEvent.detected_at))
                .limit(10)
            )
            anomalies = result.scalars().all()

            if not anomalies:
                await ctx.reply(f"No anomalies detected in the last {hours} hours.")
                return

            response = f"📊 **Anomalies (Last {hours}h)**\n\n"
            for a in anomalies:
                severity_emoji = "⚠️" if a.severity < 3 else "🔴"
                status = "✅ Resolved" if a.resolved_at else "🔍 Active"
                response += f"{severity_emoji} **{a.title}**\n"
                response += f"   {a.description}\n"
                response += f"   {status} • {a.detected_at.strftime('%Y-%m-%d %H:%M')}\n\n"

            await ctx.reply(response)

    async def _cmd_influencers(self, ctx: NexusContext):
        """View most influential members."""
        async with get_db() as db:
            result = await db.execute(
                select(ConversationNode)
                .where(ConversationNode.group_id == ctx.group_id)
                .order_by(desc(ConversationNode.influence_score))
                .limit(10)
            )
            nodes = result.scalars().all()

            if not nodes:
                await ctx.reply("No influence data available yet. Keep chatting!")
                return

            response = "🌟 **Top Influencers**\n\n"
            for i, node in enumerate(nodes, 1):
                # Get user info
                user_result = await db.execute(
                    select("users").where("users.id" == node.user_id)
                )
                # For now, just show ID
                response += f"{i}. User #{node.user_id}\n"
                response += f"   Influence: {node.influence_score:.2f}\n"
                response += f"   Messages: {node.messages_sent}\n\n"

            await ctx.reply(response)

    async def _cmd_churn_risk(self, ctx: NexusContext):
        """View members at risk of leaving."""
        async with get_db() as db:
            result = await db.execute(
                select(ChurnPrediction)
                .where(ChurnPrediction.group_id == ctx.group_id)
                .order_by(desc(ChurnPrediction.churn_risk))
                .limit(10)
            )
            predictions = result.scalars().all()

            if not predictions:
                await ctx.reply("No churn predictions available yet.")
                return

            response = "📉 **Members at Churn Risk**\n\n"
            for p in predictions:
                risk_emoji = "🔴" if p.churn_risk > 0.7 else "🟡" if p.churn_risk > 0.4 else "🟢"
                response += f"{risk_emoji} User #{p.user_id}\n"
                response += f"   Risk: {p.churn_risk * 100:.1f}%\n"
                response += f"   Inactive: {p.days_inactive} days\n"
                if p.suggested_intervention:
                    response += f"   Suggestion: {p.suggested_intervention}\n"
                response += "\n"

            await ctx.reply(response)

    async def _cmd_journey(self, ctx: NexusContext):
        """View member journey analysis."""
        target_id = await self._parse_user(ctx)
        if not target_id:
            await ctx.reply("Usage: !journey [@user|user_id]")
            return

        async with get_db() as db:
            result = await db.execute(
                select(MemberJourney).where(
                    MemberJourney.user_id == target_id,
                    MemberJourney.group_id == ctx.group_id,
                )
            )
            journey = result.scalar_one_or_none()

            if not journey:
                await ctx.reply("No journey data available for this member.")
                return

            trajectory_emoji = {
                "positive": "📈",
                "negative": "📉",
                "neutral": "➡️",
                "unknown": "❓",
            }.get(journey.trajectory, "❓")

            response = f"""🗺️ **Member Journey**

**Trajectory:** {trajectory_emoji} {journey.trajectory.title()}
**Confidence:** {journey.trajectory_confidence * 100:.1f}%

**Onboarding Milestones:**
• Read Rules: {"✅" if journey.read_rules else "❌"}
• Introduced Self: {"✅" if journey.introduced_self else "❌"}
• Responded to Welcome: {"✅" if journey.responded_to_welcome else "❌"}

**First 72 Hours:**
• Messages: {journey.first_72h_messages}
• Reactions Given: {journey.first_72h_reactions_given}
• Reactions Received: {journey.first_72h_reactions_received}
• Violations: {journey.first_72h_violations}

**Status:** {"Active" if journey.became_active else "Inactive"}
"""
            await ctx.reply(response)

    async def _cmd_topics(self, ctx: NexusContext):
        """View trending topics."""
        async with get_db() as db:
            result = await db.execute(
                select(TopicCluster)
                .where(TopicCluster.group_id == ctx.group_id)
                .order_by(desc(TopicCluster.messages_24h))
                .limit(10)
            )
            topics = result.scalars().all()

            if not topics:
                await ctx.reply("No topic data available yet.")
                return

            response = "💬 **Trending Topics**\n\n"
            for t in topics:
                trend = "📈" if t.is_emerging else "📉" if t.is_dying else "➡️"
                flags = []
                if t.is_controversial:
                    flags.append("🔥")
                if t.is_connector:
                    flags.append("🔗")

                response += f"{trend} **{t.name}**\n"
                response += f"   Keywords: {', '.join(t.keywords[:5])}\n"
                response += f"   24h: {t.messages_24h} messages\n"
                if flags:
                    response += f"   {' '.join(flags)}\n"
                response += "\n"

            await ctx.reply(response)

    async def _cmd_graph(self, ctx: NexusContext):
        """Generate conversation graph link."""
        # The actual graph visualization would be in the Mini App
        mini_app_url = ctx.settings.get("MINI_APP_URL", "https://nexus-mini-app.onrender.com")
        graph_url = f"{mini_app_url}/admin/{ctx.group_id}/intelligence/graph"

        await ctx.reply(
            f"📊 **Conversation Graph**\n\n"
            f"View the interactive social graph in the Mini App:\n{graph_url}"
        )

    async def _parse_user(self, ctx: NexusContext) -> Optional[int]:
        """Parse user from command arguments."""
        args = ctx.args or []
        if not args:
            # Check reply
            if ctx.message and ctx.message.reply_to_message:
                return ctx.message.reply_to_message.from_user.id
            return None

        arg = args[0]

        # Mention
        if arg.startswith("@"):
            username = arg[1:]
            # Look up user by username
            async with get_db() as db:
                from shared.models import User
                result = await db.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                return user.telegram_id if user else None

        # User ID
        try:
            return int(arg)
        except ValueError:
            return None


# Module registration
module = GroupIntelligenceModule
