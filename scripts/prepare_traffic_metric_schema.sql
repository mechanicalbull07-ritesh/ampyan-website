-- Additive Phase 1 schema. Apply only after reviewing the target database.
-- No visitor-level data is stored in this table.
BEGIN;
CREATE TABLE IF NOT EXISTS traffic_metric (
    hour_start_utc TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    quality VARCHAR(20) NOT NULL,
    count BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT pk_traffic_metric PRIMARY KEY (hour_start_utc, quality),
    CONSTRAINT ck_traffic_metric_quality CHECK (quality IN ('human_like', 'likely_bot', 'unknown')),
    CONSTRAINT ck_traffic_metric_count_nonnegative CHECK (count >= 0)
);
COMMIT;
