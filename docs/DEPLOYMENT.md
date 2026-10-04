# Deploying RightConnect (dev and production)

Two separate environments, each with its own Render service and Supabase project:

| | Dev (existing) | Production (new) |
|---|---|---|
| Render service | `rightconnect-staging`, Oregon | new service, **Singapore** |
| Supabase project | current project, `ap-northeast-1` (Tokyo) | new project, **`ap-southeast-1` (Singapore)** |
| Data | test data, `db/seed.sql` allowed | real users only, never run `seed.sql` |
| Razorpay | Test mode keys | Live mode keys |

## Why region matters

Every API call does 5–15 database queries, each costing at least one network round trip between Render and Supabase.

| Setup | Server ↔ DB round trip | Opening a chat |
|---|---|---|
| Render Oregon + Supabase Tokyo (dev today) | ~170 ms | ~3.5 s |
| Render Singapore + Supabase Singapore (prod) | ~1–2 ms | < 0.5 s |

Users are in India, so Singapore is also the closest region to them (~50 ms vs ~250 ms to Oregon). **Render and Supabase must always be in the same region.** Neither can change region later; a move means a new service/project.

---

## 1. Supabase (production project)

1. **New project** → Region **Southeast Asia (Singapore) – ap-southeast-1**. Save the database password in a password manager.
   - Plan: Free works, but free projects **pause after 7 days without traffic** and have no daily backups. Use **Pro** for production.
2. **Create the schema** (SQL Editor → New query):
   1. Paste and run all of `db/schema.sql` (it already contains everything up to migration 015).
   2. Run `db/migrations/016_enable_rls.sql` (blocks the public REST API from reading tables; the backend is unaffected).
   3. Do **not** run `db/seed.sql` (demo profiles and fake reviews).
3. **Connection string** (Project Settings → Database → Connection string → **Session pooler**):
   - Use the **session pooler, port `5432`**: `postgresql://postgres.<ref>:<password>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`
   - Do not use the direct `db.<ref>.supabase.co` host (IPv6-only, Render cannot reach it).
   - Session mode allows `DB_STATEMENT_CACHE=true` (one round trip per query instead of two).
4. **Authentication → Providers → Google**: enable, paste the Google OAuth Client ID and Secret.
   - In **Google Cloud Console → APIs & Services → Credentials → your OAuth client → Authorized redirect URIs**, add the new project's callback: `https://<new-ref>.supabase.co/auth/v1/callback`.
   - **OAuth consent screen**: status **In production** (not Testing), app name/logo/privacy URL filled in, or only test users can sign in.
5. **Authentication → URL Configuration**:
   - Site URL: `https://rightconnect.app` (your production domain).
   - Redirect URLs: `https://rightconnect.app/pages/auth.html`, `https://rightconnect.app/pages/marketplace.html`, `https://rightconnect.app/pages/plans.html` (add the `*.onrender.com` URL too while testing).
6. **Authentication → Sessions**: leave **Time-box user sessions** and **Inactivity timeout** off (otherwise users must sign in with Google again).
7. **Project Settings → API**: copy the **Project URL** and the **publishable (anon) key** for Render.

## 2. Render (production web service)

1. **New → Web Service** → connect the same GitHub repo.
   - Name: `rightconnect-prod` · **Region: Singapore** · Branch: `production` (see section 6) · Runtime: Python.
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - **Health check path**: `/api/v1/health`
   - Plan: **Starter or higher**. The free plan sleeps after 15 minutes idle and the next visitor waits 30–60 s.
2. **Environment variables**:

| Key | Production value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` |
| `DATABASE_URL` | session pooler URL from Supabase step 3 (port 5432) |
| `DB_STATEMENT_CACHE` | `true` (only because the URL uses port 5432; keep `false` on 6543) |
| `SUPABASE_URL` | `https://<new-ref>.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | publishable/anon key of the new project |
| `CORS_ORIGINS` | `https://rightconnect.app` (plus the onrender.com URL while testing) |
| `APP_BASE_URL` | `https://rightconnect.app` (no trailing slash) |
| `RESEND_API_KEY` | Resend API key (company email verification codes) |
| `RESEND_FROM_EMAIL` | `RightConnect <no-reply@rightconnect.app>` (domain verified in Resend) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | **Live** keys |
| `RAZORPAY_WEBHOOK_SECRET` | secret of the live webhook (section 3) |
| `RAZORPAY_PRO_AMOUNT_PAISE` / `RAZORPAY_ENTERPRISE_AMOUNT_PAISE` | prices in paise, e.g. `49900` = ₹499 |
| `ADMIN_PATH` | long random path, e.g. `/ops-8f2k9q` |
| `ADMIN_BASIC_USER` / `ADMIN_BASIC_PASSWORD` | strong, unique credentials |
| `ADMIN_EMAILS` | comma-separated emails allowed to use the admin APIs |
| `ANDROID_PACKAGE_NAME` | `app.rightconnect.twa` |
| `ANDROID_SHA256_FINGERPRINTS` | from Play Console → App signing (comma-separated) |

3. **Custom domain** (Settings → Custom Domains): add `rightconnect.app`, create the DNS records Render shows, wait for the certificate. Move the domain off the old service first if it is attached there.

## 3. Third-party settings

- **Razorpay** (Live mode): Settings → Webhooks → add `https://rightconnect.app/api/v1/payments/webhook`, event `payment_link.paid`, same secret as `RAZORPAY_WEBHOOK_SECRET`. Complete KYC before switching on live keys.
- **Resend**: verify the `rightconnect.app` sending domain (SPF/DKIM DNS records).
- **Admin account**: after you sign up once on production, make yourself admin in the SQL Editor:
  `UPDATE users SET role = 'platform_admin' WHERE email = 'you@example.com';` and include that email in `ADMIN_EMAILS`. The console is at `https://rightconnect.app<ADMIN_PATH>`.
- **Android app (TWA)**: `https://rightconnect.app/.well-known/assetlinks.json` must list the fingerprint once `ANDROID_SHA256_FINGERPRINTS` is set.

## 4. Moving existing data (optional)

Production normally starts empty. To copy real users from dev instead (needs `pg_dump`/`psql` 15+ locally; use the session pooler URLs, port 5432):

```bash
# 1. App data (public schema) – data only; the new project already has the schema.
pg_dump "$DEV_DB_URL" --data-only --schema=public --no-owner --disable-triggers -f public.sql
# 2. Logins, so existing users keep the same account ids.
pg_dump "$DEV_DB_URL" --data-only --table=auth.users --table=auth.identities --no-owner -f auth.sql
# 3. Load logins first, then app data.
psql "$PROD_DB_URL" -f auth.sql
psql "$PROD_DB_URL" -f public.sql
```

Afterwards everyone signs in once more (the new project issues new tokens). Remove seeded demo rows if dev ever ran `seed.sql`.

## 5. Check after go-live

- `https://rightconnect.app/api/v1/health` → `{"status":"ok"}`.
- `https://rightconnect.app/api/v1/health/db` responds in well under 300 ms (dev takes ~1.2 s).
- Google sign-in works and lands on the marketplace.
- Create a test request, chat, accept, mark done, rate.
- A ₹1 test payment (or Razorpay test mode on dev) activates Pro via the webhook.
- Admin console opens at `ADMIN_PATH` and asks for the Basic-auth password.
- In the browser console, `fetch('<SUPABASE_URL>/rest/v1/users?select=id', {headers:{apikey:'<publishable key>'}})` returns `[]` (RLS on).

## 6. Day-to-day workflow

- Branches: `main` → dev service (auto-deploy). `production` → prod service (auto-deploy). Release with `git checkout production && git merge main && git push`.
- **Database changes**: add a numbered file in `db/migrations/`, update `db/schema.sql` to match, run the migration on **dev first**, then on **prod before** merging to `production`. New ORM columns cause errors on every endpoint until their migration has run.
- Keep dev and prod secrets separate (different Supabase projects, Razorpay test vs live keys, different admin passwords).

## Other performance and reliability settings

| Setting | Why |
|---|---|
| Same region for Render + Supabase | Biggest single speed-up (round trip ~170 ms → ~1 ms). |
| Session pooler (5432) + `DB_STATEMENT_CACHE=true` | Reuses prepared statements: one round trip per query instead of two. |
| Render paid plan (no sleep) | Removes the 30–60 s cold start after idle time. On the free plan, an uptime pinger hitting `/api/v1/health` every 10 minutes does the same but uses free hours. |
| Supabase Pro | No 7-day pause, daily backups, more pooler connections. |
| Health check path `/api/v1/health` | Render only switches traffic to a new deploy once it is healthy (zero-downtime deploys). |
| Render log streams / alerts | Get notified about 5xx errors and failed deploys. |
