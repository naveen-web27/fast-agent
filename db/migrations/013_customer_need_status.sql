-- Customer "looking for help" switch. Turned off automatically once a finished request is rated,
-- so experts/companies stop seeing that customer as an active lead.
ALTER TABLE users ADD COLUMN IF NOT EXISTS looking_for_help BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS need_fulfilled_at TIMESTAMPTZ;
