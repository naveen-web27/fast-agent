-- Sample data for local/staging testing of live marketplace endpoints.
-- Safe to run multiple times: uses ON CONFLICT to avoid duplicate rows.

INSERT INTO services (id, name, slug, description) VALUES
    ('11111111-1111-1111-1111-111111111101', 'Health insurance', 'health-insurance', 'Personal and family medical cover advice'),
    ('11111111-1111-1111-1111-111111111102', 'Employee benefits', 'employee-benefits', 'Group and corporate benefits consulting'),
    ('11111111-1111-1111-1111-111111111103', 'Claims guidance', 'claims-guidance', 'Help filing and tracking insurance claims')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, auth_user_id, full_name, email, role, subscription_tier) VALUES
    ('22222222-2222-2222-2222-222222222201', '33333333-3333-3333-3333-333333333301', 'Riya Menon', 'riya.menon@example.com', 'expert', 'free'),
    ('22222222-2222-2222-2222-222222222202', '33333333-3333-3333-3333-333333333302', 'Arun Prasad', 'arun.prasad@example.com', 'expert', 'free')
ON CONFLICT (id) DO NOTHING;

INSERT INTO organizations (id, name, slug, description, city, verification, subscription_tier) VALUES
    ('44444444-4444-4444-4444-444444444401', 'Coverwise Insurance', 'coverwise-insurance', 'Insurance advisory company', 'India-wide', 'verified', 'pro')
ON CONFLICT (id) DO NOTHING;

INSERT INTO profiles (id, user_id, organization_id, kind, display_name, headline, bio, city, years_experience, languages, avatar_url, verification, average_rating, review_count, response_minutes) VALUES
    ('55555555-5555-5555-5555-555555555501', '22222222-2222-2222-2222-222222222201', NULL, 'expert', 'Dr. Riya Menon', 'Independent health insurance advisor', 'Helps families compare medical cover and choose policies that fit their budget.', 'Bengaluru', 9, ARRAY['English', 'Hindi', 'Tamil'], 'https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=180&q=80', 'verified', 4.9, 142, 22),
    ('55555555-5555-5555-5555-555555555502', NULL, '44444444-4444-4444-4444-444444444401', 'company', 'Coverwise Insurance', 'Insurance advisory company', '41 licensed advisors replying in under 25 minutes.', 'India-wide', NULL, ARRAY['English', 'Hindi'], 'https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=180&q=80', 'verified', 4.7, 387, 25),
    ('55555555-5555-5555-5555-555555555503', '22222222-2222-2222-2222-222222222202', NULL, 'expert', 'Arun Prasad', 'Employee benefits consultant', 'Guides small businesses through group cover, renewals, and senior citizen plans.', 'Chennai', 12, ARRAY['English', 'Tamil', 'Telugu'], 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=180&q=80', 'verified', 4.8, 96, 40)
ON CONFLICT (id) DO NOTHING;

INSERT INTO profile_services (profile_id, service_id) VALUES
    ('55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101'),
    ('55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111103'),
    ('55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111101'),
    ('55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111103'),
    ('55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111102'),
    ('55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103')
ON CONFLICT DO NOTHING;
