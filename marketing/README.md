# RightConnect Marketing Assets

Marketing materials for RightConnect (trust marketplace for verified experts & companies). Brand colors and marks are pulled from the live product (`frontend/pages/marketplace.html` `:root` variables and `frontend/assets/rightconnect-mark.svg`) so everything stays on-brand.

| Folder | Contents |
| --- | --- |
| `poster/` | Ready-to-use social/sales poster (SVG, editable) + AI image-generation prompts for photo-realistic variants |
| `video/` | Ad video script (15s reel, 30s, 60s cuts) with shot list, voiceover, on-screen captions, and a text-to-video prompt |

## Brand quick reference

- Navy: `#101b31` / `#182844`
- Teal (primary CTA): `#088a82`
- Mint (accent bg): `#e5f6f2`
- Amber (ratings): `#e3a315`
- Success green: `#17865a`
- Ink/body text: `#172033`, muted: `#687386`
- Font stack used on the site: system UI sans-serif (e.g. `-apple-system, Inter, Segoe UI`)
- Tagline options: "Verified Experts. Zero Guesswork." / "Stop Guessing. Start Connecting."
- WhatsApp CTA number: `+91 63825 95243`

## How to use the poster

`poster/sales-poster.svg` is a 1080×1350 (Instagram feed/story friendly) vector poster you can:

- Open directly in a browser to preview.
- Open in Figma/Illustrator/Inkscape to tweak copy, then export PNG/JPG.
- Convert to PNG from the command line if you have `rsvg-convert` or `inkscape` installed, e.g.:

```bash
rsvg-convert -w 1080 -h 1350 marketing/poster/sales-poster.svg -o marketing/poster/sales-poster.png
```

If you'd rather generate a photo-realistic poster with an AI image tool (Midjourney, DALL·E, Stable Diffusion, Firefly, etc.), use the ready-made prompts in `poster/poster-prompt.md`.
