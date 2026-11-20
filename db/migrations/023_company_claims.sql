-- Admin-created company listings that the real owner can claim later.
-- Existing companies were registered by their owner, so they default to 'claimed'.
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS claim_status TEXT NOT NULL DEFAULT 'claimed';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'organizations_claim_status_check') THEN
        ALTER TABLE organizations ADD CONSTRAINT organizations_claim_status_check CHECK (claim_status IN ('unclaimed', 'claimed'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS organization_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_email TEXT NOT NULL,
    email_matches_listing BOOLEAN NOT NULL DEFAULT FALSE,
    phone TEXT,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    review_reason TEXT,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS organization_claims_one_pending_idx ON organization_claims(organization_id, user_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS organization_claims_status_idx ON organization_claims(status, created_at);
ALTER TABLE organization_claims ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON organization_claims FROM anon, authenticated;
GRANT ALL ON organization_claims TO service_role;
