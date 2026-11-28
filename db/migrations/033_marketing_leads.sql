-- RightConnect Marketing (poster design + ads agency): client enquiries, follow-ups, payments and feedback. Admin-only.
-- Separate from `leads` (032), which tracks people to sign up on RightConnect.
-- Run on dev first, then production, before deploying the matching backend.
CREATE TABLE IF NOT EXISTS marketing_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT,
    -- E.164, e.g. +919876543210; one lead per number.
    phone TEXT NOT NULL,
    business_name TEXT,
    business_type TEXT,
    city TEXT,
    -- What they want, e.g. "Poster design", "Ads", "Posters + Ads".
    service TEXT,
    source TEXT,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'called', 'interested', 'converted', 'in_progress', 'completed', 'lost')),
    -- Agreed price in whole rupees; received money is the sum of 'payment' activities.
    deal_amount INTEGER CHECK (deal_amount IS NULL OR deal_amount >= 0),
    follow_up_on DATE,
    next_action TEXT,
    rating SMALLINT CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    feedback TEXT,
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS marketing_leads_phone_idx ON marketing_leads(phone);
CREATE INDEX IF NOT EXISTS marketing_leads_status_idx ON marketing_leads(status, follow_up_on);
CREATE INDEX IF NOT EXISTS marketing_leads_created_idx ON marketing_leads(created_at DESC);

-- Follow-up history: calls, WhatsApp messages, meetings, notes, payments and status changes.
CREATE TABLE IF NOT EXISTS marketing_lead_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES marketing_leads(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('note', 'call', 'whatsapp', 'meeting', 'payment', 'status')),
    text TEXT,
    amount INTEGER CHECK (amount IS NULL OR amount > 0),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT marketing_lead_activities_payment_amount CHECK ((kind = 'payment') = (amount IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS marketing_lead_activities_lead_idx ON marketing_lead_activities(lead_id, created_at DESC);

ALTER TABLE marketing_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_lead_activities ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON marketing_leads, marketing_lead_activities FROM anon, authenticated;
GRANT ALL ON marketing_leads, marketing_lead_activities TO service_role;
