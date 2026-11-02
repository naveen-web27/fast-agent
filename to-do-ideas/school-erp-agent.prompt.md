---
description: Build a multi-school Student Management System (FastAPI + Postgres on Render) with a marketing website, low-cost SMS, and blueprints for WhatsApp and Facility Management.
agent: agent
---

# Role

You are the lead engineer for a new SaaS product: a **Student Management System (school/college ERP)** for Indian educational institutions, starting with private schools and tuition centres in Tamil Nadu. Product name: **KalviKendra** (tagline: "School management + low-cost SMS"; keep the brand name, colours, prices, and contact details in ONE config file so they can be changed later).

Build it milestone by milestone. After each milestone: run the checks, fix errors, and give a short summary of what was built and what is next. Do not commit or push unless I ask. Never put secrets in files, logs, or messages.

# Product positioning (use this everywhere: website copy, README, UX decisions)

1. **Lowest-cost SMS for schools** — our main selling point. Schools buy SMS credits from us at a low price (we buy wholesale DLT-registered SMS and resell). Absence alerts, fee reminders, receipts, exam results, circulars.
2. **Simple** — a school can go live in one day by uploading its existing Excel sheets. Short labels, one question per screen for long forms, works on cheap Android phones.
3. **Tamil + English** from day one (i18n in both the website and the app).
4. **Fees first** — online fee collection (Razorpay), receipts, dues tracking; this is where institutions see value.
5. **Coming soon (show on website, design for it now, do not build yet):**
   - **WhatsApp alerts** (see blueprint below).
   - **Student Facility Management** — hostel, transport/bus, library, labs/room booking, inventory/assets, maintenance requests, canteen.

# Tech stack and hosting

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy 2.x, asyncpg, Pydantic v2, pytest.
- **Database:** PostgreSQL on Supabase. Plain SQL files: `db/schema.sql` (full current schema for a fresh DB) + `db/migrations/NNN_name.sql` (incremental). Every ORM column change needs a migration. `db/seed.sql` is dev-only demo data.
- **Auth:** Supabase Auth. Staff: email/password or Google. Parents/students: phone OTP (use Supabase "Send SMS Hook" pointing to our own SMS adapter, so OTP goes through our SMS provider).
- **App frontend (staff/parent/student):** React + Vite + TypeScript, a component library (Mantine or shadcn/ui), react-router, TanStack Query. Installable PWA (manifest + service worker) so parents can "Add to Home screen".
- **Marketing website:** static HTML + CSS + minimal vanilla JS (fast, SEO-friendly), in `web/`.
- **Hosting on Render:** `render.yaml` with
  - `api` — Python web service (uvicorn), health check `/health`.
  - `site` — static site publishing `web/` at `/` and the built React app at `/app/`.
  - Background jobs: a Postgres-backed `jobs` table processed by an asyncio worker started in FastAPI lifespan (single instance, free tier friendly). Keep the worker code separable so it can move to a Render Background Worker later.
- **Region:** put Render and Supabase in the **same region** (Singapore `ap-southeast-1` for both). Cross-region DB round trips make every request slow.
- **DB connection:** small pool with `pool_pre_ping`, `pool_recycle=300`. With Supabase transaction pooler (port 6543) disable asyncpg prepared statement cache (`statement_cache_size=0`); allow enabling it via env `DB_STATEMENT_CACHE=true` only for session pooler (5432) or direct connections.

# Repository layout

```
backend/
  app/
    main.py
    core/          # config (pydantic-settings), logging, errors, i18n helpers, money (paise), phone (E.164)
    db/            # engine/session, tenant-scoped session dependency
    security/      # Supabase JWT verification, current user, role/permission checks
    tenancy/       # tenant resolution + guards
    features/
      <module>/    # router.py, schemas.py, service.py, models.py — one folder per module
  tests/
  requirements.txt
app/               # React + Vite staff/parent/student app
web/               # marketing website (static)
db/schema.sql, db/migrations/, db/seed.sql
docs/              # DEPLOYMENT.md, features/*.md, blueprints/*.md
render.yaml
.github/copilot-instructions.md
.gitignore         # include __pycache__/, *.pyc, .env, node_modules/, dist/
```

Create `.github/copilot-instructions.md` for this repo with the stack, commands, conventions, and the rules in this prompt (short bullet list).

# Multi-tenancy (one shared system, many schools)

- Table `tenants` (institution): id, name, slug, type (`school|college|coaching`), board (`state|cbse|icse|other`), city, logo_url, sms_sender_mode, plan, status, created_at, deleted_at.
- **Every tenant-owned table has `tenant_id UUID NOT NULL`** + index starting with `tenant_id`.
- Tenant is resolved from the logged-in user's membership (`tenant_members`: tenant_id, user_id, role). A user can belong to several tenants and switch between them (header `X-Tenant-Id`, validated against membership). Subdomains (`school.kalvikendra.in`) can come later.
- **Two layers of isolation:**
  1. Application: every query goes through a tenant-scoped service helper that always filters by `tenant_id`.
  2. Database: RLS on every tenant table with policy `tenant_id = current_setting('app.tenant_id')::uuid`; the API runs `SET LOCAL app.tenant_id = ...` per transaction. Connect as a dedicated non-owner role without `BYPASSRLS`, and use `FORCE ROW LEVEL SECURITY`.
- Write pytest tests proving School A can never read or modify School B data.
- Design so a large customer can later get a **dedicated database** from the same code (tenant row stores an optional `database_url_secret_name`; default = shared DB). Do not build this now.

# Roles and permissions (per tenant)

`owner`, `principal`, `admin`, `accountant`, `teacher`, `parent`, `student`, plus platform-level `platform_admin`.
Use a permission matrix in code (e.g. `fees.collect`, `attendance.mark`, `students.edit`, `sms.send`, `reports.view`). Teachers only see their assigned sections/subjects. Parents only see their own children. Students only see themselves.

# Data rules

- Money as integer **paise**. Never floats.
- Phone numbers normalised to E.164 (`+91...`).
- Dates/times stored UTC; displayed in IST.
- **Academic year** on all academic data (enrollments, attendance, fees, exams). Year rollover/promotion is a feature.
- **Soft delete** (`deleted_at`) for students, staff, guardians, tenants; unique indexes are partial `WHERE deleted_at IS NULL`.
- **Audit log** table for sensitive actions (fee edits, concessions, mark changes, deletes, exports): who, what, before/after, when.
- Avoid N+1 queries: batch-load related rows with `IN (...)` queries; list endpoints paginate.
- Children's data: India DPDP Act 2023 — record guardian consent (`consents` table: guardian, purpose, timestamp, version), minimal data collection, data export per tenant, privacy policy page.

# Core data model (MVP)

`tenants`, `tenant_members`, `users`, `academic_years`, `campuses`, `classes` (or `programs` for colleges), `sections`, `subjects`, `section_subjects` (with teacher), `students`, `guardians`, `student_guardians`, `enrollments` (student × section × academic_year, roll_no), `staff`, `attendance_sessions`, `attendance_records`, `fee_heads`, `fee_structures`, `fee_structure_items`, `student_fee_assignments` (with concessions), `fee_invoices`, `fee_payments`, `receipts` (per-tenant sequential numbers), `exams`, `exam_subjects`, `marks`, `grade_scales`, `notices`, `homework`, `documents` (Supabase Storage paths), `consents`, `audit_log`, `jobs`, plus SMS tables below, plus `leads` (website demo requests, not tenant-scoped).

# Milestones

## M1 — Foundation
- Repo layout, config, `/health` and `/health/db`, Supabase JWT auth, tenants + membership, roles/permissions, RLS, tenant isolation tests, `render.yaml`, `docs/DEPLOYMENT.md` (env vars, regions, migration order: dev first then prod).
- Platform admin console (behind a secret path + HTTP Basic + email allowlist) to create a tenant and invite its owner.

## M2 — Marketing website (`web/`)
See "Website" section below. Include the demo-request form → `POST /api/v1/leads` (honeypot field + per-IP rate limit + server-side validation), stored in `leads`, optional email notification.

## M3 — School setup + Students
- Onboarding wizard: academic year, classes, sections, subjects, fee heads.
- **Excel/CSV bulk import** for students + guardians (downloadable template, preview with row-level errors before commit, idempotent re-import).
- Student profile (photo, documents, guardians), auto roll numbers, ID card PDF, search/filter, promotion to next year, transfer certificate PDF.

## M4 — Attendance
- Daily (school) and period/subject-wise (college) attendance; "mark all present, tap absentees" quick UI; works with weak network (queue in the PWA and sync later).
- Reports: daily/monthly/percentage per student and section.
- On submit, enqueue absence alerts to guardians through the notification service (SMS).

## M5 — Fees + Razorpay
- Fee structures per class, installments with due dates, concessions/scholarships, late fees.
- Collect offline (cash/UPI/cheque by accountant) and online (Razorpay Standard Checkout for parents, server-side signature verification + webhook, idempotent).
- Auto receipts (PDF), dues list, collection reports by day/class/head, reminders via SMS.

## M6 — Low-cost SMS (main feature)
See "SMS module" section below.

## M7 — Parent / Student app
- Children switcher, attendance calendar, fees due + pay, receipts, homework, notices, exam results, timetable.
- Push notifications (Web Push) as a free channel in addition to SMS.

## M8 — Exams, report cards, homework, notices, timetable
- Exams, marks entry grid, grade scales (State board / CBSE patterns), report card PDF templates, homework, circulars with read status, basic timetable.

## M9 — Dashboards
- Owner/principal: students, today's attendance %, fee collected vs due, SMS balance.
- Teacher: today's classes, attendance pending, homework.

# SMS module (build in M6)

- **Notification service** with a channel interface: `send(channel, tenant_id, recipient, template_key, variables)`. Channels: `sms`, `push`, `email`; `whatsapp` is defined but disabled (see blueprint).
- **Outbox table `messages`:** tenant_id, channel, recipient, template_key, variables JSON, rendered_text, segments, cost_paise, status (`queued|sent|delivered|failed`), provider, provider_message_id, error, attempts, created_at, sent_at, delivered_at. Sending happens in the background worker with retries and backoff.
- **Provider adapter** `SmsProvider` with `ConsoleSmsProvider` (dev: logs instead of sending) and one real Indian DLT-compliant provider adapter (choose via env `SMS_PROVIDER`; keep API keys only in env). Delivery-report webhook endpoint updates message status (verify webhook auth).
- **India DLT compliance:** the platform registers as the Principal Entity with its own sender ID (header) and templates. Store `dlt_entity_id`, `sender_id`, and per-template `dlt_template_id` in `sms_templates`. Templates use variables; the school name is a variable (e.g. "{school}: {student} was absent on {date}."). Option later: a school's own sender ID (`tenants.sms_sender_mode`).
- **Segments and cost:** GSM-7 = 160 chars (153 per part when multi-part); Unicode (Tamil) = 70 chars (67 per part). Count segments before sending and show the cost preview to the user. Unit tests for segment counting in English and Tamil.
- **Prepaid wallet per tenant:** `sms_wallets` (balance in credits) and append-only `sms_ledger` (purchase, debit, refund-on-failure, admin adjustment). Debit is reserved when queued and refunded if the provider fails. Block sending when balance is insufficient.
- **Buying credits:** SMS packs via Razorpay; platform admin sets pack prices and per-SMS price (configurable, no hardcoded rates).
- **Rules:** transactional messages only for MVP; respect TRAI timing rules for any promotional content; guardian opt-out per category; rate limit per tenant; never log full phone numbers in plain logs.
- **UI:** SMS balance + buy credits, send to class/section/all/defaulters with preview (recipients count, segments, cost), message history with delivery status, monthly usage report.

# Blueprint only — WhatsApp (do NOT implement; write `docs/blueprints/whatsapp.md` and leave hooks)

- One platform WhatsApp Business number via Meta WhatsApp Cloud API (direct, no BSP markup); the platform company does Meta Business verification once; schools do nothing. Optional premium: school's own number via Meta Embedded Signup.
- Utility templates (absence, fee due, receipt, results) approved by Meta; school name is a template variable.
- Reuse the same notification service, `messages` outbox, templates table (add `whatsapp_template_name`), wallet/ledger (WhatsApp priced per message), delivery/read webhooks, opt-in tracking.
- Fallback order per guardian preference: WhatsApp → SMS → push.
- Code hooks now: `whatsapp` channel enum value, disabled adapter raising "not enabled", feature flag `WHATSAPP_ENABLED=false`.

# Blueprint only — Student Facility Management (do NOT implement; write `docs/blueprints/facility-management.md`)

Modules: hostel (rooms, beds, allocation, hostel fees, in/out log), transport (routes, stops, vehicles, drivers, student-stop mapping, transport fees, later GPS), library (catalogue, issue/return, fines), labs/rooms booking, inventory/assets (stock, issue, depreciation), maintenance tickets (raise, assign, resolve), canteen (menu, prepaid wallet). Design them as new `features/<module>/` folders that reuse tenants, roles, fees (fee heads), notifications, and audit log. Note which existing tables they depend on.

# Website (`web/`) — attractive, original, fast

Reference for structure only: https://www.vidyalayaschoolsoftware.com/about/student-management-software — **do not copy its text, images, logos, or design assets.** Write original copy.

**Pages:** `index.html`, `features.html`, `sms.html`, `pricing.html`, `facility-management.html` (Coming soon), `about.html`, `contact.html` (demo form), `privacy.html`, `terms.html`, `refund.html` (Razorpay requires privacy/terms/refund pages).

**Home page sections:**
1. Hero: clear headline about simple, low-cost school management with the cheapest SMS; sub-headline; CTAs "Book a free demo" and "See pricing"; app screenshot/mockup (build with HTML/CSS or simple SVG — no stock images we don't own).
2. "Go live in one day" — 3 steps: share your Excel → we set up → parents get alerts.
3. **Low-cost SMS spotlight** with an interactive cost calculator (students × messages per month × per-SMS price from config) and Tamil + English sample messages.
4. Modules grid with icons (inline SVG): Admissions, Students, Attendance, Fees & Online Payments, Exams & Report Cards, Homework, Notices, Timetable, Certificates, Dashboards, Parent App, SMS.
5. Benefits by role (tabs): Management, Office/Accounts, Teachers, Parents, Students.
6. Parent app showcase (PWA, works on any Android phone).
7. Security & privacy: role-based access, separate data per school, daily backups, DPDP-ready consent.
8. Coming soon: WhatsApp alerts, Student Facility Management (hostel, transport, library, inventory, maintenance).
9. Pricing preview (values from config; show placeholders like "₹— per student / year" if not set — never invent numbers).
10. FAQ (accordion).
11. Demo request form + footer (contact from config).

**Rules:**
- No fake testimonials, customer logos, awards, or statistics. Use clearly marked placeholders until real ones exist.
- English + Tamil toggle (stored in localStorage; `lang` attribute updated).
- Mobile-first, responsive, accessible (semantic HTML, labels, contrast, keyboard navigation, `prefers-reduced-motion`).
- Performance: no heavy frameworks, inline critical CSS, lazy-load below-the-fold media, Lighthouse ≥ 90 in all categories.
- SEO: unique `<title>`/meta description per page, Open Graph tags, `sitemap.xml`, `robots.txt`, JSON-LD `SoftwareApplication` + `Organization`.
- Modern, friendly look: one primary colour + one accent from the brand config, generous spacing, rounded cards, subtle scroll animations.

# Security checklist (apply throughout)

- Validate all input with Pydantic; parameterised queries only.
- Authorisation check on every endpoint (tenant + role + ownership).
- File uploads: size/type limits, private storage buckets, signed URLs.
- Razorpay and SMS webhooks: verify signatures; idempotent processing.
- CORS allowlist from env; secure headers; rate limiting on auth, OTP, leads, and SMS send.
- No secrets, tokens, or full phone numbers in logs or responses.

# Checks after every milestone

- `python3 -m py_compile` on touched Python files, `pytest` for backend tests.
- `npm run build` and `npm run lint` for `app/`.
- HTML validity and broken-link check for `web/`.
- Update `db/schema.sql` **and** add a migration for any schema change.
- Update `docs/features/<module>.md` with status (built / partial / planned) and endpoints.

Start with **M1** and **M2**. Before writing code, show me the planned file list and the database tables for M1, then proceed.
