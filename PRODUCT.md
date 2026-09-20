# RightConnect

RightConnect is a trust marketplace for complex purchases. Customers discover verified experts and companies, compare credible signals, and coordinate a guided introduction before choosing a provider.

## Product Roles

### Customer

- Search by service, location, language, availability, and trust signals.
- Compare independent experts and companies.
- Request an introduction, consultation, or quote.
- Track each request, appointment, and outcome.
- Leave a review only after a verified interaction.

### Expert

- Publish a profile with services, experience, languages, coverage area, credentials, social links, and availability.
- Receive suitable customer requests.
- Accept, decline, or propose a meeting time.
- Build a reputation through verified outcomes and customer reviews.

### Company

- Publish a company profile and service catalogue.
- Manage team members, enquiries, and partner experts.
- Respond to qualified requests and keep the customer informed.

### Platform Admin

- Verify identity, credentials, and business information.
- Moderate profiles and reviews.
- Resolve disputes and prevent misleading claims.

## First Release Pages

1. Discover: search and compare verified experts and companies.
2. Profile: experience, evidence, reviews, service fit, and introduction request.
3. Request workspace: customer, expert, and company coordination in one timeline.
4. Customer dashboard: active requests, saved profiles, appointments, and reviews.
5. Expert dashboard: incoming leads, availability, profile completion, and reviews.
6. Company dashboard: request pipeline, team, and response quality.
7. Admin verification: applications, evidence checks, and review moderation.

## Authentication And Onboarding

Every person first authenticates with Google or a WhatsApp one-time code, then completes the minimum form for their role.

### Customer

- Authenticate with Google or a WhatsApp code.
- Provide display name, city, and preferred language.
- Immediately search, save profiles, request an introduction, and review completed interactions.

### Expert

- Authenticate with Google or a WhatsApp code.
- Provide professional name, service category, location, languages, years of experience, and short introduction.
- Add credential details, professional links, and availability.
- Profile remains pending until an admin verifies submitted evidence.

### Company

- Authenticate as an authorized representative.
- Provide company name, business email, website, service category, operating locations, and representative contact.
- Add business registration or relevant licences for verification.
- Organization stays pending until the business evidence is reviewed.

### Production Authentication Choice

Use Supabase Auth for the first production release:

- Enable Google OAuth for the Google button.
- Implement WhatsApp code delivery through an approved WhatsApp provider or a custom OTP service; Supabase does not natively send WhatsApp OTPs.
- Validate OTPs server-side, rate-limit requests, and never accept a code only in the browser.
- Store the selected role and onboarding state in PostgreSQL after verified authentication.

## Trust Model

Profiles should never rank only by followers. The initial trust score uses verified customer interactions, completed outcomes, response quality, verified credentials, and social proof. Social and YouTube links are supporting evidence, not a substitute for verified service quality.

## Interaction Flow

1. Customer describes a need.
2. RightConnect suggests verified experts and companies.
3. Customer chooses a profile or asks RightConnect to match one.
4. The selected expert/company accepts the request.
5. Everyone sees the request timeline, notes, and booked consultation.
6. The customer confirms an outcome and leaves a verified review.

## Visual Direction

The product uses an original work-focused interface: a deep navy navigation rail, calm white content surfaces, teal primary actions, amber rating details, and green verification status. It takes broad inspiration from modern SaaS clarity, not from third-party markup, assets, or copy.

## Data Plan

Use PostgreSQL through Supabase or Neon for the production prototype. The first schema should contain users, profiles, organizations, services, credentials, social_links, requests, request_participants, appointments, reviews, and verification_checks.