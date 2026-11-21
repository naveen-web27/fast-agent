-- Location: 6-digit Indian PIN codes so searches can show nearby people first (same area, district, then state).
-- Optional everywhere for existing rows; the app asks people with a missing location to add it.
ALTER TABLE users ADD COLUMN IF NOT EXISTS pincode TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS pincode TEXT;
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS pincode TEXT;
ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS pincode TEXT;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['users', 'profiles', 'worker_profiles', 'job_posts'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = t || '_pincode_check') THEN
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK (pincode ~ ''^[1-9][0-9]{5}$'')', t, t || '_pincode_check');
        END IF;
    END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS profiles_pincode_idx ON profiles(pincode) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS worker_profiles_pincode_idx ON worker_profiles(pincode) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS job_posts_pincode_idx ON job_posts(pincode) WHERE status = 'open';
