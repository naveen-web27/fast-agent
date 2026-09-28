-- Fixes DB drift: some environments have user_id/organization_id as NOT NULL on request_participants,
-- but a participant is either a user (expert/customer) or an organization (company), never both.
ALTER TABLE request_participants ALTER COLUMN organization_id DROP NOT NULL;
ALTER TABLE request_participants ALTER COLUMN user_id DROP NOT NULL;

