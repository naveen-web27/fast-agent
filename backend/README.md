# RightConnect API

## Layout

- `app/features/<feature>/`: each product feature owns its route, schemas, and service.
- `app/features/router.py`: one registry of feature routers, imported only by `main.py`.
- `app/models/`: SQLAlchemy ORM models.
- `app/db/`: database base and async sessions.
- `app/core/` and `app/security/`: shared configuration and cross-feature authentication.

## Local Setup

1. Use Python 3.12.8 (pinned in the repository's `.python-version`).
2. Create `backend/.env` from `backend/.env.example` and add the real Supabase database URL.
3. Install dependencies: `python3 -m pip install -r backend/requirements.txt`.
4. Run `db/schema.sql` against your database (or `db/migrations/002_subscription_tier.sql` if the schema already existed), then optionally `db/seed.sql` for sample marketplace profiles.
5. Start the API: `python3 -m uvicorn app.main:app --app-dir backend --reload`.
6. Open `http://127.0.0.1:8000/docs`.

## Authentication Boundary

The `/api/v1/auth/onboarding` endpoint requires a Supabase access token and derives `auth_user_id` from Supabase's authenticated `/auth/v1/user` response. It never accepts an auth identity from the request body.

Google OAuth is best handled by Supabase Auth. WhatsApp OTP needs an approved WhatsApp provider or an OTP provider; its verification must happen server-side.

### Session/JWT expiry (1 day)

There is no custom JWT code in this backend — access tokens are issued and verified by Supabase Auth (`get_current_auth_user_id` just calls Supabase's `/auth/v1/user`). To make sessions expire after 1 day, set it in the Supabase dashboard:

1. Supabase project → **Authentication** → **Sessions**.
2. Set **Time-box user sessions** (or **Access token (JWT) expiry** under Auth settings, depending on Supabase version) to `86400` seconds (1 day).
3. Save. New sign-ins will expire after 1 day; the frontend's `supabase-js` client already refreshes/rejects tokens automatically based on this setting — no frontend code change needed.

## Marketplace profiles

`GET /api/v1/profiles?q=&city=&kind=` searches the `profiles` table (joined with `services`) and is what `frontend/pages/marketplace.html` now calls for live discover results, replacing the old hardcoded cards. Seed data for local testing lives in `db/seed.sql`.

## Subscriptions

`users.subscription_tier` and `organizations.subscription_tier` default to `free` (see `db/migrations/002_subscription_tier.sql`). There is no billing/upgrade flow yet — every account starts on the free tier until that is built.