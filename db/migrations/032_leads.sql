-- Leads: people who enquired (e.g. on WhatsApp from ads) and haven't necessarily signed up. Admin-only.
-- Run on dev first, then production, before deploying the matching backend.
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT,
    -- E.164, e.g. +919876543210; one lead per number.
    phone TEXT NOT NULL,
    lead_type TEXT NOT NULL DEFAULT 'unknown' CHECK (lead_type IN ('unknown', 'customer', 'expert', 'company', 'worker')),
    business_name TEXT,
    service TEXT,
    city TEXT,
    source TEXT,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'contacted', 'interested', 'follow_up', 'not_interested', 'signed_up')),
    follow_up_on DATE,
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS leads_phone_idx ON leads(phone);
CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status, follow_up_on);
CREATE INDEX IF NOT EXISTS leads_created_idx ON leads(created_at DESC);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON leads FROM anon, authenticated;
GRANT ALL ON leads TO service_role;
