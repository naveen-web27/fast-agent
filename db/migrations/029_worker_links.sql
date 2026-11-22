-- Personal worker links: workers without Google/email open a private link to manage their availability and
-- hire requests. Only a SHA-256 hash of the link key is stored; resetting the link makes the old one stop working.
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS access_key_hash TEXT;
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS access_key_created_at TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS worker_profiles_access_key_idx ON worker_profiles(access_key_hash) WHERE access_key_hash IS NOT NULL;
