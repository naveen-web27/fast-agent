-- Per-identity plans (Pro = expert profile, Enterprise = company), booking, team seats,
-- request assignment, rich profiles and service catalogue.

-- Plans now live on the identity that paid, not on the person.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subscription_tier subscription_tier NOT NULL DEFAULT 'free';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL;

-- Rich profile.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS intro_video_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS portfolio_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS profile_offerings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    price_min_inr INTEGER CHECK (price_min_inr >= 0),
    price_max_inr INTEGER CHECK (price_max_inr >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (price_max_inr IS NULL OR price_min_inr IS NULL OR price_max_inr >= price_min_inr)
);
CREATE INDEX IF NOT EXISTS profile_offerings_profile_idx ON profile_offerings(profile_id);

-- Weekly availability (Asia/Kolkata local time) and bookings.
CREATE TABLE IF NOT EXISTS availability_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    CHECK (end_time > start_time)
);
CREATE INDEX IF NOT EXISTS availability_slots_profile_idx ON availability_slots(profile_id);

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booked_by UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE UNIQUE INDEX IF NOT EXISTS appointments_profile_slot_active_idx
    ON appointments(profile_id, starts_at)
    WHERE status IN ('proposed', 'confirmed');

-- Team seats and request assignment.
CREATE TABLE IF NOT EXISTS organization_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS organization_invites_pending_idx
    ON organization_invites(organization_id, lower(email))
    WHERE accepted_at IS NULL;

ALTER TABLE request_participants ADD COLUMN IF NOT EXISTS assigned_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
