-- Database initialization script for Sentiment Analysis Platform
-- Creates tables that mirror the SQLAlchemy models used by the backend

-- Drop tables if they exist (order matters because of foreign keys)
DROP TABLE IF EXISTS sentiment_results CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS user_report_preferences CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS report_schedule_frequency;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active VARCHAR(1) NOT NULL DEFAULT 'Y'
);

-- Tickets table
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    summary TEXT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    issue_type VARCHAR(100),
    parent_ticket_id VARCHAR(50),
    ultimate_sentiment VARCHAR(20),
    ultimate_confidence FLOAT,
    sentiment_trend VARCHAR(20),
    comment_count INTEGER DEFAULT 0
);

-- Sentiment results table
CREATE TABLE sentiment_results (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    field_type VARCHAR(20),
    comment_number INTEGER,
    comment_timestamp TIMESTAMP WITH TIME ZONE,
    author_id VARCHAR(100),
    CONSTRAINT fk_sentiment_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);

-- Entities table
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    text VARCHAR(100) NOT NULL,
    label VARCHAR(50) NOT NULL,
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    confidence JSONB,
    CONSTRAINT fk_entity_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);

-- Report schedule enum and preferences
CREATE TYPE report_schedule_frequency AS ENUM ('daily', 'weekly');

CREATE TABLE user_report_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    schedule_frequency report_schedule_frequency NOT NULL,
    delivery_time TIME NOT NULL DEFAULT '08:00',
    email VARCHAR(255) NOT NULL,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Indexes for tickets
CREATE INDEX idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_parent_ticket_id ON tickets(parent_ticket_id);
CREATE INDEX idx_tickets_ultimate_sentiment ON tickets(ultimate_sentiment);

-- Indexes for sentiment_results
CREATE INDEX idx_sentiment_results_ticket_id ON sentiment_results(ticket_id);
CREATE INDEX idx_sentiment_results_sentiment ON sentiment_results(sentiment);
CREATE INDEX idx_sentiment_results_created_at ON sentiment_results(created_at);
CREATE INDEX idx_sentiment_results_field_type ON sentiment_results(field_type);
CREATE INDEX idx_sentiment_results_comment_timestamp ON sentiment_results(comment_timestamp);

-- Indexes for entities
CREATE INDEX idx_entities_ticket_id ON entities(ticket_id);
CREATE INDEX idx_entities_label ON entities(label);
CREATE INDEX idx_entities_text ON entities(text);

-- Index for user report preferences
CREATE INDEX idx_user_report_preferences_user_id ON user_report_preferences(user_id);

-- Default admin user (password: "password")
INSERT INTO users (email, hashed_password, role, is_active)
VALUES (
    'admin@example.com',
    '$pbkdf2-sha256$29000$6x2D0Lr33tsb41xLifEeYw$QRzO4xhbxuU/OqX5BCnsOkFwIWcHWbWWSQnMhEw4oT8',
    'admin',
    'Y'
)
ON CONFLICT (email) DO NOTHING;

-- Refresh collation version to prevent Alpine warnings
ALTER DATABASE sentiment_db REFRESH COLLATION VERSION;

-- Summary output
SELECT 'Database initialized successfully!' AS status,
       (SELECT COUNT(*) FROM users) AS user_count,
       (SELECT COUNT(*) FROM tickets) AS ticket_count,
       (SELECT COUNT(*) FROM sentiment_results) AS sentiment_count,
        (SELECT COUNT(*) FROM entities) AS entity_count,
       (SELECT COUNT(*) FROM user_report_preferences) AS preference_count;
