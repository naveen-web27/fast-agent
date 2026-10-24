-- Thirumana porutham: signed-in history (last N per account) and prepaid report packs.
-- Apply to dev first, then production. Rows are keyed by the Supabase auth user id.
BEGIN;

CREATE TABLE porutham_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id uuid NOT NULL,
    couple_key char(48) NOT NULL,
    bride_name varchar(100) NOT NULL DEFAULT '',
    groom_name varchar(100) NOT NULL DEFAULT '',
    inputs jsonb NOT NULL,
    level varchar(6) NOT NULL CHECK (level IN ('high', 'medium', 'low')),
    stars_matched smallint NOT NULL,
    kattam_matched smallint NOT NULL,
    unlocked boolean NOT NULL DEFAULT false,
    report_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (auth_user_id, couple_key)
);
CREATE INDEX ix_porutham_history_owner ON porutham_history(auth_user_id, updated_at);

CREATE TABLE porutham_packs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id uuid NOT NULL,
    razorpay_order_id text UNIQUE,
    razorpay_payment_id text UNIQUE,
    amount_paise integer NOT NULL CHECK (amount_paise >= 100),
    reports_total integer NOT NULL CHECK (reports_total > 0),
    reports_used integer NOT NULL DEFAULT 0 CHECK (reports_used BETWEEN 0 AND reports_total),
    days integer NOT NULL CHECK (days > 0),
    status varchar(8) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid')),
    paid_at timestamptz,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_porutham_packs_owner ON porutham_packs(auth_user_id, status, expires_at);

ALTER TABLE porutham_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE porutham_packs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON porutham_history, porutham_packs FROM anon, authenticated;
GRANT ALL ON porutham_history, porutham_packs TO service_role;

COMMIT;
