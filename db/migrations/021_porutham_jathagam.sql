-- Individual Jathagam reports share the porutham history and report packs. Apply after 020.
BEGIN;

ALTER TABLE porutham_history ADD COLUMN kind varchar(10) NOT NULL DEFAULT 'kattam'
    CHECK (kind IN ('kattam', 'jathagam'));

COMMIT;
