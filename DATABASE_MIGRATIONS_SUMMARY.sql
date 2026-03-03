-- ============================================================
-- NEXUS DATABASE MIGRATIONS SUMMARY
-- ============================================================
-- This file documents all database migrations and their SQL statements.
-- For Alembic migrations, see: alembic/versions/
-- ============================================================

-- ============================================================
-- MIGRATION 001: Initial Schema
-- File: alembic/versions/001_initial.py
-- Description: Core tables for Nexus platform
-- ============================================================

-- Users table (global user model)
CREATE TABLE IF NOT EXISTS users (
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

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
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

-- Bot instances table
CREATE TABLE IF NOT EXISTS bot_instances (
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

-- Members table (user-group relationship)
CREATE TABLE IF NOT EXISTS members (
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

-- Indexes
CREATE INDEX ix_users_telegram_id ON users (telegram_id);
CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_groups_telegram_id ON groups (telegram_id);
CREATE INDEX ix_groups_username ON groups (username);
CREATE INDEX ix_bot_instances_token_hash ON bot_instances (token_hash);
CREATE INDEX ix_members_user_id ON members (user_id);
CREATE INDEX ix_members_group_id ON members (group_id);


-- ============================================================
-- MIGRATION 002: Advanced Analytics
-- File: alembic/versions/002_advanced_analytics.py
-- Description: Additional tables for analytics, notes, filters, locks, etc.
-- ============================================================

-- Note: See 002_advanced_analytics.py for complete SQL
-- Tables added: notes, filters, locks, rules, greetings, scheduled_messages,
--                warning_settings, captcha_configs, warnings, api_keys, 
--                economy_accounts, economy_transactions, games, badges, 
--                member_badges, auto_responses, federations, federation_bans


-- ============================================================
-- MIGRATION 003: Message Graveyard
-- File: alembic/versions/003_message_graveyard.py
-- Description: Message storage and retrieval system
-- ============================================================

-- Note: See 003_message_graveyard.py for complete SQL
-- Tables added: message_graveyard, graveyard_messages


-- ============================================================
-- MIGRATION 004: User Sessions (NEW)
-- File: alembic/versions/004_user_sessions.py
-- Description: Session management for Mini App authentication
-- ============================================================

-- User sessions table - tracks active login sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add last_init_data column to users for re-authentication
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_init_data TEXT;

-- Indexes for user_sessions
CREATE INDEX ix_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX ix_user_sessions_session_token ON user_sessions (session_token);
CREATE INDEX ix_user_sessions_expires_at ON user_sessions (expires_at);


-- ============================================================
-- COMPLETE TABLE LIST
-- ============================================================
-- The following tables exist in the Nexus database:
--
-- Core:
--   - users
--   - groups
--   - bot_instances
--   - members
--
-- Analytics & Content:
--   - notes
--   - filters
--   - locks
--   - rules
--   - greetings
--   - scheduled_messages
--   - warning_settings
--   - captcha_configs
--   - warnings
--   - api_keys
--
-- Economy & Gamification:
--   - economy_accounts
--   - economy_transactions
--   - games
--   - badges
--   - member_badges
--
-- Automation:
--   - auto_responses
--
-- Federations:
--   - federations
--   - federation_bans
--
-- Message Storage:
--   - message_graveyard
--   - graveyard_messages
--
-- Sessions (NEW):
--   - user_sessions
--
-- Group Intelligence:
--   - See 001_group_intelligence.py for intelligence-related tables
--
-- ============================================================
