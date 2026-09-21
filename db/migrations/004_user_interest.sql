-- Stores the customer's declared areas of interest (e.g. "Health insurance"),
-- seeded at onboarding, grown from marketplace searches, and editable in settings.
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[] NOT NULL DEFAULT '{}';

-- Migrate from the earlier single-value "interest" column, if this ran before the array version existed.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'interest'
    ) THEN
        UPDATE users SET interests = ARRAY[interest] WHERE interest IS NOT NULL AND interest <> '' AND interests = '{}';
        ALTER TABLE users DROP COLUMN interest;
    END IF;
END $$;
