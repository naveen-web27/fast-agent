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
    auth_user_id UUID NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT UNIQUE,
    role user_role NOT NULL DEFAULT 'customer',
    subscription_tier subscription_tier NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    website_url TEXT,
    city TEXT,
    verification verification_status NOT NULL DEFAULT 'pending',
    subscription_tier subscription_tier NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
    avatar_url TEXT,
    verification verification_status NOT NULL DEFAULT 'pending',
    average_rating NUMERIC(2,1) NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    response_minutes INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((kind = 'expert' AND user_id IS NOT NULL) OR (kind = 'company' AND organization_id IS NOT NULL))
);

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
    CHECK (ends_at > starts_at)
);

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