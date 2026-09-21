-- Apply this once if schema.sql was already run before subscription tiers existed.
-- Every existing and new user/organization defaults to the free tier.

DO $$ BEGIN
    CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier subscription_tier NOT NULL DEFAULT 'free';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_tier subscription_tier NOT NULL DEFAULT 'free';
