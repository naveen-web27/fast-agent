-- Supabase exposes every public table through its REST API using the public (anon) key.
-- RLS with no policies blocks that path completely; the backend connects as the table
-- owner (postgres), which bypasses RLS, so the app keeps working. Safe to re-run.
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$;
