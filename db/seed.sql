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

-- Sample customers + completed requests so the "N clients resolved" badge has real numbers to show.
INSERT INTO users (id, auth_user_id, full_name, email, role, subscription_tier) VALUES
    ('66666666-6666-6666-6666-666666666601', '77777777-7777-7777-7777-777777777701', 'Meera Iyer', 'meera.iyer@example.com', 'customer', 'free'),
    ('66666666-6666-6666-6666-666666666602', '77777777-7777-7777-7777-777777777702', 'Karthik Rajan', 'karthik.rajan@example.com', 'customer', 'free'),
    ('66666666-6666-6666-6666-666666666603', '77777777-7777-7777-7777-777777777703', 'Divya Sharma', 'divya.sharma@example.com', 'customer', 'free'),
    ('66666666-6666-6666-6666-666666666604', '77777777-7777-7777-7777-777777777704', 'Sanjay Gupta', 'sanjay.gupta@example.com', 'customer', 'free'),
    ('66666666-6666-6666-6666-666666666605', '77777777-7777-7777-7777-777777777705', 'Priya Nair', 'priya.nair@example.com', 'customer', 'free'),
    ('66666666-6666-6666-6666-666666666606', '77777777-7777-7777-7777-777777777706', 'Vikram Singh', 'vikram.singh@example.com', 'customer', 'free')
ON CONFLICT (id) DO NOTHING;

INSERT INTO requests (id, customer_id, service_id, title, requirements, city, status) VALUES
    ('88888888-8888-8888-8888-888888888801', '66666666-6666-6666-6666-666666666601', '11111111-1111-1111-1111-111111111101', 'Family health cover', 'Comparing family floater plans for 4 members.', 'Bengaluru', 'completed'),
    ('88888888-8888-8888-8888-888888888802', '66666666-6666-6666-6666-666666666602', '11111111-1111-1111-1111-111111111101', 'Senior parent health plan', 'Need a plan covering a pre-existing condition.', 'Bengaluru', 'completed'),
    ('88888888-8888-8888-8888-888888888803', '66666666-6666-6666-6666-666666666603', '11111111-1111-1111-1111-111111111103', 'Claim rejection help', 'Insurer rejected a hospitalisation claim, need guidance.', 'Bengaluru', 'completed'),
    ('88888888-8888-8888-8888-888888888804', '66666666-6666-6666-6666-666666666604', '11111111-1111-1111-1111-111111111101', 'New policy comparison', 'Comparing 3 insurers before renewal.', 'Bengaluru', 'completed'),
    ('88888888-8888-8888-8888-888888888805', '66666666-6666-6666-6666-666666666601', '11111111-1111-1111-1111-111111111101', 'Group cover for startup', 'Setting up health cover for a 12-person team.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888806', '66666666-6666-6666-6666-666666666602', '11111111-1111-1111-1111-111111111101', 'Maternity cover add-on', 'Adding maternity benefits to an existing policy.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888807', '66666666-6666-6666-6666-666666666603', '11111111-1111-1111-1111-111111111103', 'Claims escalation', 'Escalating a delayed reimbursement claim.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888808', '66666666-6666-6666-6666-666666666604', '11111111-1111-1111-1111-111111111101', 'Multi-city branch cover', 'Health cover across 3 office locations.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888809', '66666666-6666-6666-6666-666666666605', '11111111-1111-1111-1111-111111111101', 'Renewal review', 'Reviewing renewal terms before signing.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888810', '66666666-6666-6666-6666-666666666606', '11111111-1111-1111-1111-111111111101', 'New employee onboarding cover', 'Adding 5 new hires to the group policy.', 'India-wide', 'completed'),
    ('88888888-8888-8888-8888-888888888811', '66666666-6666-6666-6666-666666666605', '11111111-1111-1111-1111-111111111102', 'Employee benefits audit', 'Reviewing our current benefits package for gaps.', 'Chennai', 'completed'),
    ('88888888-8888-8888-8888-888888888812', '66666666-6666-6666-6666-666666666606', '11111111-1111-1111-1111-111111111102', 'Small business group plan', 'Setting up benefits for a 8-person team.', 'Chennai', 'completed'),
    ('88888888-8888-8888-8888-888888888813', '66666666-6666-6666-6666-666666666601', '11111111-1111-1111-1111-111111111102', 'Retirement benefits plan', 'Adding a retirement benefit tier for senior staff.', 'Chennai', 'completed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO request_participants (id, request_id, user_id, organization_id, participant_role, accepted_at) VALUES
    ('99999999-9999-9999-9999-999999999901', '88888888-8888-8888-8888-888888888801', '22222222-2222-2222-2222-222222222201', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999902', '88888888-8888-8888-8888-888888888802', '22222222-2222-2222-2222-222222222201', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999903', '88888888-8888-8888-8888-888888888803', '22222222-2222-2222-2222-222222222201', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999904', '88888888-8888-8888-8888-888888888804', '22222222-2222-2222-2222-222222222201', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999905', '88888888-8888-8888-8888-888888888805', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999906', '88888888-8888-8888-8888-888888888806', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999907', '88888888-8888-8888-8888-888888888807', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999908', '88888888-8888-8888-8888-888888888808', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999909', '88888888-8888-8888-8888-888888888809', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999910', '88888888-8888-8888-8888-888888888810', NULL, '44444444-4444-4444-4444-444444444401', 'company', now()),
    ('99999999-9999-9999-9999-999999999911', '88888888-8888-8888-8888-888888888811', '22222222-2222-2222-2222-222222222202', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999912', '88888888-8888-8888-8888-888888888812', '22222222-2222-2222-2222-222222222202', NULL, 'expert', now()),
    ('99999999-9999-9999-9999-999999999913', '88888888-8888-8888-8888-888888888813', '22222222-2222-2222-2222-222222222202', NULL, 'expert', now())
ON CONFLICT (id) DO NOTHING;
