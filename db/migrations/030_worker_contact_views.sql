-- Worker contact: an optional email collected by admins, and a log of who viewed each worker's phone/email.
-- One row per (worker, viewer). New rows count toward the viewer's daily limit (Free 10, Pro 20, Enterprise 30);
-- viewing the same worker again does not. Workers can report a caller, and admins review the reports.
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS contact_email TEXT;

CREATE TABLE IF NOT EXISTS worker_contact_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    viewer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    view_count INTEGER NOT NULL DEFAULT 1,
    reported_at TIMESTAMPTZ,
    report_reason TEXT,
    CONSTRAINT worker_contact_views_once UNIQUE (worker_id, viewer_user_id)
);
CREATE INDEX IF NOT EXISTS worker_contact_views_viewer_idx ON worker_contact_views(viewer_user_id, first_viewed_at DESC);
CREATE INDEX IF NOT EXISTS worker_contact_views_reported_idx ON worker_contact_views(reported_at DESC) WHERE reported_at IS NOT NULL;

ALTER TABLE worker_contact_views ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON worker_contact_views FROM anon, authenticated;
GRANT ALL ON worker_contact_views TO service_role;
