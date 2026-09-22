# 10. Backlog — Not Started

Status: ❌ Not started. These are referenced in [PRODUCT.md](../../PRODUCT.md) or implied by the schema but have no backend or frontend work yet.

## Saved Profiles / Comparison List

- No table (`user_saved_profiles` needed: `user_id`, `profile_id`, `created_at`, unique pair).
- Frontend already has an empty placeholder view in [marketplace.html](../../frontend/pages/marketplace.html) ("Your comparison list will live here").
- Needed: `POST /profiles/{id}/save`, `DELETE /profiles/{id}/save`, `GET /me/saved-profiles`.

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
