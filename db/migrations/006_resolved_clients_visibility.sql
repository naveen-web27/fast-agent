-- Lets an expert or company owner hide the "N clients resolved" badge shown on their card.
ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS show_resolved_count BOOLEAN NOT NULL DEFAULT TRUE;
