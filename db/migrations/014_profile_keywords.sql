-- Provider-chosen search words (e.g. "ads", "facebook ads") so customers find them in their own words.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS keywords TEXT[] NOT NULL DEFAULT '{}';
