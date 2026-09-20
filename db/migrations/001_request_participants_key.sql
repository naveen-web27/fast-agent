-- Apply this once only if the original schema.sql was already run in Supabase.
-- It replaces the composite key that prevented company-only participants.

ALTER TABLE request_participants DROP CONSTRAINT request_participants_pkey;
ALTER TABLE request_participants ADD COLUMN id UUID DEFAULT gen_random_uuid();
UPDATE request_participants SET id = gen_random_uuid() WHERE id IS NULL;
ALTER TABLE request_participants ALTER COLUMN id SET NOT NULL;
ALTER TABLE request_participants ADD PRIMARY KEY (id);

CREATE UNIQUE INDEX IF NOT EXISTS request_participants_user_unique_idx
    ON request_participants(request_id, participant_role, user_id)
    WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS request_participants_organization_unique_idx
    ON request_participants(request_id, participant_role, organization_id)
    WHERE organization_id IS NOT NULL;