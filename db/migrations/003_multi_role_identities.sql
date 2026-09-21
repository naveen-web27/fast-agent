-- Adds multi-role support: one auth identity can be a customer, an expert, and/or
-- admin of one or more companies at the same time.

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_role TEXT NOT NULL DEFAULT 'admin' CHECK (member_role IN ('admin', 'staff')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, user_id)
);

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS email_domain_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- One personal expert profile per user; company profiles are unaffected (user_id IS NULL there).
CREATE UNIQUE INDEX IF NOT EXISTS profiles_user_expert_unique_idx
    ON profiles(user_id)
    WHERE kind = 'expert';

CREATE TABLE IF NOT EXISTS email_verifications (
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
CREATE INDEX IF NOT EXISTS email_verifications_email_idx ON email_verifications(email, purpose);

-- No backfill needed: prior onboarding only ever wrote to `users` and never created
-- `profiles`/`organizations` rows for expert or company_admin signups, so there is no
-- legacy expert/company data to migrate into the new tables.
