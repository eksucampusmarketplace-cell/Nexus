"""Add Group Intelligence and Advanced Features models

Revision ID: group_intelligence
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'group_intelligence'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Group Intelligence Tables
    
    # Behavior patterns
    op.create_table(
        'behavior_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('sequence', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('time_window_seconds', sa.Integer(), nullable=True, server_default='3600'),
        sa.Column('min_occurrences', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_risk_score', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('false_positive_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('auto_action', sa.String(30), nullable=True),
        sa.Column('action_threshold', sa.Integer(), nullable=True, server_default='80'),
        sa.Column('is_platform_pattern', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_learned', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pattern_id'),
    )
    op.create_index('ix_behavior_patterns_pattern_id', 'behavior_patterns', ['pattern_id'])
    
    # Member behavior logs
    op.create_table(
        'member_behavior_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('behavior_type', sa.String(50), nullable=False),
        sa.Column('behavior_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('matched_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_contribution', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_member_behavior_logs_user_id', 'member_behavior_logs', ['user_id'])
    op.create_index('ix_member_behavior_logs_group_id', 'member_behavior_logs', ['group_id'])
    op.create_index('ix_member_behavior_logs_behavior_type', 'member_behavior_logs', ['behavior_type'])
    op.create_index('ix_member_behavior_logs_timestamp', 'member_behavior_logs', ['timestamp'])
    
    # Predictive scores
    op.create_table(
        'predictive_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('spam_likelihood', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('raid_likelihood', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('abuse_likelihood', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('churn_likelihood', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('matched_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('behavioral_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('monitoring_level', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('shadow_watch', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('predicted_action', sa.String(50), nullable=True),
        sa.Column('prediction_confidence', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('first_flagged', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', name='uq_predictive_user_group'),
    )
    
    # Conversation nodes
    op.create_table(
        'conversation_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('influence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('centrality_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('trust_score_normalized', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('total_interactions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('messages_sent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('replies_received', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reactions_received', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('clique_membership', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('bridges_to', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_isolated', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Conversation edges
    op.create_table(
        'conversation_edges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('source_user_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('reply_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('mention_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reaction_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('forward_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('strength', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('reciprocity', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('avg_sentiment', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('last_interaction', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['source_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'source_user_id', 'target_user_id', name='uq_conversation_edge'),
    )
    
    # Anomaly events
    op.create_table(
        'anomaly_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anomaly_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('deviation_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('baseline_value', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('actual_value', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('involved_users', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('related_messages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('action_taken', sa.String(100), nullable=True),
        sa.Column('action_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('is_false_positive', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['action_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('anomaly_id'),
    )
    op.create_index('ix_anomaly_events_anomaly_id', 'anomaly_events', ['anomaly_id'])
    op.create_index('ix_anomaly_events_group_id', 'anomaly_events', ['group_id'])
    op.create_index('ix_anomaly_events_anomaly_type', 'anomaly_events', ['anomaly_type'])
    op.create_index('ix_anomaly_events_detected_at', 'anomaly_events', ['detected_at'])
    
    # Member journeys
    op.create_table(
        'member_journeys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('first_message_at', sa.DateTime(), nullable=True),
        sa.Column('first_reply_at', sa.DateTime(), nullable=True),
        sa.Column('first_reaction_at', sa.DateTime(), nullable=True),
        sa.Column('read_rules', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('read_rules_at', sa.DateTime(), nullable=True),
        sa.Column('introduced_self', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('introduced_at', sa.DateTime(), nullable=True),
        sa.Column('welcomed_by_bot', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('responded_to_welcome', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('first_72h_messages', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('first_72h_reactions_given', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('first_72h_reactions_received', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('first_72h_violations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('trajectory', sa.String(20), nullable=True, server_default='unknown'),
        sa.Column('trajectory_confidence', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('engagement_trend', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('became_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('churned_at', sa.DateTime(), nullable=True),
        sa.Column('banned_at', sa.DateTime(), nullable=True),
        sa.Column('last_analyzed', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Topic clusters
    op.create_table(
        'topic_clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('representative_messages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('unique_participants', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_sentiment', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('controversy_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('is_emerging', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_dying', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_controversial', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_connector', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('messages_24h', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('messages_7d', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('trend_direction', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('first_seen', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('last_seen', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_id'),
    )
    
    # Churn predictions
    op.create_table(
        'churn_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('churn_risk', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('engagement_decline_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('days_inactive', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('message_quality_trend', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('reaction_giving_trend', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('social_connection_loss', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('suggested_intervention', sa.String(100), nullable=True),
        sa.Column('intervention_priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('intervention_sent', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('intervention_at', sa.DateTime(), nullable=True),
        sa.Column('intervention_result', sa.String(50), nullable=True),
        sa.Column('predicted_churn_date', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Automation rules
    op.create_table(
        'automation_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('condition_logic', sa.String(10), nullable=True, server_default='and'),
        sa.Column('actions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('trigger_type', sa.String(30), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_triggers_per_day', sa.Integer(), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_id'),
    )
    
    # Behavioral tripwires
    op.create_table(
        'behavioral_tripwires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tripwire_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('trigger_behavior', sa.String(100), nullable=False),
        sa.Column('escalation_levels', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('window_seconds', sa.Integer(), nullable=True, server_default='86400'),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tripwire_id'),
    )
    
    # Member tripwire states
    op.create_table(
        'member_tripwire_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('tripwire_id', sa.String(100), nullable=False),
        sa.Column('trigger_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_level', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_triggered', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('window_start', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', 'tripwire_id', name='uq_member_tripwire'),
    )
    
    # Time-based rule sets
    op.create_table(
        'time_based_rule_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ruleset_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule_type', sa.String(20), nullable=False),
        sa.Column('days_of_week', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('start_time', sa.String(5), nullable=False),
        sa.Column('end_time', sa.String(5), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True, server_default='UTC'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('config_overrides', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ruleset_id'),
    )
    
    # Broadcast campaigns
    op.create_table(
        'broadcast_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_file_id', sa.String(500), nullable=True),
        sa.Column('media_type', sa.String(20), nullable=True),
        sa.Column('button_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('targeting', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('delivery_type', sa.String(20), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('is_ab_test', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('variant_a_content', sa.Text(), nullable=True),
        sa.Column('variant_b_content', sa.Text(), nullable=True),
        sa.Column('ab_split_ratio', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('sent_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reaction_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reply_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(20), nullable=True, server_default='draft'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id'),
    )
    
    # Shadow watch sessions
    op.create_table(
        'shadow_watch_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('started_by', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('delay_seconds', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('notify_channel_id', sa.BigInteger(), nullable=True),
        sa.Column('messages_watched', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('messages_blocked', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['started_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Time capsules
    op.create_table(
        'time_capsules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capsule_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('media_file_id', sa.String(500), nullable=True),
        sa.Column('open_at', sa.DateTime(), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('capsule_type', sa.String(20), nullable=True, server_default='message'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('capsule_id'),
    )
    
    # Group oaths
    op.create_table(
        'group_oaths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('oath_text', sa.Text(), nullable=False),
        sa.Column('confirmation_phrase', sa.String(100), nullable=False),
        sa.Column('require_on_join', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_group_oath_group_id', 'group_oaths', ['group_id'])
    
    # Oath acceptances
    op.create_table(
        'oath_acceptances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', name='uq_oath_user_group'),
    )
    
    # Member preferences
    op.create_table(
        'member_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('digest_delivery', sa.String(20), nullable=True, server_default='group'),
        sa.Column('dm_notifications', sa.String(20), nullable=True, server_default='mentions'),
        sa.Column('show_on_leaderboard', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('show_on_member_map', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('birthday', sa.Date(), nullable=True),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True, server_default='UTC'),
        sa.Column('language', sa.String(10), nullable=True, server_default='en'),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', name='uq_member_prefs'),
    )
    
    # Group themes
    op.create_table(
        'group_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('primary_color', sa.String(7), nullable=True, server_default='#3B82F6'),
        sa.Column('secondary_color', sa.String(7), nullable=True, server_default='#1E40AF'),
        sa.Column('accent_color', sa.String(7), nullable=True, server_default='#10B981'),
        sa.Column('background_color', sa.String(7), nullable=True, server_default='#0F172A'),
        sa.Column('text_color', sa.String(7), nullable=True, server_default='#F8FAFC'),
        sa.Column('card_style', sa.String(20), nullable=True, server_default='rounded'),
        sa.Column('welcome_card_template', sa.String(50), nullable=True),
        sa.Column('profile_card_template', sa.String(50), nullable=True),
        sa.Column('logo_file_id', sa.String(500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_group_theme_group_id', 'group_themes', ['group_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('group_themes')
    op.drop_table('member_preferences')
    op.drop_table('oath_acceptances')
    op.drop_table('group_oaths')
    op.drop_table('time_capsules')
    op.drop_table('shadow_watch_sessions')
    op.drop_table('broadcast_campaigns')
    op.drop_table('time_based_rule_sets')
    op.drop_table('member_tripwire_states')
    op.drop_table('behavioral_tripwires')
    op.drop_table('automation_rules')
    op.drop_table('churn_predictions')
    op.drop_table('topic_clusters')
    op.drop_table('member_journeys')
    op.drop_table('anomaly_events')
    op.drop_table('conversation_edges')
    op.drop_table('conversation_nodes')
    op.drop_table('predictive_scores')
    op.drop_table('member_behavior_logs')
    op.drop_table('behavior_patterns')
