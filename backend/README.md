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

### Session persistence

There is no custom JWT code in this backend — access tokens are issued and verified by Supabase Auth (`get_current_auth_user_id` just calls Supabase's `/auth/v1/user`). Do **not** enable **Time-box user sessions** in the Supabase dashboard (Authentication → Sessions) — that forces every user to sign in with Google again once the box expires. Leave it disabled so `supabase-js`'s refresh token keeps the session alive indefinitely between visits; users only re-authenticate if they explicitly sign out or revoke access.

## Troubleshooting: 500 error / connection failure on Render

If requests that touch the database fail with a 500 and the traceback ends inside `asyncpg`'s SSL `create_connection` (no clear app error), `DATABASE_URL` is pointing at Supabase's **direct** host (`db.PROJECT.supabase.co`). That host is IPv6-only, and Render does not support outbound IPv6, so the connection just hangs/fails.

Fix: in Supabase, go to **Settings -> Database -> Connection pooling** and copy the pooler connection string instead (`aws-0-<region>.pooler.supabase.com`, port `6543` for transaction mode or `5432` for session mode). Update the `DATABASE_URL` env var on Render to that value and redeploy.

## Marketplace profiles

`GET /api/v1/profiles?q=&city=&kind=` searches the `profiles` table (joined with `services`) and is what `frontend/pages/marketplace.html` now calls for live discover results, replacing the old hardcoded cards. Seed data for local testing lives in `db/seed.sql`.

## Subscriptions

`users.subscription_tier` and `organizations.subscription_tier` default to `free` (see `db/migrations/002_subscription_tier.sql`). There is no billing/upgrade flow yet — every account starts on the free tier until that is built.

## Multi-role identities (customer + expert + company, same login)

One auth identity (one `users` row) can act as a customer, have one personal expert profile, and admin any number of companies at the same time:

- `GET /api/v1/auth/identities` — returns the base account plus `expert_profile` (or null) and `companies` (list with each `member_role`/`verification`).
- `POST /api/v1/auth/identities/expert` — adds a personal expert profile to an already-onboarded account.
- `POST /api/v1/auth/identities/companies` — registers a new company and makes the caller its first admin (`organization_members`, `member_role='admin'`).
- The initial `/auth/onboarding` call still creates the base account, and now also creates the matching `profiles`/`organizations` row for whichever role was picked first (previously this data was silently discarded).
- `frontend/pages/marketplace.html` has a workspace switcher (sidebar, under the logo) that lists Customer / Expert profile / each company, and modals to add an expert profile or a new company without leaving the page.

Run `db/migrations/003_multi_role_identities.sql` against an existing database (adds `organization_members`, `email_verifications`, `organizations.email_domain_verified`).

### Company email/domain verification

Company `verification` starts `pending` (same manual-review flag used for expert credentials). Additionally, `organizations.email_domain_verified` can be set via a one-time email code:

1. `POST /api/v1/auth/identities/companies/domain-otp/send` — emails a 6-digit code to a company email address (caller must be an admin of that organization). Requires `RESEND_API_KEY` to be set (see `.env.example`); returns 503 if not configured.
2. `POST /api/v1/auth/identities/companies/domain-otp/verify` — checks the code (10 minute expiry, 5 attempts) and sets `email_domain_verified = true` on success.

This only proves the admin can receive mail at that address — it is a real but partial signal, not full business verification. Companies without a matching domain email (e.g. a startup using a personal Gmail) can still register and go through manual document review instead; they simply stay `email_domain_verified = false` until they either verify a domain email or a platform admin manually verifies their `verification` status from uploaded business registration documents.