-- External videos only. Browser writes are not allowed; the API enforces ownership and quotas.
CREATE TABLE IF NOT EXISTS video_showcases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    source_url VARCHAR(500) NOT NULL,
    title VARCHAR(120) NOT NULL CHECK (char_length(btrim(title)) BETWEEN 2 AND 120),
    description VARCHAR(600) NOT NULL CHECK (char_length(btrim(description)) BETWEEN 2 AND 600),
    cover_url VARCHAR(1000) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT video_showcases_profile_source_key UNIQUE (profile_id, source_url)
);
CREATE INDEX IF NOT EXISTS ix_video_showcases_profile_id ON video_showcases(profile_id);
CREATE INDEX IF NOT EXISTS video_showcases_created_idx ON video_showcases(created_at, id);
ALTER TABLE video_showcases ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON video_showcases FROM anon, authenticated;
GRANT ALL ON video_showcases TO service_role;
