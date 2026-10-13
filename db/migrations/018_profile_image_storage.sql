-- Keep optimized profile images in Supabase Storage; PostgreSQL stores only their URL.
DO $$
BEGIN
    IF to_regclass('storage.buckets') IS NOT NULL AND to_regclass('storage.objects') IS NOT NULL THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES ('profile-images', 'profile-images', TRUE, 1048576, ARRAY['image/webp'])
        ON CONFLICT (id) DO UPDATE SET
            public = EXCLUDED.public,
            file_size_limit = EXCLUDED.file_size_limit,
            allowed_mime_types = EXCLUDED.allowed_mime_types;

        EXECUTE 'DROP POLICY IF EXISTS profile_images_read_own ON storage.objects';
        EXECUTE 'DROP POLICY IF EXISTS profile_images_insert_own ON storage.objects';
        EXECUTE 'DROP POLICY IF EXISTS profile_images_update_own ON storage.objects';
        EXECUTE 'CREATE POLICY profile_images_read_own ON storage.objects FOR SELECT TO authenticated USING (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
        EXECUTE 'CREATE POLICY profile_images_insert_own ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
        EXECUTE 'CREATE POLICY profile_images_update_own ON storage.objects FOR UPDATE TO authenticated USING (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text) WITH CHECK (bucket_id = ''profile-images'' AND (storage.foldername(name))[1] = (select auth.uid())::text)';
    END IF;
END $$;