-- Additive, nullable rich-news storage. No existing rows are rewritten.
ALTER TABLE news
ADD COLUMN content_blocks JSONB NULL;

-- Operational rollback intentionally leaves this column in place.
-- Destructive downgrade (manual approval only):
-- ALTER TABLE news DROP COLUMN content_blocks;
