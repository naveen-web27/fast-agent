-- Direct contact: workers and job posters can let signed-in users call or WhatsApp them.
-- Off for existing rows (they were promised privacy until a hire is accepted); new sign-ups opt in.
ALTER TABLE worker_profiles ADD COLUMN IF NOT EXISTS show_contact BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS show_contact BOOLEAN NOT NULL DEFAULT FALSE;
