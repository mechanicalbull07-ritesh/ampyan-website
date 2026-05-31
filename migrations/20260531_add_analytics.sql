-- Optional manual PostgreSQL migration. Runtime startup also creates these
-- append-only tables and adds the visit columns safely through SQLAlchemy.
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS session_id VARCHAR(100);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS source VARCHAR(120);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS country VARCHAR(100);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS city VARCHAR(120);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS browser VARCHAR(80);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS os_name VARCHAR(80);
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT FALSE;
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS is_internal BOOLEAN DEFAULT FALSE;
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE website_visit ADD COLUMN IF NOT EXISTS traffic_type VARCHAR(30) DEFAULT 'web';

CREATE INDEX IF NOT EXISTS ix_website_visit_visit_time ON website_visit (visit_time);
CREATE INDEX IF NOT EXISTS ix_website_visit_session_id ON website_visit (session_id);
CREATE INDEX IF NOT EXISTS ix_website_visit_source ON website_visit (source);
CREATE INDEX IF NOT EXISTS ix_website_visit_country ON website_visit (country);
CREATE INDEX IF NOT EXISTS ix_website_visit_is_bot ON website_visit (is_bot);
CREATE INDEX IF NOT EXISTS ix_website_visit_is_internal ON website_visit (is_internal);

CREATE TABLE IF NOT EXISTS analytics_event (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(60) NOT NULL,
    session_id VARCHAR(100),
    source VARCHAR(120),
    path VARCHAR(500),
    referrer VARCHAR(500),
    country VARCHAR(100),
    city VARCHAR(120),
    device_type VARCHAR(30),
    browser VARCHAR(80),
    os_name VARCHAR(80),
    traffic_type VARCHAR(30) DEFAULT 'web',
    is_bot BOOLEAN DEFAULT FALSE,
    is_internal BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    user_id INTEGER REFERENCES "user" (id),
    ip_address VARCHAR(50),
    metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS ix_analytics_event_created_at ON analytics_event (created_at);
CREATE INDEX IF NOT EXISTS ix_analytics_event_event_type ON analytics_event (event_type);
CREATE INDEX IF NOT EXISTS ix_analytics_event_session_id ON analytics_event (session_id);
CREATE INDEX IF NOT EXISTS ix_analytics_event_source ON analytics_event (source);
CREATE INDEX IF NOT EXISTS ix_analytics_event_country ON analytics_event (country);
CREATE INDEX IF NOT EXISTS ix_analytics_event_is_bot ON analytics_event (is_bot);
CREATE INDEX IF NOT EXISTS ix_analytics_event_is_internal ON analytics_event (is_internal);

CREATE TABLE IF NOT EXISTS api_request_metric (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    path VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    traffic_type VARCHAR(30) DEFAULT 'api',
    is_bot BOOLEAN DEFAULT FALSE,
    is_internal BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_api_request_metric_created_at ON api_request_metric (created_at);
CREATE INDEX IF NOT EXISTS ix_api_request_metric_path ON api_request_metric (path);
CREATE INDEX IF NOT EXISTS ix_api_request_metric_status_code ON api_request_metric (status_code);
