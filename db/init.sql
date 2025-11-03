-- Database initialization script for Sentiment Analysis Platform

-- Create database (run this manually or adjust for your setup)
-- CREATE DATABASE sentiment_db;
-- \c sentiment_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active CHAR(1) NOT NULL DEFAULT 'Y'
);

-- Create tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    summary TEXT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sentiment_results table
CREATE TABLE IF NOT EXISTS sentiment_results (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);

-- Create entities table
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    text VARCHAR(100) NOT NULL,
    label VARCHAR(50) NOT NULL,
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sentiment_results_ticket_id ON sentiment_results(ticket_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_sentiment ON sentiment_results(sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_created_at ON sentiment_results(created_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_sentiment_created_at ON sentiment_results(sentiment, created_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_confidence ON sentiment_results(confidence);

CREATE INDEX IF NOT EXISTS idx_entities_ticket_id ON entities(ticket_id);
CREATE INDEX IF NOT EXISTS idx_entities_label ON entities(label);
CREATE INDEX IF NOT EXISTS idx_entities_text ON entities(text);
CREATE INDEX IF NOT EXISTS idx_entities_label_text ON entities(label, text);

CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_status_created_at ON tickets(status, created_at);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Insert default admin user (password: admin123)
-- Note: In production, hash the password properly
INSERT INTO users (email, hashed_password, role)
VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9.8XlI0w2e', 'admin')
ON CONFLICT (email) DO NOTHING;
