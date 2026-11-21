-- Local workforce hub: workers (service partners), employer-verified work history, hires, reviews and job posts.
-- Run on dev first, then production, before deploying the matching backend.
ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'worker';

-- The admin audit log also records company listings/claims (migration 023) and workers.
ALTER TABLE admin_actions DROP CONSTRAINT IF EXISTS admin_actions_target_type_check;
ALTER TABLE admin_actions ADD CONSTRAINT admin_actions_target_type_check
    CHECK (target_type IN ('user', 'profile', 'request', 'organization', 'worker'));

CREATE TABLE IF NOT EXISTS worker_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    headline TEXT NOT NULL,
    bio TEXT,
    city TEXT,
    area TEXT,
    languages TEXT[] NOT NULL DEFAULT '{}',
    years_experience SMALLINT CHECK (years_experience BETWEEN 0 AND 70),
    skills TEXT[] NOT NULL DEFAULT '{}',
    rate_amount INTEGER CHECK (rate_amount >= 0),
    rate_unit TEXT CHECK (rate_unit IN ('hour', 'day', 'month')),
    availability TEXT NOT NULL DEFAULT 'available' CHECK (availability IN ('available', 'busy', 'offline')),
    busy_until DATE,
    availability_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contact_phone TEXT,
    avatar_url TEXT,
    claim_status TEXT NOT NULL DEFAULT 'claimed' CHECK (claim_status IN ('unclaimed', 'claimed')),
    claim_code_hash TEXT,
    claim_code_expires_at TIMESTAMPTZ,
    claimed_at TIMESTAMPTZ,
    adult_confirmed_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    average_rating NUMERIC(2, 1) NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    blocked_at TIMESTAMPTZ,
    blocked_reason TEXT,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS worker_profiles_user_active_idx ON worker_profiles(user_id) WHERE user_id IS NOT NULL AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS worker_profiles_claim_code_idx ON worker_profiles(claim_code_hash) WHERE claim_code_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS worker_profiles_search_idx ON worker_profiles(city, availability) WHERE deleted_at IS NULL AND blocked_at IS NULL;

CREATE TABLE IF NOT EXISTS job_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poster_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    skill TEXT NOT NULL,
    city TEXT NOT NULL,
    area TEXT,
    openings SMALLINT NOT NULL DEFAULT 1 CHECK (openings BETWEEN 1 AND 500),
    pay TEXT,
    starts_on DATE,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS job_posts_open_idx ON job_posts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS job_posts_poster_idx ON job_posts(poster_user_id);

CREATE TABLE IF NOT EXISTS worker_hires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    employer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    job_id UUID REFERENCES job_posts(id) ON DELETE SET NULL,
    initiated_by TEXT NOT NULL CHECK (initiated_by IN ('employer', 'worker')),
    title TEXT NOT NULL,
    details TEXT,
    location TEXT,
    start_date DATE,
    pay_offer TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'cancelled', 'completed')),
    responded_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS worker_hires_worker_idx ON worker_hires(worker_id, created_at DESC);
CREATE INDEX IF NOT EXISTS worker_hires_employer_idx ON worker_hires(employer_user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS worker_hires_one_open_request_idx ON worker_hires(worker_id, employer_user_id) WHERE status = 'pending' AND job_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS worker_hires_one_application_idx ON worker_hires(worker_id, job_id) WHERE job_id IS NOT NULL AND status IN ('pending', 'accepted');

CREATE TABLE IF NOT EXISTS worker_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    employer_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    skills TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'self' CHECK (status IN ('self', 'pending', 'verified', 'declined')),
    added_by TEXT NOT NULL DEFAULT 'worker' CHECK (added_by IN ('worker', 'employer')),
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMPTZ,
    hire_id UUID REFERENCES worker_hires(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS worker_experiences_worker_idx ON worker_experiences(worker_id);
CREATE INDEX IF NOT EXISTS worker_experiences_pending_idx ON worker_experiences(organization_id) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS worker_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hire_id UUID NOT NULL UNIQUE REFERENCES worker_hires(id) ON DELETE CASCADE,
    worker_id UUID NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS worker_reviews_worker_idx ON worker_reviews(worker_id, created_at DESC);

ALTER TABLE worker_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_hires ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_experiences ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON worker_profiles, job_posts, worker_hires, worker_experiences, worker_reviews FROM anon, authenticated;
GRANT ALL ON worker_profiles, job_posts, worker_hires, worker_experiences, worker_reviews TO service_role;
