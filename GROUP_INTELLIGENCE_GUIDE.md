# Group Intelligence Layer - Implementation Guide

## Overview

This document describes the implementation of the Group Intelligence Layer and Advanced Features for Nexus. These features represent a paradigm shift in how Telegram bot platforms approach community management - treating groups as living communities with their own culture, memory, governance, economy, and identity.

## Architecture

### Database Models (`shared/models_intelligence.py`)

The following model categories have been implemented:

#### 1. Group Intelligence Models
- `BehaviorPattern` - Known behavioral patterns for predictive moderation
- `MemberBehaviorLog` - Log of all member behaviors for analysis
- `PredictiveScore` - Risk scores and predictions for each member
- `ConversationNode` - Nodes in the social graph (members)
- `ConversationEdge` - Edges in the social graph (interactions)
- `AnomalyEvent` - Detected anomalies in group activity
- `MemberJourney` - Member onboarding journey tracking
- `TopicCluster` - Topic intelligence clusters
- `ChurnPrediction` - Member churn risk predictions

#### 2. Automation Models
- `AutomationRule` - Conditional automation rules
- `BehavioralTripwire` - Escalation ladders for behaviors
- `MemberTripwireState` - Member state against tripwires
- `TimeBasedRuleSet` - Different rules for different times
- `SmartCooldown` - Trust-score-adjusted cooldowns
- `AutomatedEvent` - Self-running community events

#### 3. Communication Models
- `BroadcastCampaign` - Rich announcement campaigns
- `DMCampaign` - Personalized DM campaigns
- `AnnouncementReaction` - Reaction tracking

#### 4. Personalization Models
- `MemberPreferences` - Member preference profiles
- `AdminPreferences` - Admin notification preferences
- `GroupTheme` - Custom group theming
- `CustomRankName` - Custom rank names for levels
- `CustomEconomyConfig` - Custom economy naming
- `WelcomeFlow` - Conditional welcome sequences

#### 5. Safety Architecture Models
- `CoordinatedAttack` - Detected coordinated attacks
- `HoneypotTrap` - Spam trap triggers
- `VerificationLevel` - Member verification levels
- `VerificationRequirement` - Requirements for actions
- `ShadowWatchSession` - Pre-moderation sessions
- `ShadowWatchMessage` - Messages in shadow watch

#### 6. Integration Models
- `WebhookConfig` - Webhook configurations
- `WebhookLog` - Webhook execution logs
- `EventSubscription` - Event stream subscriptions

#### 7. Unique Features Models
- `TimeCapsule` - Future message delivery
- `GroupSoundtrack` - Voice message soundtracks
- `LegacyMember` - Honored departed members
- `GroupOath` - Group oath system
- `OathAcceptance` - Oath acceptance records
- `LiveCollaborationSession` - Real-time admin collaboration
- `SeasonalMode` - Seasonal operating modes

### API Routes (`api/routers/intelligence.py`)

All intelligence endpoints are under `/api/v1/groups/{group_id}/`:

#### Intelligence Overview
- `GET /intelligence` - Full intelligence dashboard data
- `GET /members/{user_id}/intelligence` - Per-member intelligence

#### Predictive Moderation
- `GET /predictive-scores` - List risk scores
- `GET /behavior-patterns` - List known patterns

#### Conversation Graph
- `GET /conversation-graph` - Full graph for visualization

#### Anomaly Timeline
- `GET /anomalies` - List anomalies
- `POST /anomalies/{id}/resolve` - Resolve an anomaly

#### Member Journey
- `GET /journeys` - List member journeys
- `GET /journeys/{user_id}` - Specific journey

#### Topic Intelligence
- `GET /topics` - Topic landscape

#### Churn Prediction
- `GET /churn-predictions` - At-risk members

#### Automation
- `GET /automation-rules` - List rules
- `POST /automation-rules` - Create rule
- `GET /tripwires` - List tripwires
- `POST /tripwires` - Create tripwire
- `GET /time-rules` - List time-based rules
- `POST /time-rules` - Create time rule

#### Communication
- `GET /broadcasts` - List broadcasts
- `POST /broadcasts` - Create broadcast
- `GET /dm-campaigns` - List DM campaigns
- `POST /dm-campaigns` - Create campaign

#### Personalization
- `GET /members/{user_id}/preferences` - Get preferences
- `PATCH /members/{user_id}/preferences` - Update preferences
- `GET /theme` - Get group theme
- `PATCH /theme` - Update theme

#### Safety
- `GET /shadow-watch` - List shadow watch sessions
- `POST /shadow-watch` - Start shadow watch
- `DELETE /shadow-watch/{id}` - End shadow watch

#### Unique Features
- `GET /time-capsules` - List capsules
- `POST /time-capsules` - Create capsule
- `GET /legacy-members` - List legacy members
- `POST /legacy-members` - Create legacy member
- `GET /oath` - Get group oath
- `PUT /oath` - Update oath
- `GET /webhooks` - List webhooks
- `POST /webhooks` - Create webhook

### Bot Module (`bot/modules/group_intelligence/`)

The bot module handles real-time intelligence gathering:

#### Event Handlers
- `on_message` - Logs behavior, checks patterns, updates graph
- `on_new_member` - Creates journey, estimates account age
- `on_left_member` - Marks churn
- `on_reaction` - Tracks engagement

#### Commands
- `!risk [@user]` - Check member risk score
- `!predict [@user]` - View behavior predictions
- `!anomalies [hours]` - View recent anomalies
- `!influencers` - View top influencers
- `!churn_risk` - View at-risk members
- `!journey [@user]` - View member journey
- `!topics` - View trending topics
- `!graph` - Get graph visualization link

### Service Layer (`bot/services/group_intelligence_service.py`)

Core business logic for all intelligence features:

#### Methods
- `log_behavior()` - Log member behavior
- `update_predictive_score()` - Update risk scores
- `check_patterns()` - Match behaviors to patterns
- `record_interaction()` - Record graph interactions
- `calculate_influence_scores()` - Compute influence
- `create_anomaly()` - Create anomaly event
- `record_journey_milestone()` - Track journey progress
- `calculate_trajectory()` - Predict member trajectory
- `update_churn_risk()` - Calculate churn risk
- `create_automation_rule()` - Create automation
- `evaluate_conditions()` - Evaluate rule conditions
- `start_shadow_watch()` - Begin shadow watch
- `end_shadow_watch()` - End shadow watch
- `create_time_capsule()` - Create capsule

### Mini App Views (`mini-app/src/views/AdminDashboard/`)

#### GroupIntelligence.tsx
Full-featured intelligence dashboard with tabs:
- Overview - Stats cards, recent anomalies, trending topics
- Predictive - Risk score list with detailed breakdowns
- Anomalies - Anomaly timeline with resolution
- Social Graph - Top influencers display
- Topics - Topic landscape with trending indicators
- Churn Risk - At-risk member list with interventions

#### AutomationCenterEnhanced.tsx
Visual automation builder with:
- Automation Rules - Create and manage rules
- Tripwires - Escalation ladder management
- Time Rules - Time-based rule sets

## Key Features

### 1. Predictive Moderation
The system watches behavioral patterns and predicts who is likely to cause problems before they do. Pattern matching is based on known spam/raid/abuse sequences.

### 2. Conversation Graph
Builds a silent social graph showing:
- Who talks to whom
- Who influences whom
- Who bridges different cliques
- Who is isolated

### 3. Anomaly Timeline
Tracks unusual events:
- Message volume spikes
- Rapid join patterns
- Topic dominance
- Activity anomalies

### 4. Member Journey Mapping
Tracks the critical first 72 hours:
- Did they read rules?
- Did they introduce themselves?
- Did they respond to welcome?
- Are they on a positive trajectory?

### 5. Topic Intelligence
Analyzes discussion topics:
- Emerging topics
- Dying topics
- Controversial topics
- Connector topics (bridge different member groups)

### 6. Churn Prediction
Identifies at-risk members and suggests interventions:
- Send DM
- Invite to event
- Award special recognition

### 7. Conditional Automation Engine
Visual if-this-then-that builder with:
- Multiple conditions (AND/OR logic)
- Multiple actions
- Trigger types (message, join, reaction, etc.)
- Cooldown periods

### 8. Behavioral Tripwires
Escalation ladders for repeated behaviors:
- Level 1: Enhanced monitoring
- Level 2: Auto-mute
- Level 3: Notify admins
- Level 4: Auto-ban

### 9. Shadow Watch
Pre-moderation capability for suspicious members:
- Messages delayed by N seconds
- Admins see messages before they appear
- Can block before group sees

### 10. Time Capsules
Messages sealed until a future date:
- Milestone celebrations
- Predictions to be revealed
- Founder messages

## Database Migration

Run the migration:
```bash
alembic upgrade head
```

The migration creates all 45+ new tables for the intelligence features.

## Integration Checklist

For each feature, ensure:
- [x] Database model defined
- [x] Pydantic schema defined
- [x] API route created
- [x] Bot module handler implemented
- [x] Service layer method created
- [x] Mini App view created

## Next Steps

1. **Worker Tasks**: Create Celery tasks for:
   - Periodic influence score calculation
   - Churn prediction updates
   - Anomaly detection scans
   - Time capsule opening

2. **ML Integration**: Add ML models for:
   - Pattern learning from moderation actions
   - Sentiment analysis
   - Topic clustering
   - Trajectory prediction

3. **Real-time Updates**: Add WebSocket support for:
   - Live anomaly alerts
   - Real-time graph updates
   - Live collaboration sessions

4. **Testing**: Add comprehensive tests for:
   - Pattern matching accuracy
   - Risk score calculations
   - Automation rule evaluation
   - API endpoints

## Configuration

Enable intelligence features in group settings:
```python
# Enable predictive moderation
module_config.config["predictive_moderation_enabled"] = True

# Enable conversation graph
module_config.config["conversation_graph_enabled"] = True

# Enable anomaly detection
module_config.config["anomaly_detection_enabled"] = True

# Set analysis frequency (hours)
module_config.config["analysis_frequency_hours"] = 1
```

## Performance Considerations

- Behavior logs are high-volume; consider partitioning by date
- Conversation graph updates are batched
- Anomaly detection runs on schedule, not every message
- Churn predictions calculated daily
- Influence scores recalculated hourly

## Security

- All intelligence endpoints require admin authentication
- Shadow watch is admin-only
- Predictive scores are private to admins
- Member preferences are user-controlled
- Sensitive data is never exposed via API
