"""API router for Group Intelligence features."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import Group, Member, User
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
from shared.schemas_intelligence import (
    AnomalyEventResponse,
    AnomalyTimelineResponse,
    AutomationRuleCreate,
    AutomationRuleResponse,
    BehavioralTripwireCreate,
    BehavioralTripwireResponse,
    BroadcastCampaignCreate,
    BroadcastCampaignResponse,
    ChurnPredictionResponse,
    ChurnRiskPanelResponse,
    ConversationGraphResponse,
    ConversationNodeResponse,
    DMCampaignCreate,
    DMCampaignResponse,
    GroupIntelligenceConfig,
    GroupOathResponse,
    GroupOathUpdate,
    GroupThemeResponse,
    GroupThemeUpdate,
    IntelligenceOverviewResponse,
    LegacyMemberCreate,
    LegacyMemberResponse,
    MemberIntelligenceResponse,
    MemberJourneyResponse,
    MemberPreferencesResponse,
    MemberPreferencesUpdate,
    PredictiveScoreResponse,
    ShadowWatchSessionCreate,
    ShadowWatchSessionResponse,
    TimeCapsuleCreate,
    TimeCapsuleResponse,
    TimeBasedRuleSetCreate,
    TimeBasedRuleSetResponse,
    TopicClusterResponse,
    TopicLandscapeResponse,
    VerificationLevelResponse,
    WebhookConfigCreate,
    WebhookConfigResponse,
)
from api.routers.auth import get_current_user

router = APIRouter()


# ============ INTELLIGENCE OVERVIEW ============


@router.get("/groups/{group_id}/intelligence", response_model=IntelligenceOverviewResponse)
async def get_intelligence_overview(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the intelligence overview for a group."""
    # Verify user is admin
    await _verify_admin(db, group_id, user.id)

    # Get predictive moderation stats
    predictive_stats = await _get_predictive_stats(db, group_id)

    # Get conversation graph summary
    graph_stats = await _get_graph_stats(db, group_id)

    # Get anomaly timeline
    anomaly_timeline = await _get_anomaly_timeline(db, group_id, hours=168)

    # Get journey stats
    journey_stats = await _get_journey_stats(db, group_id)

    # Get topic landscape
    topic_landscape = await _get_topic_landscape(db, group_id)

    # Get churn predictions
    churn_panel = await _get_churn_panel(db, group_id)

    return IntelligenceOverviewResponse(
        predictive_moderation=predictive_stats,
        conversation_graph=graph_stats,
        anomaly_timeline=anomaly_timeline,
        member_journeys=journey_stats,
        topic_intelligence=topic_landscape,
        churn_predictions=churn_panel,
    )


@router.get("/groups/{group_id}/members/{user_id}/intelligence", response_model=MemberIntelligenceResponse)
async def get_member_intelligence(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get intelligence data for a specific member."""
    await _verify_admin(db, group_id, current_user.id)

    # Get predictive score
    score_result = await db.execute(
        select(PredictiveScore).where(
            PredictiveScore.group_id == group_id,
            PredictiveScore.user_id == user_id,
        )
    )
    predictive_score = score_result.scalar_one_or_none()

    # Get journey
    journey_result = await db.execute(
        select(MemberJourney).where(
            MemberJourney.group_id == group_id,
            MemberJourney.user_id == user_id,
        )
    )
    journey = journey_result.scalar_one_or_none()

    # Get churn prediction
    churn_result = await db.execute(
        select(ChurnPrediction).where(
            ChurnPrediction.group_id == group_id,
            ChurnPrediction.user_id == user_id,
        )
    )
    churn = churn_result.scalar_one_or_none()

    # Get conversation node
    node_result = await db.execute(
        select(ConversationNode).where(
            ConversationNode.group_id == group_id,
            ConversationNode.user_id == user_id,
        )
    )
    node = node_result.scalar_one_or_none()

    return MemberIntelligenceResponse(
        predictive_score=PredictiveScoreResponse.model_validate(predictive_score) if predictive_score else None,
        journey=MemberJourneyResponse.model_validate(journey) if journey else None,
        churn_prediction=ChurnPredictionResponse.model_validate(churn) if churn else None,
        conversation_node=ConversationNodeResponse.model_validate(node) if node else None,
        verification_level=None,
        preferences=None,
    )


# ============ PREDICTIVE MODERATION ============


@router.get("/groups/{group_id}/predictive-scores", response_model=List[PredictiveScoreResponse])
async def get_predictive_scores(
    group_id: int,
    min_risk: int = Query(0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get predictive risk scores for members."""
    await _verify_admin(db, group_id, user.id)

    result = await db.execute(
        select(PredictiveScore)
        .where(
            PredictiveScore.group_id == group_id,
            PredictiveScore.risk_score >= min_risk,
        )
        .order_by(desc(PredictiveScore.risk_score))
        .limit(limit)
    )
    scores = result.scalars().all()

    return [PredictiveScoreResponse.model_validate(s) for s in scores]


@router.get("/groups/{group_id}/behavior-patterns", response_model=List[BehaviorPattern])
async def get_behavior_patterns(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get behavior patterns."""
    await _verify_admin(db, group_id, user.id)

    result = await db.execute(
        select(BehaviorPattern).where(BehaviorPattern.is_active == True)
    )
    return result.scalars().all()


# ============ CONVERSATION GRAPH ============


@router.get("/groups/{group_id}/conversation-graph", response_model=ConversationGraphResponse)
async def get_conversation_graph(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the full conversation graph for visualization."""
    await _verify_admin(db, group_id, user.id)

    # Get all nodes
    nodes_result = await db.execute(
        select(ConversationNode).where(ConversationNode.group_id == group_id)
    )
    nodes = nodes_result.scalars().all()

    # Get all edges
    edges_result = await db.execute(
        select(ConversationEdge).where(ConversationEdge.group_id == group_id)
    )
    edges = edges_result.scalars().all()

    # Find cliques (simplified - would use network analysis in production)
    cliques = await _detect_cliques(nodes, edges)

    # Find isolated members
    isolated = [n.user_id for n in nodes if n.is_isolated]

    # Find top influencers
    sorted_nodes = sorted(nodes, key=lambda n: n.influence_score, reverse=True)
    top_influencers = [n.user_id for n in sorted_nodes[:10]]

    # Find bridges
    bridges = await _find_bridges(nodes, edges)

    return ConversationGraphResponse(
        nodes=[ConversationNodeResponse.model_validate(n) for n in nodes],
        edges=[{
            "source": e.source_user_id,
            "target": e.target_user_id,
            "strength": e.strength,
            "reply_count": e.reply_count,
            "mention_count": e.mention_count,
        } for e in edges],
        cliques=cliques,
        isolated_members=isolated,
        top_influencers=top_influencers,
        bridges=bridges,
    )


# ============ ANOMALY TIMELINE ============


@router.get("/groups/{group_id}/anomalies", response_model=AnomalyTimelineResponse)
async def get_anomalies(
    group_id: int,
    hours: int = Query(168, ge=1, le=720),
    severity: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get anomaly timeline for a group."""
    await _verify_admin(db, group_id, user.id)

    timeline = await _get_anomaly_timeline(db, group_id, hours, severity)
    return timeline


@router.post("/groups/{group_id}/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    group_id: int,
    anomaly_id: str,
    action_taken: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark an anomaly as resolved."""
    await _verify_admin(db, group_id, user.id)

    result = await db.execute(
        select(AnomalyEvent).where(
            AnomalyEvent.anomaly_id == anomaly_id,
            AnomalyEvent.group_id == group_id,
        )
    )
    anomaly = result.scalar_one_or_none()

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.action_taken = action_taken
    anomaly.action_by = user.id
    anomaly.resolved_at = datetime.utcnow()

    await db.commit()

    return {"status": "resolved", "anomaly_id": anomaly_id}


# ============ MEMBER JOURNEY ============


@router.get("/groups/{group_id}/journeys", response_model=List[MemberJourneyResponse])
async def get_member_journeys(
    group_id: int,
    trajectory: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get member journeys for a group."""
    await _verify_admin(db, group_id, user.id)

    query = select(MemberJourney).where(MemberJourney.group_id == group_id)

    if trajectory:
        query = query.where(MemberJourney.trajectory == trajectory)

    query = query.order_by(desc(MemberJourney.joined_at)).limit(limit)

    result = await db.execute(query)
    journeys = result.scalars().all()

    return [MemberJourneyResponse.model_validate(j) for j in journeys]


@router.get("/groups/{group_id}/journeys/{user_id}", response_model=MemberJourneyResponse)
async def get_member_journey(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get journey for a specific member."""
    await _verify_admin(db, group_id, current_user.id)

    result = await db.execute(
        select(MemberJourney).where(
            MemberJourney.group_id == group_id,
            MemberJourney.user_id == user_id,
        )
    )
    journey = result.scalar_one_or_none()

    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    return MemberJourneyResponse.model_validate(journey)


# ============ TOPIC INTELLIGENCE ============


@router.get("/groups/{group_id}/topics", response_model=TopicLandscapeResponse)
async def get_topics(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get topic landscape for a group."""
    await _verify_admin(db, group_id, user.id)

    landscape = await _get_topic_landscape(db, group_id)
    return landscape


# ============ CHURN PREDICTION ============


@router.get("/groups/{group_id}/churn-predictions", response_model=ChurnRiskPanelResponse)
async def get_churn_predictions(
    group_id: int,
    min_risk: float = Query(0.3, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get churn predictions for members."""
    await _verify_admin(db, group_id, user.id)

    panel = await _get_churn_panel(db, group_id, min_risk)
    return panel


# ============ AUTOMATION RULES ============


@router.get("/groups/{group_id}/automation-rules", response_model=List[AutomationRuleResponse])
async def get_automation_rules(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get automation rules for a group."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import AutomationRule

    result = await db.execute(
        select(AutomationRule).where(AutomationRule.group_id == group_id)
    )
    rules = result.scalars().all()

    return [AutomationRuleResponse.model_validate(r) for r in rules]


@router.post("/groups/{group_id}/automation-rules", response_model=AutomationRuleResponse)
async def create_automation_rule(
    group_id: int,
    rule: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new automation rule."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import AutomationRule
    import uuid

    rule_obj = AutomationRule(
        rule_id=f"rule_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        created_by=user.id,
        **rule.model_dump(),
    )

    db.add(rule_obj)
    await db.commit()
    await db.refresh(rule_obj)

    return AutomationRuleResponse.model_validate(rule_obj)


# ============ BEHAVIORAL TRIPWIRES ============


@router.get("/groups/{group_id}/tripwires", response_model=List[BehavioralTripwireResponse])
async def get_tripwires(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get behavioral tripwires for a group."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import BehavioralTripwire

    result = await db.execute(
        select(BehavioralTripwire).where(BehavioralTripwire.group_id == group_id)
    )
    tripwires = result.scalars().all()

    return [BehavioralTripwireResponse.model_validate(t) for t in tripwires]


@router.post("/groups/{group_id}/tripwires", response_model=BehavioralTripwireResponse)
async def create_tripwire(
    group_id: int,
    tripwire: BehavioralTripwireCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a behavioral tripwire."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import BehavioralTripwire
    import uuid

    tripwire_obj = BehavioralTripwire(
        tripwire_id=f"tw_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        **tripwire.model_dump(),
    )

    db.add(tripwire_obj)
    await db.commit()
    await db.refresh(tripwire_obj)

    return BehavioralTripwireResponse.model_validate(tripwire_obj)


# ============ TIME-BASED RULE SETS ============


@router.get("/groups/{group_id}/time-rules", response_model=List[TimeBasedRuleSetResponse])
async def get_time_rules(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get time-based rule sets."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import TimeBasedRuleSet

    result = await db.execute(
        select(TimeBasedRuleSet).where(TimeBasedRuleSet.group_id == group_id)
    )
    rules = result.scalars().all()

    return [TimeBasedRuleSetResponse.model_validate(r) for r in rules]


@router.post("/groups/{group_id}/time-rules", response_model=TimeBasedRuleSetResponse)
async def create_time_rule(
    group_id: int,
    rule: TimeBasedRuleSetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a time-based rule set."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import TimeBasedRuleSet
    import uuid

    rule_obj = TimeBasedRuleSet(
        ruleset_id=f"trs_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        **rule.model_dump(),
    )

    db.add(rule_obj)
    await db.commit()
    await db.refresh(rule_obj)

    return TimeBasedRuleSetResponse.model_validate(rule_obj)


# ============ BROADCAST CAMPAIGNS ============


@router.get("/groups/{group_id}/broadcasts", response_model=List[BroadcastCampaignResponse])
async def get_broadcasts(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get broadcast campaigns."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import BroadcastCampaign

    result = await db.execute(
        select(BroadcastCampaign).where(BroadcastCampaign.group_id == group_id)
    )
    broadcasts = result.scalars().all()

    return [BroadcastCampaignResponse.model_validate(b) for b in broadcasts]


@router.post("/groups/{group_id}/broadcasts", response_model=BroadcastCampaignResponse)
async def create_broadcast(
    group_id: int,
    broadcast: BroadcastCampaignCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a broadcast campaign."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import BroadcastCampaign
    import uuid

    broadcast_obj = BroadcastCampaign(
        campaign_id=f"bc_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        created_by=user.id,
        **broadcast.model_dump(),
    )

    db.add(broadcast_obj)
    await db.commit()
    await db.refresh(broadcast_obj)

    return BroadcastCampaignResponse.model_validate(broadcast_obj)


# ============ DM CAMPAIGNS ============


@router.get("/groups/{group_id}/dm-campaigns", response_model=List[DMCampaignResponse])
async def get_dm_campaigns(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get DM campaigns."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import DMCampaign

    result = await db.execute(
        select(DMCampaign).where(DMCampaign.group_id == group_id)
    )
    campaigns = result.scalars().all()

    return [DMCampaignResponse.model_validate(c) for c in campaigns]


@router.post("/groups/{group_id}/dm-campaigns", response_model=DMCampaignResponse)
async def create_dm_campaign(
    group_id: int,
    campaign: DMCampaignCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a DM campaign."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import DMCampaign
    import uuid

    campaign_obj = DMCampaign(
        campaign_id=f"dm_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        created_by=user.id,
        **campaign.model_dump(),
    )

    db.add(campaign_obj)
    await db.commit()
    await db.refresh(campaign_obj)

    return DMCampaignResponse.model_validate(campaign_obj)


# ============ MEMBER PREFERENCES ============


@router.get("/groups/{group_id}/members/{user_id}/preferences", response_model=MemberPreferencesResponse)
async def get_member_preferences(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get member preferences."""
    # Users can only access their own preferences unless admin
    if current_user.id != user_id:
        await _verify_admin(db, group_id, current_user.id)

    from shared.models_intelligence import MemberPreferences

    result = await db.execute(
        select(MemberPreferences).where(
            MemberPreferences.group_id == group_id,
            MemberPreferences.user_id == user_id,
        )
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Create default preferences
        prefs = MemberPreferences(
            user_id=user_id,
            group_id=group_id,
        )
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return MemberPreferencesResponse.model_validate(prefs)


@router.patch("/groups/{group_id}/members/{user_id}/preferences", response_model=MemberPreferencesResponse)
async def update_member_preferences(
    group_id: int,
    user_id: int,
    update: MemberPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update member preferences."""
    # Users can only update their own preferences
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update own preferences")

    from shared.models_intelligence import MemberPreferences

    result = await db.execute(
        select(MemberPreferences).where(
            MemberPreferences.group_id == group_id,
            MemberPreferences.user_id == user_id,
        )
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = MemberPreferences(
            user_id=user_id,
            group_id=group_id,
        )
        db.add(prefs)

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)

    await db.commit()
    await db.refresh(prefs)

    return MemberPreferencesResponse.model_validate(prefs)


# ============ GROUP THEME ============


@router.get("/groups/{group_id}/theme", response_model=GroupThemeResponse)
async def get_group_theme(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get group theme."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import GroupTheme

    result = await db.execute(
        select(GroupTheme).where(GroupTheme.group_id == group_id)
    )
    theme = result.scalar_one_or_none()

    if not theme:
        # Return default theme
        theme = GroupTheme(group_id=group_id)

    return GroupThemeResponse.model_validate(theme)


@router.patch("/groups/{group_id}/theme", response_model=GroupThemeResponse)
async def update_group_theme(
    group_id: int,
    update: GroupThemeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update group theme."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import GroupTheme

    result = await db.execute(
        select(GroupTheme).where(GroupTheme.group_id == group_id)
    )
    theme = result.scalar_one_or_none()

    if not theme:
        theme = GroupTheme(group_id=group_id)
        db.add(theme)

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(theme, key, value)

    await db.commit()
    await db.refresh(theme)

    return GroupThemeResponse.model_validate(theme)


# ============ SHADOW WATCH ============


@router.get("/groups/{group_id}/shadow-watch", response_model=List[ShadowWatchSessionResponse])
async def get_shadow_watch_sessions(
    group_id: int,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get shadow watch sessions."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import ShadowWatchSession

    query = select(ShadowWatchSession).where(ShadowWatchSession.group_id == group_id)

    if active_only:
        query = query.where(ShadowWatchSession.is_active == True)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [ShadowWatchSessionResponse.model_validate(s) for s in sessions]


@router.post("/groups/{group_id}/shadow-watch", response_model=ShadowWatchSessionResponse)
async def create_shadow_watch(
    group_id: int,
    session: ShadowWatchSessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a shadow watch session."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import ShadowWatchSession
    import uuid

    session_obj = ShadowWatchSession(
        user_id=session.user_id,
        group_id=group_id,
        started_by=user.id,
        delay_seconds=session.delay_seconds,
        notify_channel_id=session.notify_channel_id,
        reason=session.reason,
    )

    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)

    return ShadowWatchSessionResponse.model_validate(session_obj)


@router.delete("/groups/{group_id}/shadow-watch/{session_id}")
async def end_shadow_watch(
    group_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """End a shadow watch session."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import ShadowWatchSession

    result = await db.execute(
        select(ShadowWatchSession).where(
            ShadowWatchSession.id == session_id,
            ShadowWatchSession.group_id == group_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    session.ended_at = datetime.utcnow()

    await db.commit()

    return {"status": "ended"}


# ============ TIME CAPSULES ============


@router.get("/groups/{group_id}/time-capsules", response_model=List[TimeCapsuleResponse])
async def get_time_capsules(
    group_id: int,
    include_opened: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get time capsules."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import TimeCapsule

    query = select(TimeCapsule).where(TimeCapsule.group_id == group_id)

    if not include_opened:
        query = query.where(TimeCapsule.opened_at == None)

    result = await db.execute(query)
    capsules = result.scalars().all()

    return [TimeCapsuleResponse.model_validate(c) for c in capsules]


@router.post("/groups/{group_id}/time-capsules", response_model=TimeCapsuleResponse)
async def create_time_capsule(
    group_id: int,
    capsule: TimeCapsuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a time capsule."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import TimeCapsule
    import uuid

    capsule_obj = TimeCapsule(
        capsule_id=f"cap_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        created_by=user.id,
        **capsule.model_dump(),
    )

    db.add(capsule_obj)
    await db.commit()
    await db.refresh(capsule_obj)

    return TimeCapsuleResponse.model_validate(capsule_obj)


# ============ LEGACY MEMBERS ============


@router.get("/groups/{group_id}/legacy-members", response_model=List[LegacyMemberResponse])
async def get_legacy_members(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get legacy members."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import LegacyMember

    result = await db.execute(
        select(LegacyMember).where(LegacyMember.group_id == group_id)
    )
    members = result.scalars().all()

    return [LegacyMemberResponse.model_validate(m) for m in members]


@router.post("/groups/{group_id}/legacy-members", response_model=LegacyMemberResponse)
async def create_legacy_member(
    group_id: int,
    legacy: LegacyMemberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a legacy member record."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import LegacyMember

    legacy_obj = LegacyMember(
        group_id=group_id,
        **legacy.model_dump(),
    )

    db.add(legacy_obj)
    await db.commit()
    await db.refresh(legacy_obj)

    return LegacyMemberResponse.model_validate(legacy_obj)


# ============ GROUP OATH ============


@router.get("/groups/{group_id}/oath", response_model=GroupOathResponse)
async def get_group_oath(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get group oath configuration."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import GroupOath

    result = await db.execute(
        select(GroupOath).where(GroupOath.group_id == group_id)
    )
    oath = result.scalar_one_or_none()

    if not oath:
        raise HTTPException(status_code=404, detail="No oath configured")

    return GroupOathResponse.model_validate(oath)


@router.put("/groups/{group_id}/oath", response_model=GroupOathResponse)
async def update_group_oath(
    group_id: int,
    update: GroupOathUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update group oath configuration."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import GroupOath

    result = await db.execute(
        select(GroupOath).where(GroupOath.group_id == group_id)
    )
    oath = result.scalar_one_or_none()

    if not oath:
        if not update.oath_text or not update.confirmation_phrase:
            raise HTTPException(status_code=400, detail="Oath text and confirmation phrase required")
        oath = GroupOath(group_id=group_id)
        db.add(oath)

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(oath, key, value)

    await db.commit()
    await db.refresh(oath)

    return GroupOathResponse.model_validate(oath)


# ============ WEBHOOKS ============


@router.get("/groups/{group_id}/webhooks", response_model=List[WebhookConfigResponse])
async def get_webhooks(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get webhook configurations."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import WebhookConfig

    result = await db.execute(
        select(WebhookConfig).where(WebhookConfig.group_id == group_id)
    )
    webhooks = result.scalars().all()

    return [WebhookConfigResponse.model_validate(w) for w in webhooks]


@router.post("/groups/{group_id}/webhooks", response_model=WebhookConfigResponse)
async def create_webhook(
    group_id: int,
    webhook: WebhookConfigCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a webhook configuration."""
    await _verify_admin(db, group_id, user.id)

    from shared.models_intelligence import WebhookConfig
    import uuid

    webhook_obj = WebhookConfig(
        webhook_id=f"wh_{uuid.uuid4().hex[:12]}",
        group_id=group_id,
        **webhook.model_dump(),
    )

    db.add(webhook_obj)
    await db.commit()
    await db.refresh(webhook_obj)

    return WebhookConfigResponse.model_validate(webhook_obj)


# ============ HELPER FUNCTIONS ============


async def _verify_admin(db: AsyncSession, group_id: int, user_id: int):
    """Verify user is an admin of the group."""
    result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")


async def _get_predictive_stats(db: AsyncSession, group_id: int) -> Dict[str, Any]:
    """Get predictive moderation statistics."""
    # Count members by risk level
    high_risk = await db.execute(
        select(func.count(PredictiveScore.id)).where(
            PredictiveScore.group_id == group_id,
            PredictiveScore.risk_score >= 70,
        )
    )
    high_risk_count = high_risk.scalar() or 0

    medium_risk = await db.execute(
        select(func.count(PredictiveScore.id)).where(
            PredictiveScore.group_id == group_id,
            PredictiveScore.risk_score >= 30,
            PredictiveScore.risk_score < 70,
        )
    )
    medium_risk_count = medium_risk.scalar() or 0

    shadow_watch = await db.execute(
        select(func.count(PredictiveScore.id)).where(
            PredictiveScore.group_id == group_id,
            PredictiveScore.shadow_watch == True,
        )
    )
    shadow_watch_count = shadow_watch.scalar() or 0

    return {
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "shadow_watch_count": shadow_watch_count,
        "patterns_detected": 0,
    }


async def _get_graph_stats(db: AsyncSession, group_id: int) -> Dict[str, Any]:
    """Get conversation graph statistics."""
    nodes_count = await db.execute(
        select(func.count(ConversationNode.id)).where(
            ConversationNode.group_id == group_id
        )
    )
    total_nodes = nodes_count.scalar() or 0

    edges_count = await db.execute(
        select(func.count(ConversationEdge.id)).where(
            ConversationEdge.group_id == group_id
        )
    )
    total_edges = edges_count.scalar() or 0

    isolated = await db.execute(
        select(func.count(ConversationNode.id)).where(
            ConversationNode.group_id == group_id,
            ConversationNode.is_isolated == True,
        )
    )
    isolated_count = isolated.scalar() or 0

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "isolated_members": isolated_count,
    }


async def _get_anomaly_timeline(
    db: AsyncSession, group_id: int, hours: int, severity: Optional[int] = None
) -> AnomalyTimelineResponse:
    """Get anomaly timeline."""
    query = select(AnomalyEvent).where(
        AnomalyEvent.group_id == group_id,
        AnomalyEvent.detected_at >= datetime.utcnow() - timedelta(hours=hours),
    )

    if severity:
        query = query.where(AnomalyEvent.severity >= severity)

    query = query.order_by(desc(AnomalyEvent.detected_at)).limit(100)

    result = await db.execute(query)
    anomalies = result.scalars().all()

    # Calculate stats
    by_type = {}
    by_severity = {}
    for a in anomalies:
        by_type[a.anomaly_type] = by_type.get(a.anomaly_type, 0) + 1
        by_severity[str(a.severity)] = by_severity.get(str(a.severity), 0) + 1

    return AnomalyTimelineResponse(
        anomalies=[AnomalyEventResponse.model_validate(a) for a in anomalies],
        total=len(anomalies),
        by_type=by_type,
        by_severity=by_severity,
    )


async def _get_journey_stats(db: AsyncSession, group_id: int) -> Dict[str, Any]:
    """Get journey statistics."""
    total = await db.execute(
        select(func.count(MemberJourney.id)).where(
            MemberJourney.group_id == group_id
        )
    )
    total_count = total.scalar() or 0

    positive = await db.execute(
        select(func.count(MemberJourney.id)).where(
            MemberJourney.group_id == group_id,
            MemberJourney.trajectory == "positive",
        )
    )
    positive_count = positive.scalar() or 0

    negative = await db.execute(
        select(func.count(MemberJourney.id)).where(
            MemberJourney.group_id == group_id,
            MemberJourney.trajectory == "negative",
        )
    )
    negative_count = negative.scalar() or 0

    return {
        "total_tracked": total_count,
        "positive_trajectory": positive_count,
        "negative_trajectory": negative_count,
    }


async def _get_topic_landscape(db: AsyncSession, group_id: int) -> TopicLandscapeResponse:
    """Get topic landscape."""
    result = await db.execute(
        select(TopicCluster).where(TopicCluster.group_id == group_id)
    )
    topics = result.scalars().all()

    emerging = [t.cluster_id for t in topics if t.is_emerging]
    dying = [t.cluster_id for t in topics if t.is_dying]
    controversial = [t.cluster_id for t in topics if t.is_controversial]
    connectors = [t.cluster_id for t in topics if t.is_connector]

    return TopicLandscapeResponse(
        topics=[TopicClusterResponse.model_validate(t) for t in topics],
        emerging=emerging,
        dying=dying,
        controversial=controversial,
        connectors=connectors,
    )


async def _get_churn_panel(
    db: AsyncSession, group_id: int, min_risk: float = 0.3
) -> ChurnRiskPanelResponse:
    """Get churn risk panel."""
    result = await db.execute(
        select(ChurnPrediction).where(
            ChurnPrediction.group_id == group_id,
            ChurnPrediction.churn_risk >= min_risk,
        ).order_by(desc(ChurnPrediction.churn_risk))
    )
    predictions = result.scalars().all()

    at_risk = []
    by_risk_level = {"high": 0, "medium": 0, "low": 0}

    for p in predictions:
        at_risk.append({
            "user_id": p.user_id,
            "churn_risk": p.churn_risk,
            "days_inactive": p.days_inactive,
            "suggested_intervention": p.suggested_intervention,
        })

        if p.churn_risk >= 0.7:
            by_risk_level["high"] += 1
        elif p.churn_risk >= 0.5:
            by_risk_level["medium"] += 1
        else:
            by_risk_level["low"] += 1

    return ChurnRiskPanelResponse(
        at_risk_members=at_risk,
        total_at_risk=len(at_risk),
        by_risk_level=by_risk_level,
    )


async def _detect_cliques(nodes: List, edges: List) -> List[List[int]]:
    """Detect cliques in the conversation graph (simplified)."""
    # This is a simplified implementation
    # In production, use proper graph clustering algorithms
    cliques = []

    # Build adjacency dict
    adj = {}
    for n in nodes:
        adj[n.user_id] = set()

    for e in edges:
        if e.source_user_id in adj:
            adj[e.source_user_id].add(e.target_user_id)

    # Find small cliques (simplified)
    for user_id, neighbors in adj.items():
        for neighbor in neighbors:
            common = neighbors & adj.get(neighbor, set())
            if len(common) >= 2:
                clique = sorted([user_id, neighbor] + list(common))[:5]
                if clique not in cliques:
                    cliques.append(clique)

    return cliques[:10]  # Limit to 10 cliques


async def _find_bridges(nodes: List, edges: List) -> List[Dict[str, Any]]:
    """Find bridge members in the conversation graph."""
    bridges = []

    # Find members who connect different groups
    for n in nodes:
        if n.bridges_to and len(n.bridges_to) >= 2:
            bridges.append({
                "user_id": n.user_id,
                "bridges_to": n.bridges_to,
                "influence": n.influence_score,
            })

    return sorted(bridges, key=lambda x: len(x["bridges_to"]), reverse=True)[:10]
