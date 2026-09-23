# RightConnect — Ad Video Script

Three cut lengths from the same story beats so you can pick what fits the platform (Instagram/YouTube Shorts/Reels = 15–30s, YouTube pre-roll/LinkedIn = 60s).

Brand voice: confident, warm, no-jargon. Colors on screen: navy `#101b31`, teal `#088a82`, mint `#8de8cd`/`#e5f6f2`, amber `#e3a315` (ratings), green `#17865a` (verified).

---

## 60-second version (full story)

| # | Time | Visual | On-screen text | Voiceover (VO) | SFX/Music |
| - | ---- | ------ | --------------- | -------------- | --------- |
| 1 | 0:00–0:05 | Person frustrated, scrolling endless search results / getting ghosted by a "contractor" on chat. Muted, slightly desaturated tone. | "Sound familiar?" | "Finding someone you can actually trust for the big stuff... shouldn't feel like a gamble." | Tense, low hum music starts |
| 2 | 0:05–0:10 | Screen wipes to navy background, RightConnect logo animates in (teal square, white R, mint plus badge). | "Meet RightConnect" | "Meet RightConnect — the marketplace where every expert and company is actually verified." | Music brightens, teal swell |
| 3 | 0:10–0:20 | Screen recording / UI mockup of the Discover page: search bar, profile cards with green "Verified" badge, amber star ratings, tags. | "Search. Compare. Trust." | "Search by service, city, or language. Compare real, verified experts and companies side by side — ratings, credentials, and reviews, all up front." | Upbeat, light plucky music |
| 4 | 0:20–0:30 | UI mockup of a profile detail page scrolling: bio, credentials, reviews list, "Request introduction" button being tapped. | "One tap to connect" | "Like what you see? Send a request in one tap, and they'll respond directly — no cold calls, no guesswork." | Click/tap SFX |
| 5 | 0:30–0:40 | Request workspace / timeline UI: message bubbles appearing, "Meeting booked" status chip turning green. | "Track it end to end" | "Track every conversation and booking in one shared timeline, from first message to completed job." | Notification chime |
| 6 | 0:40–0:48 | Split screen: happy customer + expert shaking hands (illustrated or stock-safe icon), 5-star review appearing with amber stars. | "Leave a verified review" | "And once it's done, leave a review that actually means something — because it's tied to a real, verified interaction." | Warm music swell |
| 7 | 0:48–0:55 | Cut to poster-style end card (reuse `poster/sales-poster.svg` composition): headline "Find Verified Pros You Can Actually Trust", CTA button, WhatsApp bar. | "Get Matched — It's Free" + WhatsApp number `+91 63825 95243` | "Stop guessing. Start connecting. Get matched with a verified pro today — totally free." | Music peaks |
| 8 | 0:55–0:60 | Logo lockup centered, tagline below, WhatsApp + web CTA fade in. | "RightConnect — Verified Experts. Zero Guesswork." | "RightConnect. Verified experts. Zero guesswork." | Music resolves, soft outro sting |

**CTA card copy (frame 7–8):** `Get Matched Free →` button, `Chat on WhatsApp +91 63825 95243`, `rightconnect.app`

---

## 30-second cut down

Use beats 1, 2, 3 (trimmed), 4 (trimmed), 7, 8.

1. **0:00–0:04** — "Finding someone you can trust for the big stuff shouldn't be a gamble." (frustrated scroll visual)
2. **0:04–0:08** — Logo reveal: "Meet RightConnect."
3. **0:08–0:16** — Discover UI: "Search, compare, and see verified experts and companies — ratings, credentials, reviews, all up front."
4. **0:16–0:22** — Profile → request tap: "Send a request in one tap. They respond directly. No cold calls."
5. **0:22–0:30** — End card: "Stop guessing. Start connecting. Get matched — it's free." + WhatsApp/website CTA.

---

## 15-second reel/short (punchy hook version)

1. **0:00–0:03** — Bold text slam on navy bg: **"Hiring a pro shouldn't feel like a coin flip."**
2. **0:03–0:06** — Quick UI flash: verified badge (green) + amber star rating zooming in.
3. **0:06–0:10** — Text: **"RightConnect verifies every expert & company — before you ever message them."**
4. **0:10–0:15** — End card: logo + **"Get matched free →"** + WhatsApp number, teal CTA button pulses once.

Caption/description copy: `Stop guessing. Start connecting. 🔗 Verified experts & companies, one trusted marketplace. Get matched free — link in bio.`

---

## Voiceover-only script (for recording)

> Finding someone you can trust for the big stuff shouldn't feel like a gamble.
> Meet RightConnect — the marketplace where every expert and company is actually verified.
> Search by service, city, or language. Compare real, verified profiles — ratings, credentials, and reviews, all up front.
> Like what you see? Send a request in one tap, and they'll respond directly — no cold calls, no guesswork.
> Track every conversation and booking in one shared timeline, from first message to completed job.
> And once it's done, leave a review that actually means something — because it's tied to a real, verified interaction.
> Stop guessing. Start connecting. Get matched with a verified pro today — totally free.
> RightConnect. Verified experts. Zero guesswork.

Estimated read time at a natural pace: ~48–55 seconds — pad with pauses/music swells to hit exactly 60s.

---

## Text-to-video AI prompt (Sora/Runway/Pika/Kling style tools)

Use this if generating b-roll/UI-motion clips instead of screen-recording the real app:

```
Clean, modern product demo animation for a professional services marketplace app
called RightConnect. Deep navy (#101b31) UI with teal (#088a82) accent buttons,
mint (#8de8cd) highlights, and amber (#e3a315) star ratings. Show a smooth mobile
screen-capture-style animation: a search bar filtering profile cards, each card
showing an avatar circle, a green "Verified" badge, star ratings, and a rounded
"Request" button being tapped, transitioning into a chat/timeline view with message
bubbles appearing. Minimal flat UI motion graphics, smooth easing, no real human
faces, no third-party logos, corporate SaaS aesthetic, 9:16 vertical, 15 seconds.
```

## Production notes

- If you don't have real app footage yet, mock the screens using the actual `frontend/pages/marketplace.html` in a browser and screen-record at 1080x1920 (mobile emulation) — it already matches these brand colors exactly.
- Keep on-screen text high-contrast (white/mint on navy) to match the poster for consistent branding across poster + video.
- WhatsApp number and "free" claim must stay consistent with whatever is live in-app at publish time (`WHATSAPP_NUMBER` in `marketplace.html`).
