-- Direct contact for experts/companies, and work mode (on-site / remote / hybrid) for workers and jobs.
-- Run on dev first, then production, before deploying the matching backend.

-- Experts and companies: signed-in users can "View contact" (phone/WhatsApp/email) without waiting for a request
-- to be accepted. On for everyone by default; the owner can switch it off in Edit profile.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS show_contact BOOLEAN NOT NULL DEFAULT TRUE;

-- Who viewed an expert's/company's contact: one row per (profile, viewer). New rows share the viewer's daily
-- contact limit with worker_contact_views (Free 10, Pro 20, Enterprise 30); viewing the same profile again does not.
CREATE TABLE IF NOT EXISTS profile_contact_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    viewer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    view_count INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT profile_contact_views_once UNIQUE (profile_id, viewer_user_id)
);
CREATE INDEX IF NOT EXISTS profile_contact_views_viewer_idx ON profile_contact_views(viewer_user_id, first_viewed_at DESC);
CREATE INDEX IF NOT EXISTS profile_contact_views_profile_idx ON profile_contact_views(profile_id, last_viewed_at DESC);

ALTER TABLE profile_contact_views ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON profile_contact_views FROM anon, authenticated;
GRANT ALL ON profile_contact_views TO service_role;

-- Work mode and preferred work location for workers; work mode for job posts.
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS work_mode TEXT;
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS preferred_location TEXT;
ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS work_mode TEXT NOT NULL DEFAULT 'onsite';
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'worker_profiles_work_mode_check') THEN
        ALTER TABLE worker_profiles ADD CONSTRAINT worker_profiles_work_mode_check
            CHECK (work_mode IS NULL OR work_mode IN ('onsite', 'remote', 'hybrid'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'job_posts_work_mode_check') THEN
        ALTER TABLE job_posts ADD CONSTRAINT job_posts_work_mode_check
            CHECK (work_mode IN ('onsite', 'remote', 'hybrid'));
    END IF;
END $$;
