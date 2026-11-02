# RightConnect digital marketing: AI video production handoff

## What to make

The original campaign below uses separate ads for three audiences in two languages. For the founder-requested combined Tamil awareness ad, use [all-users-tamil.md](all-users-tamil.md): customer, expert, and company problems/solutions in one video, without onboarding instructions. It includes a longer master and a concise alternative. The planned homepage guide/app tour is separate and must not be advertised as available until published.

| Audience | Tamil script | English script | Primary action |
| --- | --- | --- | --- |
| Customers looking for services | [customers-tamil.md](customers-tamil.md) | [customers-english.md](customers-english.md) | Explore the marketplace |
| Independent experts offering services | [experts-tamil.md](experts-tamil.md) | [experts-english.md](experts-english.md) | Create an expert profile |
| Companies offering services | [companies-tamil.md](companies-tamil.md) | [companies-english.md](companies-english.md) | Add a company profile |

Each script includes a 30-second storyboard, a 15-second cut, alternative hooks, caption copy, and a visual-generation prompt. Tamil scripts include Tamil-script voiceover plus a Tanglish pronunciation reference. Record the Tamil version in conversational Tamil, not as an English ad translated word for word.

## Recommended creative direction

**Customers:** "I need help, but whom should I approach?"

**Experts:** "People should be able to understand what I do before they contact me."

**Companies:** "Help potential customers understand our services and start an enquiry."

Sell the next useful action, not an outcome we cannot guarantee. Prefer "find the right help for your business" over "grow your business instantly." The founder's customer hook becomes:

> "உங்க business-க்கு help வேணுமா? Insurance பத்தி விளக்கம் வேணுமா? அதுக்கான experts, companies-ஐ எங்கே தேடுறதுன்னு யோசிக்கிறீங்களா?"

Insurance is an optional category-specific variation, not the theme of every campaign. Use it only when the advertised market has suitable, legally authorized providers.

## Production specification

- Master format: vertical 9:16, 1080 x 1920. Supply an optional 4:5 crop for feed placements.
- Produce one approximately 30-second master and one approximately 15-second cut per audience/language: **12 finished videos**.
- Timings are editing targets, not verified voiceover durations. Record first, check pronunciation, and trim copy or extend to 35 seconds rather than rushing.
- Start the problem/hook immediately. Show the RightConnect name within the first 5 seconds and keep the website visible on the final card for about 3 seconds.
- Use one clear CTA per ad. Say "Open rightconnect.app" rather than telling everyone to install an app.
- Provide burned-in captions and a clean master without captions, plus separate `.srt`, voiceover, music, and editable project files.
- Add captions, URLs, and logos in an editor. Do not ask a video model to generate readable Tamil, accurate product screens, or the brand mark.
- Keep essential captions and CTAs clear of platform controls; check each platform's current safe-area preview before export.
- Use original or licensed music, footage, and voices. Do not clone a real person's voice or likeness without permission. Follow the ad platform's applicable synthetic-media disclosure rules.
- Use adults in everyday Tamil Nadu/Indian professional settings. Avoid luxury-success montages, cash showers, staged testimonials, or exaggerated before/after results.
- Tamil VO: warm, natural spoken Tamil with familiar English words such as "business," "profile," and "service." Tanglish text is a recording guide, not the subtitle track.
- English VO: friendly Indian English, clear and conversational, not a hard-sell announcer.
- Pronounce RightConnect as **"Right Connect"**, two words. Say the website as **"right connect dot app."**

## Brand and product footage

- Navy: `#101b31`; teal: `#088a82`; mint: `#e5f6f2`; amber: `#e3a315`.
- Use the original [RightConnect mark](../../frontend/assets/rightconnect-mark.svg). Do not redraw it with AI.
- Record the actual [marketplace](../../frontend/pages/marketplace.html), [intro page](../../frontend/index.html), and [auth flow](../../frontend/pages/auth.html) from a release-approved environment.
- In the delivered creative, show only approved demonstration accounts. Hide emails, phone numbers, request messages, payment details, browser tokens, and other personal information.
- Do not invent ratings, reviews, verification badges, customer counts, appointments, or success notifications. A real feature shown with clearly marked demo content is acceptable; a fabricated testimonial is not.
- Use screen recordings for the UI shots in each storyboard. AI-generated b-roll should contain no legible phone screens.

## Release and claims checklist

These are creative drafts based on repository features, **not confirmation that every feature, service category, or provider is live**.

Before spending on ads:

1. Confirm `https://rightconnect.app` and all ad destinations work on mobile.
2. Confirm advertised categories have real, available providers in the target market. If not, narrow the ad or run an explicitly labeled early-access/provider-onboarding campaign instead.
3. Test Google sign-in, provider onboarding, marketplace discovery, and the request acceptance/chat flow.
4. For video-showcase shots, verify the showcase migration is applied and publishing works in the live environment. Otherwise omit those optional shots and sentences.
5. Free showcase allowance is **2 per profile**; **10 requires that profile's active Pro or Enterprise plan**. Do not call all provider tools free or invent subscription prices.
6. Do not say "every provider is verified," "guaranteed customers," "instant replies," "guaranteed business growth," "best insurance," "zero risk," or "100% trusted."
7. Showing verification details or reviews is conditional on what exists on that profile. Do not imply that watching a provider's Reel verifies their service quality.
8. Do not imply immediate chat/contact disclosure: customers send a request, and the provider must accept before the request conversation/contact flow proceeds.
9. For insurance-themed ads, do not claim RightConnect sells, recommends, underwrites, or guarantees an insurance policy. Have the relevant advertiser review applicable licensing and ad requirements.
10. Customers can use the website without installing anything. An Android APK is optional; do not imply an iPhone native app or Google Play listing is available.

These six scripts are the current handoff for this campaign. Do not copy stronger claims from older marketing drafts without checking them against this checklist.

## Distribution and measurement suggestions

- First, recruit enough experts/companies in **one category and region** to make customer discovery useful. A provider-onboarding ad should not imply there is already strong customer demand.
- Run customer, expert, and company ads separately, each in Tamil and English. Choose audience/creative based on actual regional fit, not assumptions that every business needs the same service.
- Start by testing two hooks per audience while keeping the remaining video and destination unchanged. Use comparable spend and sufficient observation time; do not declare a winner from a handful of clicks.
- Customer success metric: relevant introduction requests, not only views or account registrations.
- Expert success metric: completed expert profiles with clear service details, not only sign-ups.
- Company success metric: completed company profiles and appropriate enquiry handling, not only page visits.
- Track with distinct UTM links, and verify analytics captures them before launching:
  - Customer Tamil: `https://rightconnect.app/pages/marketplace.html?utm_source=instagram&utm_medium=paid_social&utm_campaign=customers_tamil&utm_content=hook_a`
  - Expert English: `https://rightconnect.app/pages/auth.html?utm_source=instagram&utm_medium=paid_social&utm_campaign=experts_english&utm_content=hook_a`
  - Company Tamil: `https://rightconnect.app/pages/auth.html?utm_source=instagram&utm_medium=paid_social&utm_campaign=companies_tamil&utm_content=hook_a`
- The expert/company links open the shared onboarding page, not an automatic role-specific account. Show the actual role/setup steps in the recording.

## Naming the exports

Use names such as `rightconnect_customers_tamil_30s_hook-a_v1.mp4` and `rightconnect_companies_english_15s_hook-b_v1.mp4`.

Deliver a contact sheet with audience, language, hook, length, CTA, destination URL, and approval status for every export.
