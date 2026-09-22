-- Lets a customer bookmark experts/companies to compare later ("Saved" tab).
CREATE TABLE IF NOT EXISTS saved_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, profile_id)
);
CREATE INDEX IF NOT EXISTS saved_profiles_user_idx ON saved_profiles(user_id, created_at DESC);
