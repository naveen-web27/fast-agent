-- LinkedIn-style profiles: experience and education for experts, company facts,
-- and a light public profile for customers.

ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS founded_year SMALLINT CHECK (founded_year BETWEEN 1800 AND 2100);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS team_size TEXT;

CREATE TABLE IF NOT EXISTS profile_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    location TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS profile_experiences_profile_idx ON profile_experiences(profile_id);

CREATE TABLE IF NOT EXISTS profile_educations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    school TEXT NOT NULL,
    degree TEXT,
    field_of_study TEXT,
    start_year SMALLINT CHECK (start_year BETWEEN 1900 AND 2100),
    end_year SMALLINT CHECK (end_year BETWEEN 1900 AND 2100),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
);
CREATE INDEX IF NOT EXISTS profile_educations_profile_idx ON profile_educations(profile_id);
