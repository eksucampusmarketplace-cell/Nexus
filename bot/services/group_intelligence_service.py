"""Group Intelligence Service - Core business logic for intelligence features."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import Group, Member, User
from shared.models_intelligence import (
    AnomalyEvent,
    AutomationRule,
    BehaviorPattern,
    BehavioralTripwire,
    BroadcastCampaign,
    ChurnPrediction,
    ConversationEdge,
    ConversationNode,
    DMCampaign,
    MemberBehaviorLog,
    MemberJourney,
    MemberPreferences,
    PredictiveScore,
    TopicCluster,
    ShadowWatchSession,
    TimeCapsule,
)


class GroupIntelligenceService:
    """Service for Group Intelligence features."""

    # ============ PREDICTIVE MODERATION ============

    @staticmethod
    async def log_behavior(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        behavior_type: str,
        behavior_data: Optional[Dict] = None,
        message_id: Optional[int] = None,
    ) -> MemberBehaviorLog:
        """Log a member behavior for pattern analysis."""
        log = MemberBehaviorLog(
            user_id=user_id,
            group_id=group_id,
            behavior_type=behavior_type,
            behavior_data=behavior_data or {},
            message_id=message_id,
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_predictive_score(
        db: AsyncSession,
        user_id: int,
        group_id: int,
    ) -> Optional[PredictiveScore]:
        """Get predictive score for a member."""
        result = await db.execute(
            select(PredictiveScore).where(
                PredictiveScore.user_id == user_id,
                PredictiveScore.group_id == group_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_predictive_score(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        risk_delta: int = 0,
        spam_likelihood_delta: float = 0,
        raid_likelihood_delta: float = 0,
        abuse_likelihood_delta: float = 0,
        matched_pattern: Optional[str] = None,
        behavioral_flag: Optional[str] = None,
    ) -> PredictiveScore:
        """Update predictive score for a member."""
        score = await GroupIntelligenceService.get_predictive_score(db, user_id, group_id)

        if not score:
            score = PredictiveScore(
                user_id=user_id,
                group_id=group_id,
                risk_score=0,
                matched_patterns=[],
                behavioral_flags=[],
            )
            db.add(score)

        # Update scores
        score.risk_score = max(0, min(100, score.risk_score + risk_delta))
        score.spam_likelihood = max(0, min(1, score.spam_likelihood + spam_likelihood_delta))
        score.raid_likelihood = max(0, min(1, score.raid_likelihood + raid_likelihood_delta))
        score.abuse_likelihood = max(0, min(1, score.abuse_likelihood + abuse_likelihood_delta))

        # Add matched pattern
        if matched_pattern and matched_pattern not in score.matched_patterns:
            score.matched_patterns = score.matched_patterns + [matched_pattern]

        # Add behavioral flag
        if behavioral_flag and behavioral_flag not in score.behavioral_flags:
            score.behavioral_flags = score.behavioral_flags + [behavioral_flag]

        # Set first flagged if new
        if score.risk_score > 0 and not score.first_flagged:
            score.first_flagged = datetime.utcnow()

        # Update monitoring level
        if score.risk_score >= 70:
            score.monitoring_level = 2
        elif score.risk_score >= 40:
            score.monitoring_level = 1
        else:
            score.monitoring_level = 0

        score.last_updated = datetime.utcnow()
        await db.flush()
        return score

    @staticmethod
    async def check_patterns(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        behaviors: List[MemberBehaviorLog],
    ) -> List[BehaviorPattern]:
        """Check if behaviors match known patterns."""
        matched = []

        # Get active patterns
        result = await db.execute(
            select(BehaviorPattern).where(BehaviorPattern.is_active == True)
        )
        patterns = result.scalars().all()

        for pattern in patterns:
            if GroupIntelligenceService._match_pattern(pattern, behaviors):
                matched.append(pattern)

        return matched

    @staticmethod
    def _match_pattern(pattern: BehaviorPattern, behaviors: List[MemberBehaviorLog]) -> bool:
        """Check if behaviors match a pattern."""
        if not behaviors or not pattern.sequence:
            return False

        # Check time window
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=pattern.time_window_seconds)
        recent_behaviors = [b for b in behaviors if b.timestamp >= window_start]

        if len(recent_behaviors) < pattern.min_occurrences:
            return False

        # Match sequence
        behavior_types = [b.behavior_type for b in recent_behaviors]
        sequence_types = [s.get("type") for s in pattern.sequence if s.get("type")]

        # Simple matching - check if sequence is a subsequence
        matched = 0
        seq_idx = 0
        for bt in behavior_types:
            if seq_idx < len(sequence_types) and bt == sequence_types[seq_idx]:
                matched += 1
                seq_idx += 1

        return matched >= pattern.min_occurrences

    # ============ CONVERSATION GRAPH ============

    @staticmethod
    async def get_or_create_node(
        db: AsyncSession,
        group_id: int,
        user_id: int,
    ) -> ConversationNode:
        """Get or create a conversation node."""
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
                is_isolated=True,
            )
            db.add(node)
            await db.flush()

        return node

    @staticmethod
    async def record_interaction(
        db: AsyncSession,
        group_id: int,
        source_user_id: int,
        target_user_id: int,
        interaction_type: str,
    ):
        """Record an interaction between two users."""
        if source_user_id == target_user_id:
            return

        # Get or create edge
        result = await db.execute(
            select(ConversationEdge).where(
                ConversationEdge.group_id == group_id,
                ConversationEdge.source_user_id == source_user_id,
                ConversationEdge.target_user_id == target_user_id,
            )
        )
        edge = result.scalar_one_or_none()

        if not edge:
            edge = ConversationEdge(
                group_id=group_id,
                source_user_id=source_user_id,
                target_user_id=target_user_id,
                reply_count=0,
                mention_count=0,
                reaction_count=0,
                forward_count=0,
                strength=0.0,
                reciprocity=0.0,
                avg_sentiment=0.0,
            )
            db.add(edge)

        # Increment counter
        if interaction_type == "reply":
            edge.reply_count += 1
        elif interaction_type == "mention":
            edge.mention_count += 1
        elif interaction_type == "reaction":
            edge.reaction_count += 1
        elif interaction_type == "forward":
            edge.forward_count += 1

        edge.strength = (edge.reply_count + edge.mention_count * 0.5 + edge.reaction_count * 0.3) / 10
        edge.last_interaction = datetime.utcnow()

        # Update source node
        source_node = await GroupIntelligenceService.get_or_create_node(
            db, group_id, source_user_id
        )
        source_node.total_interactions += 1
        source_node.messages_sent += 1
        source_node.is_isolated = False

        # Update target node
        target_node = await GroupIntelligenceService.get_or_create_node(
            db, group_id, target_user_id
        )
        target_node.replies_received += 1
        target_node.is_isolated = False

        await db.flush()

    @staticmethod
    async def calculate_influence_scores(db: AsyncSession, group_id: int):
        """Calculate influence scores for all nodes in a group."""
        # Get all nodes
        result = await db.execute(
            select(ConversationNode).where(ConversationNode.group_id == group_id)
        )
        nodes = result.scalars().all()

        # Get all edges
        result = await db.execute(
            select(ConversationEdge).where(ConversationEdge.group_id == group_id)
        )
        edges = result.scalars().all()

        # Build adjacency
        outgoing = {n.user_id: [] for n in nodes}
        incoming = {n.user_id: [] for n in nodes}

        for e in edges:
            if e.source_user_id in outgoing:
                outgoing[e.source_user_id].append((e.target_user_id, e.strength))
            if e.target_user_id in incoming:
                incoming[e.target_user_id].append((e.source_user_id, e.strength))

        # Calculate simple influence score
        for node in nodes:
            # Influence = replies received * 2 + mentions * 1.5 + reactions
            replies = sum(s for _, s in incoming.get(node.user_id, []))
            mentions = sum(1 for _ in incoming.get(node.user_id, []))
            
            node.influence_score = min(100, (
                node.replies_received * 0.4 +
                node.reactions_received * 0.3 +
                mentions * 0.3
            ))

        await db.flush()

    # ============ ANOMALY DETECTION ============

    @staticmethod
    async def create_anomaly(
        db: AsyncSession,
        group_id: int,
        anomaly_type: str,
        title: str,
        description: str,
        severity: int = 1,
        deviation_score: float = 0.0,
        baseline_value: float = 0.0,
        actual_value: float = 0.0,
        involved_users: Optional[List[int]] = None,
        context_data: Optional[Dict] = None,
    ) -> AnomalyEvent:
        """Create an anomaly event."""
        anomaly = AnomalyEvent(
            anomaly_id=f"anom_{uuid.uuid4().hex[:12]}",
            group_id=group_id,
            anomaly_type=anomaly_type,
            title=title,
            description=description,
            severity=severity,
            deviation_score=deviation_score,
            baseline_value=baseline_value,
            actual_value=actual_value,
            involved_users=involved_users or [],
            context_data=context_data,
            detected_at=datetime.utcnow(),
        )
        db.add(anomaly)
        await db.flush()
        return anomaly

    @staticmethod
    async def resolve_anomaly(
        db: AsyncSession,
        anomaly_id: str,
        action_taken: str,
        action_by: int,
    ) -> Optional[AnomalyEvent]:
        """Resolve an anomaly."""
        result = await db.execute(
            select(AnomalyEvent).where(AnomalyEvent.anomaly_id == anomaly_id)
        )
        anomaly = result.scalar_one_or_none()

        if anomaly:
            anomaly.action_taken = action_taken
            anomaly.action_by = action_by
            anomaly.resolved_at = datetime.utcnow()
            await db.flush()

        return anomaly

    # ============ MEMBER JOURNEY ============

    @staticmethod
    async def get_or_create_journey(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        joined_at: Optional[datetime] = None,
    ) -> MemberJourney:
        """Get or create a member journey record."""
        result = await db.execute(
            select(MemberJourney).where(
                MemberJourney.user_id == user_id,
                MemberJourney.group_id == group_id,
            )
        )
        journey = result.scalar_one_or_none()

        if not journey:
            journey = MemberJourney(
                user_id=user_id,
                group_id=group_id,
                joined_at=joined_at or datetime.utcnow(),
            )
            db.add(journey)
            await db.flush()

        return journey

    @staticmethod
    async def record_journey_milestone(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        milestone: str,
    ):
        """Record a journey milestone."""
        journey = await GroupIntelligenceService.get_or_create_journey(
            db, user_id, group_id
        )

        now = datetime.utcnow()

        if milestone == "first_message" and not journey.first_message_at:
            journey.first_message_at = now
        elif milestone == "first_reply" and not journey.first_reply_at:
            journey.first_reply_at = now
        elif milestone == "first_reaction" and not journey.first_reaction_at:
            journey.first_reaction_at = now
        elif milestone == "read_rules":
            journey.read_rules = True
            journey.read_rules_at = now
        elif milestone == "introduced_self":
            journey.introduced_self = True
            journey.introduced_at = now
        elif milestone == "responded_to_welcome":
            journey.responded_to_welcome = True

        # Update 72h metrics if applicable
        if journey.joined_at:
            hours_since_join = (now - journey.joined_at).total_seconds() / 3600
            if hours_since_join <= 72:
                if milestone == "first_message":
                    journey.first_72h_messages += 1
                elif milestone == "first_reaction":
                    journey.first_72h_reactions_given += 1

        await db.flush()

    @staticmethod
    async def calculate_trajectory(
        db: AsyncSession,
        user_id: int,
        group_id: int,
    ) -> Tuple[str, float]:
        """Calculate member trajectory based on early behavior."""
        journey = await GroupIntelligenceService.get_or_create_journey(db, user_id, group_id)

        # Simple trajectory calculation
        score = 0.0

        # Positive indicators
        if journey.read_rules:
            score += 10
        if journey.introduced_self:
            score += 15
        if journey.responded_to_welcome:
            score += 10
        if journey.first_72h_messages > 5:
            score += 20
        if journey.first_72h_reactions_received > 3:
            score += 15

        # Negative indicators
        if journey.first_72h_violations > 0:
            score -= journey.first_72h_violations * 20
        if not journey.first_message_at and journey.joined_at:
            hours_silent = (datetime.utcnow() - journey.joined_at).total_seconds() / 3600
            if hours_silent > 24:
                score -= 30

        # Determine trajectory
        if score >= 30:
            trajectory = "positive"
            confidence = min(1.0, score / 60)
        elif score <= -20:
            trajectory = "negative"
            confidence = min(1.0, abs(score) / 40)
        else:
            trajectory = "neutral"
            confidence = 0.5

        journey.trajectory = trajectory
        journey.trajectory_confidence = confidence
        journey.engagement_trend = score / 100

        await db.flush()
        return trajectory, confidence

    # ============ CHURN PREDICTION ============

    @staticmethod
    async def get_or_create_churn_prediction(
        db: AsyncSession,
        user_id: int,
        group_id: int,
    ) -> ChurnPrediction:
        """Get or create churn prediction."""
        result = await db.execute(
            select(ChurnPrediction).where(
                ChurnPrediction.user_id == user_id,
                ChurnPrediction.group_id == group_id,
            )
        )
        prediction = result.scalar_one_or_none()

        if not prediction:
            prediction = ChurnPrediction(
                user_id=user_id,
                group_id=group_id,
                churn_risk=0.0,
                engagement_decline_rate=0.0,
                days_inactive=0,
            )
            db.add(prediction)
            await db.flush()

        return prediction

    @staticmethod
    async def update_churn_risk(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        last_active: datetime,
        message_count_7d: int,
        reaction_count_7d: int,
    ):
        """Update churn risk for a member."""
        prediction = await GroupIntelligenceService.get_or_create_churn_prediction(
            db, user_id, group_id
        )

        # Calculate days inactive
        prediction.days_inactive = (datetime.utcnow() - last_active).days

        # Calculate churn risk
        risk = 0.0

        # Inactivity risk
        if prediction.days_inactive > 30:
            risk += 0.4
        elif prediction.days_inactive > 14:
            risk += 0.2
        elif prediction.days_inactive > 7:
            risk += 0.1

        # Low engagement risk
        if message_count_7d < 5:
            risk += 0.2
        if reaction_count_7d < 2:
            risk += 0.1

        # Cap at 1.0
        prediction.churn_risk = min(1.0, risk)

        # Suggest intervention
        if prediction.churn_risk > 0.5:
            if prediction.days_inactive > 14:
                prediction.suggested_intervention = "send_dm"
            else:
                prediction.suggested_intervention = "invite_to_event"
            prediction.intervention_priority = int(prediction.churn_risk * 10)

        prediction.last_updated = datetime.utcnow()
        await db.flush()

    # ============ AUTOMATION ============

    @staticmethod
    async def create_automation_rule(
        db: AsyncSession,
        group_id: int,
        name: str,
        conditions: List[Dict],
        actions: List[Dict],
        trigger_type: str,
        created_by: int,
        description: Optional[str] = None,
        condition_logic: str = "and",
        priority: int = 0,
        cooldown_seconds: int = 0,
    ) -> AutomationRule:
        """Create an automation rule."""
        rule = AutomationRule(
            rule_id=f"rule_{uuid.uuid4().hex[:12]}",
            group_id=group_id,
            name=name,
            description=description,
            conditions=conditions,
            condition_logic=condition_logic,
            actions=actions,
            trigger_type=trigger_type,
            is_enabled=True,
            priority=priority,
            cooldown_seconds=cooldown_seconds,
            created_by=created_by,
        )
        db.add(rule)
        await db.flush()
        return rule

    @staticmethod
    async def evaluate_conditions(
        conditions: List[Dict],
        condition_logic: str,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate automation conditions against context."""
        results = []

        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            context_value = context.get(field)

            if context_value is None:
                results.append(False)
                continue

            # Evaluate
            if operator == "eq":
                results.append(context_value == value)
            elif operator == "ne":
                results.append(context_value != value)
            elif operator == "gt":
                results.append(context_value > value)
            elif operator == "lt":
                results.append(context_value < value)
            elif operator == "gte":
                results.append(context_value >= value)
            elif operator == "lte":
                results.append(context_value <= value)
            elif operator == "contains":
                results.append(str(value).lower() in str(context_value).lower())
            elif operator == "matches":
                import re
                results.append(bool(re.search(value, str(context_value))))
            elif operator == "in":
                results.append(context_value in value)
            else:
                results.append(False)

        # Apply logic
        if condition_logic == "and":
            return all(results)
        else:
            return any(results)

    # ============ SHADOW WATCH ============

    @staticmethod
    async def start_shadow_watch(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        started_by: int,
        reason: Optional[str] = None,
        delay_seconds: int = 5,
    ) -> ShadowWatchSession:
        """Start a shadow watch session."""
        # End any existing session
        result = await db.execute(
            select(ShadowWatchSession).where(
                ShadowWatchSession.user_id == user_id,
                ShadowWatchSession.group_id == group_id,
                ShadowWatchSession.is_active == True,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = False
            existing.ended_at = datetime.utcnow()

        # Create new session
        session = ShadowWatchSession(
            user_id=user_id,
            group_id=group_id,
            started_by=started_by,
            reason=reason,
            delay_seconds=delay_seconds,
            is_active=True,
        )
        db.add(session)

        # Update predictive score
        score = await GroupIntelligenceService.get_predictive_score(db, user_id, group_id)
        if score:
            score.shadow_watch = True
            score.monitoring_level = 2

        await db.flush()
        return session

    @staticmethod
    async def end_shadow_watch(
        db: AsyncSession,
        session_id: int,
    ):
        """End a shadow watch session."""
        result = await db.execute(
            select(ShadowWatchSession).where(ShadowWatchSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            session.ended_at = datetime.utcnow()

            # Update predictive score
            score = await GroupIntelligenceService.get_predictive_score(
                db, session.user_id, session.group_id
            )
            if score:
                score.shadow_watch = False
                score.monitoring_level = max(0, score.monitoring_level - 1)

            await db.flush()

    # ============ TIME CAPSULES ============

    @staticmethod
    async def create_time_capsule(
        db: AsyncSession,
        group_id: int,
        created_by: int,
        title: str,
        message: str,
        open_at: datetime,
        capsule_type: str = "message",
        media_file_id: Optional[str] = None,
    ) -> TimeCapsule:
        """Create a time capsule."""
        capsule = TimeCapsule(
            capsule_id=f"cap_{uuid.uuid4().hex[:12]}",
            group_id=group_id,
            title=title,
            message=message,
            open_at=open_at,
            created_by=created_by,
            capsule_type=capsule_type,
            media_file_id=media_file_id,
        )
        db.add(capsule)
        await db.flush()
        return capsule

    @staticmethod
    async def get_ready_capsules(db: AsyncSession) -> List[TimeCapsule]:
        """Get capsules ready to be opened."""
        now = datetime.utcnow()
        result = await db.execute(
            select(TimeCapsule).where(
                TimeCapsule.open_at <= now,
                TimeCapsule.opened_at == None,
            )
        )
        return result.scalars().all()

    # ============ MEMBER PREFERENCES ============

    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession,
        user_id: int,
        group_id: int,
    ) -> MemberPreferences:
        """Get or create member preferences."""
        result = await db.execute(
            select(MemberPreferences).where(
                MemberPreferences.user_id == user_id,
                MemberPreferences.group_id == group_id,
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            prefs = MemberPreferences(
                user_id=user_id,
                group_id=group_id,
            )
            db.add(prefs)
            await db.flush()

        return prefs

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        user_id: int,
        group_id: int,
        updates: Dict[str, Any],
    ) -> MemberPreferences:
        """Update member preferences."""
        prefs = await GroupIntelligenceService.get_or_create_preferences(
            db, user_id, group_id
        )

        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.utcnow()
        await db.flush()
        return prefs
