-- RightConnect initial PostgreSQL schema.
-- Run this in the Supabase SQL Editor or against a Neon database.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('customer', 'expert', 'company_admin', 'platform_admin');
CREATE TYPE profile_kind AS ENUM ('expert', 'company');
CREATE TYPE request_status AS ENUM ('submitted', 'accepted', 'meeting_booked', 'provider_invited', 'completed', 'cancelled');
CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'rejected');
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    role user_role NOT NULL DEFAULT 'customer',
    interests TEXT[] NOT NULL DEFAULT '{}',
    looking_for_help BOOLEAN NOT NULL DEFAULT TRUE,
    need_fulfilled_at TIMESTAMPTZ,
    bio TEXT,
    city TEXT,
    avatar_url TEXT,
    subscription_tier subscription_tier NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    blocked_at TIMESTAMPTZ,
    blocked_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX users_auth_user_id_active_idx ON users(auth_user_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX users_email_active_idx ON users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX users_phone_active_idx ON users(phone) WHERE deleted_at IS NULL AND phone IS NOT NULL;

CREATE TABLE payments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL CHECK (plan IN ('pro', 'enterprise')),
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 100),
    razorpay_link_id TEXT UNIQUE,
    razorpay_order_id TEXT UNIQUE,
    razorpay_payment_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'refunded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at TIMESTAMPTZ,
    access_expires_at TIMESTAMPTZ
);
CREATE INDEX payments_user_id_idx ON payments(user_id);

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    website_url TEXT,
    city TEXT,
    verification verification_status NOT NULL DEFAULT 'pending',
    email_domain_verified BOOLEAN NOT NULL DEFAULT FALSE,
    subscription_tier subscription_tier NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_role TEXT NOT NULL DEFAULT 'admin' CHECK (member_role IN ('admin', 'staff')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, user_id)
);

CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT 'company_domain',
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,
    attempts SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX email_verifications_email_idx ON email_verifications(email, purpose);

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    kind profile_kind NOT NULL,
    display_name TEXT NOT NULL,
    headline TEXT NOT NULL,
    bio TEXT,
    city TEXT,
    years_experience SMALLINT,
    languages TEXT[] NOT NULL DEFAULT '{}',
    keywords TEXT[] NOT NULL DEFAULT '{}',
    avatar_url TEXT,
    verification verification_status NOT NULL DEFAULT 'pending',
    average_rating NUMERIC(2,1) NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    response_minutes INTEGER,
    show_resolved_count BOOLEAN NOT NULL DEFAULT TRUE,
    subscription_tier subscription_tier NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    intro_video_url TEXT,
    portfolio_url TEXT,
    founded_year SMALLINT CHECK (founded_year BETWEEN 1800 AND 2100),
    team_size TEXT,
    view_count INTEGER NOT NULL DEFAULT 0,
    blocked_at TIMESTAMPTZ,
    blocked_reason TEXT,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((kind = 'expert' AND user_id IS NOT NULL) OR (kind = 'company' AND organization_id IS NOT NULL))
);

CREATE UNIQUE INDEX profiles_user_expert_unique_idx ON profiles(user_id) WHERE kind = 'expert' AND deleted_at IS NULL;

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE profile_services (
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    PRIMARY KEY (profile_id, service_id)
);

CREATE TABLE credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    issuing_body TEXT,
    credential_number TEXT,
    document_url TEXT,
    verification verification_status NOT NULL DEFAULT 'pending',
    verified_at TIMESTAMPTZ
);

CREATE TABLE social_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    follower_count INTEGER,
    UNIQUE (profile_id, platform)
);

CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(id),
    service_id UUID REFERENCES services(id),
    title TEXT NOT NULL,
    requirements TEXT NOT NULL,
    city TEXT,
    status request_status NOT NULL DEFAULT 'submitted',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE request_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    participant_role TEXT NOT NULL CHECK (participant_role IN ('customer', 'expert', 'company')),
    accepted_at TIMESTAMPTZ,
    completion_confirmed_at TIMESTAMPTZ,
    completion_disputed_at TIMESTAMPTZ,
    assigned_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
);

CREATE TABLE request_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id),
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    meeting_url TEXT,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'confirmed', 'cancelled', 'completed')),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    booked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (ends_at > starts_at)
);
CREATE UNIQUE INDEX appointments_profile_slot_active_idx
    ON appointments(profile_id, starts_at)
    WHERE status IN ('proposed', 'confirmed');

CREATE TABLE availability_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    CHECK (end_time > start_time)
);
CREATE INDEX availability_slots_profile_idx ON availability_slots(profile_id);

CREATE TABLE profile_offerings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    price_min_inr INTEGER CHECK (price_min_inr >= 0),
    price_max_inr INTEGER CHECK (price_max_inr >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (price_max_inr IS NULL OR price_min_inr IS NULL OR price_max_inr >= price_min_inr)
);
CREATE INDEX profile_offerings_profile_idx ON profile_offerings(profile_id);

CREATE TABLE profile_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    location TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE INDEX profile_experiences_profile_idx ON profile_experiences(profile_id);

CREATE TABLE profile_educations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    school TEXT NOT NULL,
    degree TEXT,
    field_of_study TEXT,
    start_year SMALLINT CHECK (start_year BETWEEN 1900 AND 2100),
    end_year SMALLINT CHECK (end_year BETWEEN 1900 AND 2100),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
);
CREATE INDEX profile_educations_profile_idx ON profile_educations(profile_id);

CREATE TABLE organization_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX organization_invites_pending_idx
    ON organization_invites(organization_id, lower(email))
    WHERE accepted_at IS NULL;

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES requests(id),
    reviewer_id UUID NOT NULL REFERENCES users(id),
    profile_id UUID NOT NULL REFERENCES profiles(id),
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body TEXT NOT NULL,
    verified_interaction BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (request_id, reviewer_id, profile_id)
);

CREATE TABLE saved_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, profile_id)
);

CREATE TABLE admin_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL CHECK (target_type IN ('user', 'profile', 'request')),
    target_id UUID NOT NULL,
    target_label TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX admin_actions_created_idx ON admin_actions(created_at DESC);

CREATE INDEX profiles_kind_verification_idx ON profiles(kind, verification);
CREATE INDEX profiles_city_idx ON profiles(city);
CREATE INDEX requests_customer_status_idx ON requests(customer_id, status);
CREATE INDEX request_events_request_created_idx ON request_events(request_id, created_at DESC);
CREATE UNIQUE INDEX request_participants_user_unique_idx
    ON request_participants(request_id, participant_role, user_id)
    WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX request_participants_organization_unique_idx
    ON request_participants(request_id, participant_role, organization_id)
    WHERE organization_id IS NOT NULL;

-- payments is created before profiles/organizations, so its identity links are added here.
ALTER TABLE payments ADD COLUMN profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE payments ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL;

CREATE INDEX saved_profiles_user_idx ON saved_profiles(user_id, created_at DESC);

CREATE TABLE ai_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    service_type varchar(40) NOT NULL,
    user_inputs jsonb NOT NULL DEFAULT '{}'::jsonb,
    calculated_data jsonb,
    ai_report text,
    variants jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    language varchar(2) NOT NULL DEFAULT 'ta' CHECK (language IN ('ta', 'en')),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    token_hash char(64) NOT NULL CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    tier varchar(16) NOT NULL DEFAULT 'basic' CHECK (tier = 'basic'),
    engine_version varchar(40) NOT NULL DEFAULT '1.0.0',
    prompt_version varchar(40) NOT NULL DEFAULT '1.0.0',
    attempt_count integer NOT NULL DEFAULT 1 CHECK (attempt_count BETWEEN 1 AND 5),
    generation_attempt integer NOT NULL DEFAULT 1 CHECK (generation_attempt = attempt_count),
    error_code varchar(40),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    last_attempt_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_ai_reports_user_created ON ai_reports(user_id, created_at DESC);
CREATE INDEX ix_ai_reports_created ON ai_reports(created_at);
CREATE INDEX ix_ai_reports_pending ON ai_reports(last_attempt_at) WHERE status = 'pending';

CREATE TABLE ai_report_family_members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label varchar(80) NOT NULL CHECK (char_length(label) BETWEEN 1 AND 80),
    details jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_ai_report_family_user ON ai_report_family_members(user_id);

CREATE TABLE ai_report_usage (
    id varchar(160) PRIMARY KEY,
    count integer NOT NULL DEFAULT 0 CHECK (count >= 0),
    expires_at timestamptz NOT NULL
);
CREATE INDEX ix_ai_report_usage_expires ON ai_report_usage(expires_at);
REVOKE ALL ON ai_reports, ai_report_family_members, ai_report_usage FROM anon, authenticated;
GRANT ALL ON ai_reports, ai_report_family_members, ai_report_usage TO service_role;

-- Block Supabase's public REST API (anon key) from reading tables; the backend connects as owner and bypasses RLS.
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$;

-- Profile images are stored as optimized objects, not database blobs. These
-- Supabase Storage statements are skipped for PostgreSQL providers without Storage.
DO $$
BEGIN
    IF to_regclass('storage.buckets') IS NOT NULL AND to_regclass('storage.objects') IS NOT NULL THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES ('profile-images', 'profile-images', TRUE, 1048576, ARRAY['image/webp'])
        ON CONFLICT (id) DO UPDATE SET
            public = EXCLUDED.public,
            file_size_limit = EXCLUDED.file_size_limit,
            allowed_mime_types = EXCLUDED.allowed_mime_types;

        EXECUTE 'DROP POLICY IF EXISTS profile_images_read_own ON storage.objects';
        EXECUTE 'DROP POLICY IF EXISTS profile_images_insert_own ON storage.objects';
        EXECUTE 'DROP POLICY IF EXISTS profile_images_update_own ON storage.objects';
        EXECUTE 'CREATE POLICY profile_images_read_own ON storage.objects FOR SELECT TO authenticated USING (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
        EXECUTE 'CREATE POLICY profile_images_insert_own ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
        EXECUTE 'CREATE POLICY profile_images_update_own ON storage.objects FOR UPDATE TO authenticated USING (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text) WITH CHECK (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
    END IF;
END $$;