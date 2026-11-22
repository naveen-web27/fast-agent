-- Worker pay as a range (e.g. ₹500–1,000 per day), with an option to hide it from the public.
-- rate_amount stays the lower end; rate_max is the optional upper end.
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS rate_max INTEGER;
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS rate_hidden BOOLEAN NOT NULL DEFAULT FALSE;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'worker_profiles_rate_range_check') THEN
        ALTER TABLE worker_profiles ADD CONSTRAINT worker_profiles_rate_range_check
            CHECK (rate_max IS NULL OR (rate_amount IS NOT NULL AND rate_max >= rate_amount));
    END IF;
END $$;
