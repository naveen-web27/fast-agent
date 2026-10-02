ALTER TABLE requests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE request_participants ADD COLUMN IF NOT EXISTS completion_confirmed_at TIMESTAMPTZ;
ALTER TABLE request_participants ADD COLUMN IF NOT EXISTS completion_disputed_at TIMESTAMPTZ;
