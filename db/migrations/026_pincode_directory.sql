-- Place names for PIN codes, so people can type "Edappadi" or "Salem" instead of a PIN.
-- Load the rows once per database after this migration:
--   PYTHONPATH=backend python3 db/scripts/import_pincodes.py
-- pg_trgm gives typo-tolerant matching (e.g. "Edappadi" finds the official "Idappadi").
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS pincode_areas (
    id SERIAL PRIMARY KEY,
    pincode TEXT NOT NULL CHECK (pincode ~ '^[1-9][0-9]{5}$'),
    area TEXT NOT NULL,
    taluk TEXT NOT NULL DEFAULT '',
    district TEXT NOT NULL,
    state TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS pincode_areas_pincode_idx ON pincode_areas(pincode);
CREATE INDEX IF NOT EXISTS pincode_areas_area_trgm ON pincode_areas USING gin (lower(area) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS pincode_areas_taluk_trgm ON pincode_areas USING gin (lower(taluk) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS pincode_areas_district_trgm ON pincode_areas USING gin (lower(district) gin_trgm_ops);
ALTER TABLE pincode_areas ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON pincode_areas FROM anon, authenticated;
GRANT ALL ON pincode_areas TO service_role;

-- The chosen area name ("Idappadi") shown next to the city/district on cards and the location bar.
ALTER TABLE users ADD COLUMN IF NOT EXISTS locality TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS locality TEXT;
