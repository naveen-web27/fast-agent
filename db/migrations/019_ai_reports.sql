-- Apply manually to dev before production. The backend DB role must own these
-- tables or have BYPASSRLS and explicit table grants; no browser policies exist.
BEGIN;

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

ALTER TABLE ai_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_report_family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_report_usage ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ai_reports, ai_report_family_members, ai_report_usage FROM anon, authenticated;
GRANT ALL ON ai_reports, ai_report_family_members, ai_report_usage TO service_role;
COMMIT;

-- Schedule a server-side daily maintenance job, adjusting 30 to
-- AI_REPORT_RETENTION_DAYS. Run bounded batches until no rows remain:
-- DELETE FROM ai_reports WHERE id IN
--   (SELECT id FROM ai_reports WHERE created_at < now() - interval '30 days'
--    ORDER BY created_at LIMIT 1000);
-- DELETE FROM ai_report_usage WHERE expires_at < now();
-- Family records persist by explicit consent until removed/account deletion.