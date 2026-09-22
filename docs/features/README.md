# RightConnect — Feature Workflow Status

This folder documents, per product feature, the intended workflow and the current build status: what is completed, what is partially done, and what remains to be built. It is generated from the actual backend routers/models/schemas and frontend pages in this repo (not just the product spec in [PRODUCT.md](../../PRODUCT.md)).

Legend: ✅ Done · 🟡 Partial · ❌ Not started

## Status At A Glance

| # | Feature Area | Status | Doc |
|---|---|---|---|
| 1 | Authentication & Onboarding (Google, WhatsApp OTP, multi-role) | 🟡 Partial (Google done, WhatsApp stub) | [01-auth-onboarding.md](01-auth-onboarding.md) |
| 2 | Discover / Marketplace search | 🟡 Partial (basic search, filters missing) | [02-discover-marketplace.md](02-discover-marketplace.md) |
| 3 | Request Workspace (timeline, accept, appointments) | 🟡 Partial (messaging done, appointments not wired) | [03-request-workspace.md](03-request-workspace.md) |
| 4 | Reviews & Trust Model | 🟡 Partial (create/display done, moderation missing) | [04-reviews-trust.md](04-reviews-trust.md) |
| 5 | Admin Verification Console | 🟡 Partial (profiles only; credentials/reviews not covered) | [05-admin-verification.md](05-admin-verification.md) |
| 6 | Company Features (registration, domain OTP, team) | 🟡 Partial (registration + domain OTP done, team mgmt missing) | [06-company-features.md](06-company-features.md) |
| 7 | Expert Profiles | 🟡 Partial (create done, edit/credentials missing) | [07-expert-profiles.md](07-expert-profiles.md) |
| 8 | Customer / Expert / Company Dashboards | ❌ Not started (no dedicated endpoints/pages) | [08-dashboards.md](08-dashboards.md) |
| 9 | Notifications & Billing | ❌ Not started (only OTP emails exist) | [09-notifications-billing.md](09-notifications-billing.md) |
| 10 | Backlog: saved profiles, disputes, analytics, recommendations | ❌ Not started | [10-backlog.md](10-backlog.md) |

## How To Use These Docs

- Each doc has: **Workflow** (mermaid diagram of the intended end-to-end flow), **Completed** (concrete evidence — endpoints, models, files), **Not Done / To Do** (concrete gaps with suggested endpoints), and **Status**.
- When a gap is closed, move the item from "To Do" to "Completed" in the same edit and update the status table above.
- Source of truth for evidence: `backend/app/features/*`, `backend/app/models/*`, `db/schema.sql`, `db/migrations/*`, `frontend/pages/*`.
