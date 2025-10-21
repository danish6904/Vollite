CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Analysis sessions tracking
CREATE TABLE analysis_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_status VARCHAR(20) DEFAULT 'pending',
    volatility_profile VARCHAR(50),
    analysis_duration INTEGER
);

-- Analysis results storage
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES analysis_sessions(id),
    summary TEXT,
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    key_findings JSONB,
    process_data JSONB,
    network_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES analysis_sessions(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(10) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    threat_indicators JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Threat intelligence cache
CREATE TABLE threat_intelligence (
    id SERIAL PRIMARY KEY,
    indicator_type VARCHAR(20) NOT NULL,
    indicator_value VARCHAR(255) NOT NULL,
    threat_type VARCHAR(50),
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
    source VARCHAR(50) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator_type, indicator_value, source)
);