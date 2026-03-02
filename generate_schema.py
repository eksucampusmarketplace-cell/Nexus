#!/usr/bin/env python3
"""Generate complete Nexus database schema SQL file."""

SCHEMA = """
-- Nexus Telegram Bot Platform - Complete Database Schema
-- PostgreSQL 14+
-- Generated from SQLAlchemy models and Alembic migrations

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(32),
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64),
    language_code VARCHAR(10),
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_users_telegram_id ON users (telegram_id);
CREATE INDEX ix_users_username ON users (username);

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    username VARCHAR(32),
    member_count INTEGER DEFAULT 0,
    language VARCHAR(10) DEFAULT 'en',
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_premium BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'UTC'
);

CREATE INDEX ix_groups_telegram_id ON groups (telegram_id);
CREATE INDEX ix_groups_username ON groups (username);

CREATE TABLE bot_instances (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    bot_telegram_id BIGINT NOT NULL,
    bot_username VARCHAR(32) NOT NULL,
    bot_name VARCHAR(64) NOT NULL,
    group_id INTEGER UNIQUE REFERENCES groups(id),
    registered_by INTEGER REFERENCES users(id),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    webhook_url VARCHAR(500)
);

CREATE INDEX ix_bot_instances_token_hash ON bot_instances (token_hash);

CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    trust_score INTEGER DEFAULT 50,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    streak_days INTEGER DEFAULT 0,
    last_streak_date DATE,
    warn_count INTEGER DEFAULT 0,
    mute_count INTEGER DEFAULT 0,
    ban_count INTEGER DEFAULT 0,
    is_muted BOOLEAN DEFAULT FALSE,
    mute_until TIMESTAMP,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_until TIMESTAMP,
    is_approved BOOLEAN DEFAULT FALSE,
    is_whitelisted BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'member',
    custom_title VARCHAR(64),
    CONSTRAINT uq_user_group UNIQUE (user_id, group_id)
);

CREATE INDEX ix_members_user_id ON members (user_id);
CREATE INDEX ix_members_group_id ON members (group_id);

-- ============================================================
-- BADGES & PROFILES
-- ============================================================

CREATE TABLE badge_definitions (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(50) NOT NULL,
    category VARCHAR(30) NOT NULL,
    auto_award_condition JSONB
);

CREATE INDEX ix_badge_definitions_slug ON badge_definitions (slug);

CREATE TABLE member_badges (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    badge_slug VARCHAR(50) NOT NULL REFERENCES badge_definitions(slug),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX ix_member_badges_member_id ON member_badges (member_id);

CREATE TABLE member_profiles (
    id SERIAL PRIMARY KEY,
    member_id INTEGER UNIQUE REFERENCES members(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    bio TEXT,
    birthday DATE,
    social_links JSONB,
    profile_theme VARCHAR(50) DEFAULT 'default',
    is_public BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_profile_member UNIQUE (member_id)
);

-- ============================================================
-- MODERATION
-- ============================================================

CREATE TABLE mod_actions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    target_user_id INTEGER NOT NULL REFERENCES users(id),
    actor_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(30) NOT NULL,
    reason TEXT,
    duration_seconds INTEGER,
    silent BOOLEAN DEFAULT FALSE,
    ai_inferred BOOLEAN DEFAULT FALSE,
    message_id BIGINT,
    message_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    reversed_at TIMESTAMP,
    reversed_by INTEGER REFERENCES users(id)
);

CREATE INDEX ix_mod_actions_group_id ON mod_actions (group_id);
CREATE INDEX ix_mod_actions_target_user_id ON mod_actions (target_user_id);
CREATE INDEX ix_mod_actions_action_type ON mod_actions (action_type);

CREATE TABLE warnings (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    issued_by INTEGER NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX ix_warnings_group_id ON warnings (group_id);
CREATE INDEX ix_warnings_user_id ON warnings (user_id);

-- ============================================================
-- FEDERATIONS (CROSS-GROUP BANS)
-- ============================================================

CREATE TABLE federations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE
);

CREATE TABLE federation_admins (
    id SERIAL PRIMARY KEY,
    federation_id UUID NOT NULL REFERENCES federations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    added_by INTEGER NOT NULL REFERENCES users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_federation_admins_federation_id ON federation_admins (federation_id);

CREATE TABLE federation_members (
    id SERIAL PRIMARY KEY,
    federation_id UUID NOT NULL REFERENCES federations(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_by INTEGER NOT NULL REFERENCES users(id)
);

CREATE INDEX ix_federation_members_federation_id ON federation_members (federation_id);

CREATE TABLE federation_bans (
    id SERIAL PRIMARY KEY,
    federation_id UUID NOT NULL REFERENCES federations(id),
    target_user_id INTEGER NOT NULL REFERENCES users(id),
    banned_by INTEGER NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX ix_federation_bans_federation_id ON federation_bans (federation_id);

-- ============================================================
-- CONTENT MANAGEMENT
-- ============================================================

CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    keyword VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    media_file_id VARCHAR(500),
    media_type VARCHAR(20),
    has_buttons BOOLEAN DEFAULT FALSE,
    button_data JSONB,
    is_private BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_notes_group_id ON notes (group_id);
CREATE INDEX ix_notes_keyword ON notes (keyword);

CREATE TABLE filters (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    trigger VARCHAR(200) NOT NULL,
    match_type VARCHAR(20) DEFAULT 'contains',
    response_type VARCHAR(20) DEFAULT 'text',
    response_content TEXT NOT NULL,
    response_file_id VARCHAR(500),
    action VARCHAR(20),
    delete_trigger BOOLEAN DEFAULT FALSE,
    admin_only BOOLEAN DEFAULT FALSE,
    case_sensitive BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_filters_group_id ON filters (group_id);

CREATE TABLE locks (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    lock_type VARCHAR(50) NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    mode VARCHAR(20) DEFAULT 'delete',
    mode_duration INTEGER,
    schedule_enabled BOOLEAN DEFAULT FALSE,
    schedule_windows JSONB,
    allowlist JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_locks_group_id ON locks (group_id);
CREATE INDEX ix_locks_lock_type ON locks (lock_type);

CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE NOT NULL REFERENCES groups(id),
    content TEXT NOT NULL,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- GREETINGS & MESSAGING
-- ============================================================

CREATE TABLE greetings (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    greeting_type VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    media_file_id VARCHAR(500),
    media_type VARCHAR(20),
    has_buttons BOOLEAN DEFAULT FALSE,
    button_data JSONB,
    delete_previous BOOLEAN DEFAULT FALSE,
    delete_after_seconds INTEGER,
    send_as_dm BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_greetings_group_id ON greetings (group_id);
CREATE INDEX ix_greetings_greeting_type ON greetings (greeting_type);

CREATE TABLE captcha_settings (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE NOT NULL REFERENCES groups(id),
    captcha_type VARCHAR(20) DEFAULT 'button',
    timeout_seconds INTEGER DEFAULT 90,
    action_on_fail VARCHAR(20) DEFAULT 'kick',
    mute_on_join BOOLEAN DEFAULT TRUE,
    custom_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scheduled_messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    content TEXT NOT NULL,
    media_file_id VARCHAR(500),
    media_type VARCHAR(20),
    has_buttons BOOLEAN DEFAULT FALSE,
    button_data JSONB,
    schedule_type VARCHAR(20) DEFAULT 'once',
    run_at TIMESTAMP,
    cron_expression VARCHAR(100),
    days_of_week JSONB,
    time_slot VARCHAR(5),
    end_date DATE,
    max_runs INTEGER,
    run_count INTEGER DEFAULT 0,
    self_destruct_after INTEGER,
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_scheduled_messages_group_id ON scheduled_messages (group_id);

-- ============================================================
-- MODULE CONFIGURATION
-- ============================================================

CREATE TABLE module_configs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    module_name VARCHAR(50) NOT NULL,
    config JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id),
    CONSTRAINT uq_group_module UNIQUE (group_id, module_name)
);

CREATE INDEX ix_module_configs_group_id ON module_configs (group_id);
CREATE INDEX ix_module_configs_module_name ON module_configs (module_name);

-- ============================================================
-- ECONOMY SYSTEM
-- ============================================================

CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    member_id INTEGER UNIQUE REFERENCES members(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    balance BIGINT DEFAULT 0,
    total_earned BIGINT DEFAULT 0,
    total_spent BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wallet_member UNIQUE (member_id)
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    from_wallet_id INTEGER REFERENCES wallets(id),
    to_wallet_id INTEGER REFERENCES wallets(id),
    amount BIGINT NOT NULL,
    reason TEXT,
    transaction_type VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE economy_config (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE REFERENCES groups(id),
    currency_name VARCHAR(30) DEFAULT 'coins',
    currency_emoji VARCHAR(5) DEFAULT '🪙',
    earn_per_message INTEGER DEFAULT 1,
    earn_per_reaction INTEGER DEFAULT 2,
    daily_bonus INTEGER DEFAULT 100,
    xp_to_coin_enabled BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- REPUTATION SYSTEM
-- ============================================================

CREATE TABLE reputation (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    score INTEGER DEFAULT 0,
    last_given_at TIMESTAMP,
    CONSTRAINT uq_rep_group_user UNIQUE (group_id, user_id)
);

CREATE TABLE reputation_logs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    from_user INTEGER NOT NULL REFERENCES users(id),
    to_user INTEGER NOT NULL REFERENCES users(id),
    delta INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- GAMES
-- ============================================================

CREATE TABLE game_sessions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    game_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE INDEX ix_game_sessions_group_id ON game_sessions (group_id);

CREATE TABLE game_scores (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    game_type VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- POLLS
-- ============================================================

CREATE TABLE polls (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    question VARCHAR(300) NOT NULL,
    options JSONB NOT NULL,
    is_anonymous BOOLEAN DEFAULT TRUE,
    allows_multiple BOOLEAN DEFAULT FALSE,
    closes_at TIMESTAMP,
    is_closed BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    message_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE poll_votes (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES polls(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    option_indices JSONB NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- API & AUTH
-- ============================================================

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    label VARCHAR(100),
    scopes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX ix_api_keys_key_hash ON api_keys (key_hash);
CREATE INDEX ix_api_keys_group_id ON api_keys (group_id);

-- ============================================================
-- UTILITY TABLES
-- ============================================================

CREATE TABLE log_channels (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    channel_id BIGINT NOT NULL,
    log_types JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    added_by INTEGER REFERENCES users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE antiflood_config (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE REFERENCES groups(id),
    is_enabled BOOLEAN DEFAULT TRUE,
    message_limit INTEGER DEFAULT 5,
    window_seconds INTEGER DEFAULT 5,
    action VARCHAR(20) DEFAULT 'mute',
    action_duration INTEGER DEFAULT 300,
    media_flood_enabled BOOLEAN DEFAULT TRUE,
    media_limit INTEGER DEFAULT 3
);

CREATE TABLE antiraid_config (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE REFERENCES groups(id),
    is_enabled BOOLEAN DEFAULT TRUE,
    join_threshold INTEGER DEFAULT 10,
    window_seconds INTEGER DEFAULT 60,
    action VARCHAR(20) DEFAULT 'lock',
    auto_unlock_after INTEGER DEFAULT 3600,
    notify_admins BOOLEAN DEFAULT TRUE
);

CREATE TABLE banned_words (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    word VARCHAR(200) NOT NULL,
    list_number INTEGER DEFAULT 1,
    is_regex BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE banned_word_list_configs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    list_number INTEGER NOT NULL,
    action VARCHAR(20) DEFAULT 'delete',
    action_duration INTEGER,
    delete_message BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_group_list UNIQUE (group_id, list_number)
);

CREATE TABLE approvals (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    approved_by INTEGER NOT NULL REFERENCES users(id),
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE force_subscribe (
    id SERIAL PRIMARY KEY,
    group_id INTEGER UNIQUE REFERENCES groups(id),
    channel_id BIGINT NOT NULL,
    channel_username VARCHAR(32),
    action_on_fail VARCHAR(20) DEFAULT 'restrict',
    message TEXT,
    is_enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE group_events (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    starts_at TIMESTAMP NOT NULL,
    ends_at TIMESTAMP,
    location VARCHAR(200),
    created_by INTEGER REFERENCES users(id),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT,
    status VARCHAR(20) DEFAULT 'upcoming'
);

CREATE TABLE event_rsvps (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES group_events(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(10) NOT NULL,
    rsvp_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_milestones (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    happened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auto_generated BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

CREATE TABLE topic_configs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    topic_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    enabled_modules JSONB,
    custom_welcome TEXT,
    is_locked BOOLEAN DEFAULT FALSE
);

CREATE TABLE cas_cache (
    user_id BIGINT PRIMARY KEY,
    is_banned BOOLEAN NOT NULL,
    ban_reason TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE export_jobs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    requested_by INTEGER NOT NULL REFERENCES users(id),
    modules JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================
-- MESSAGE GRAVEYARD
-- ============================================================

CREATE TABLE deleted_messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,
    content_type VARCHAR(50) DEFAULT 'text',
    media_file_id VARCHAR(255),
    media_group_id VARCHAR(255),
    deletion_reason VARCHAR(50) NOT NULL,
    deleted_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    can_restore BOOLEAN DEFAULT TRUE,
    restored_at TIMESTAMP,
    restored_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    restored_message_id BIGINT,
    trigger_word VARCHAR(255),
    lock_type VARCHAR(50),
    ai_confidence INTEGER,
    metadata JSONB
);

CREATE INDEX ix_deleted_messages_group_id ON deleted_messages (group_id);
CREATE INDEX ix_deleted_messages_message_id ON deleted_messages (message_id);
CREATE INDEX ix_deleted_messages_user_id ON deleted_messages (user_id);
CREATE INDEX ix_deleted_messages_deletion_reason ON deleted_messages (deletion_reason);
CREATE INDEX ix_deleted_messages_deleted_at ON deleted_messages (deleted_at);

-- ============================================================
-- END OF CORE SCHEMA
-- ============================================================
"""

with open('nexus_schema.sql', 'w') as f:
    f.write(SCHEMA.strip())

print("Schema generated successfully!")
print("File: nexus_schema.sql")
