ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL CHECK (plan IN ('pro', 'enterprise')),
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 100),
    razorpay_link_id TEXT UNIQUE,
    razorpay_payment_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'refunded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at TIMESTAMPTZ,
    access_expires_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS payments_user_id_idx ON payments(user_id);