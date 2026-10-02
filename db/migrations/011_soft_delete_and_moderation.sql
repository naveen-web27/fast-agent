-- Soft delete + moderation. Rows are only flagged here; a later purge job hard-deletes them.

ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_reason TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- A deleted account must not block the same Google login/email/phone from signing up again.
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_auth_user_id_key;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_phone_key;
CREATE UNIQUE INDEX IF NOT EXISTS users_auth_user_id_active_idx ON users(auth_user_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_email_active_idx ON users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_phone_active_idx ON users(phone) WHERE deleted_at IS NULL AND phone IS NOT NULL;

-- Same for re-creating an expert profile after deleting the old one.
DROP INDEX IF EXISTS profiles_user_expert_unique_idx;
CREATE UNIQUE INDEX IF NOT EXISTS profiles_user_expert_unique_idx
    ON profiles(user_id)
    WHERE kind = 'expert' AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS admin_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL CHECK (target_type IN ('user', 'profile', 'request')),
    target_id UUID NOT NULL,
    target_label TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS admin_actions_created_idx ON admin_actions(created_at DESC);
