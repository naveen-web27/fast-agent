# RightConnect API

## Layout

- `app/features/<feature>/`: each product feature owns its route, schemas, and service.
- `app/features/router.py`: one registry of feature routers, imported only by `main.py`.
- `app/models/`: SQLAlchemy ORM models.
- `app/db/`: database base and async sessions.
- `app/core/` and `app/security/`: shared configuration and cross-feature authentication.

## Local Setup

1. Create `backend/.env` from `backend/.env.example` and add the real Supabase database URL.
2. Install dependencies: `python3 -m pip install -r backend/requirements.txt`.
3. Start the API: `python3 -m uvicorn app.main:app --app-dir backend --reload`.
4. Open `http://127.0.0.1:8000/docs`.

## Authentication Boundary

The `/api/v1/auth/onboarding` endpoint requires a Supabase access token and derives `auth_user_id` from Supabase's authenticated `/auth/v1/user` response. It never accepts an auth identity from the request body.

Google OAuth is best handled by Supabase Auth. WhatsApp OTP needs an approved WhatsApp provider or an OTP provider; its verification must happen server-side.