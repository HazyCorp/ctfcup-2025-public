CREATE TABLE IF NOT EXISTS feeds (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    is_public BOOLEAN NOT NULL DEFAULT false,
    api_key TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS iocs (
    id UUID PRIMARY KEY,
    feed_id UUID NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feeds_public ON feeds(is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_feeds_api_key ON feeds(api_key) WHERE api_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_iocs_feed_id ON iocs(feed_id);
CREATE INDEX IF NOT EXISTS idx_iocs_type ON iocs(type);
CREATE INDEX IF NOT EXISTS idx_iocs_value ON iocs(value);

CREATE OR REPLACE FUNCTION hash()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.api_key IS NOT NULL THEN
        NEW.api_key := md5(NEW.api_key::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_hash
    BEFORE INSERT ON feeds
    FOR EACH ROW
    EXECUTE FUNCTION hash();