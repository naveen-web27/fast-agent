# 10. Backlog — Not Started

Status: ❌ Not started. These are referenced in [PRODUCT.md](../../PRODUCT.md) or implied by the schema but have no backend or frontend work yet.

## Saved Profiles / Comparison List — ✅ Completed (Sept 2026)

- `saved_profiles` table ([005_saved_profiles.sql](../../db/migrations/005_saved_profiles.sql)), `SavedProfile` model, and endpoints `POST/DELETE /api/v1/profiles/{id}/save` + `GET /api/v1/profiles/saved` (paginated).
- Frontend: Save/Unsave toggle on every profile card and the profile detail page; the "Saved" tab in [marketplace.html](../../frontend/pages/marketplace.html) now renders real bookmarked profiles instead of a static placeholder.

## Shareable Profile Links — ✅ Completed (Sept 2026)

- Opening a profile pushes `?profile=<id>` into the URL (`history.pushState`); loading that URL directly (e.g. shared after a YouTube mention) or hitting browser back/forward deep-links straight into the profile, unauthenticated.
- Added a "Copy profile link" button on the profile detail page.

## Interest-Based Recommendations

- `users.interests` is captured and editable, but nothing consumes it.
- Needed: `GET /recommendations?interests=...` or a `recommended_profiles` field on the future customer dashboard.

## Advanced Search Filtering

- Tracked in detail in [02-discover-marketplace.md](02-discover-marketplace.md) — service, language, experience range, rating, response time, availability filters.

## Dispute Resolution / Support

- No dispute model tied to requests or reviews.
- Needed: `POST /disputes`, `GET/PATCH /disputes/{id}` (admin), `GET /admin/disputes`.

## Analytics & Reporting

- No event logging (profile views, request funnel, completion rate).
- No `GET /expert/analytics`, `GET /customer/analytics`, `GET /organization/analytics`, or platform-wide admin analytics.

## Availability Scheduling

- Referenced in expert onboarding intent (PRODUCT.md) but no `availability` table/model/endpoints — needed before appointments can be auto-suggested.

## WhatsApp OTP Provider

- Tracked in [01-auth-onboarding.md](01-auth-onboarding.md) — no provider selected/integrated yet, UI is a stub.
