# the platform Retest Results — What the platform owner Fixed (Sep 2026)

After reporting 24 findings on the a dealer the platform staging build, the platform owner fixed
19 in a single pass. Track these so you know what a platform developer CAN fix
quickly vs what typically lags.

## Fixed immediately (19 of 24)

- Meta descriptions on all 9 page types (unique, descriptive, 150+ chars)
- Canonical tags on all pages
- Homepage title: "a dealer Car Sales Ltd | Used Cars Leeds, West Yorkshire"
- "HPI Cleaer" → "HPI Clear" (feed fix)
- robots.txt created (with AI bot allowances — ChatGPT, Claude, Perplexity)
- sitemap.xml created (returns 200)
- AutoDealer JSON-LD on homepage (Organization + AutoDealer + WebSite in @graph,
  with address, telephone, openingHoursSpecification, geo, sameAs, priceRange)
- Open Graph + Twitter Card tags on all pages
- Favicon (PNG + apple-touch-icon)
- Monthly finance figure replaced with "Finance available – ask for details"
  + representative example + "subject to status" + "credit broker, not a lender"
- Social media links made clickable (Facebook + Instagram)
- VDP spec fields expanded: now shows Year, Transmission, Fuel, Mileage, Body Type,
  Engine Size, Doors, Colour (8 items, up from 6 — Service History / Interior Trim
  with "N/A" removed)
- Server/X-Powered-By headers suppressed
- All 5 security headers added (X-Frame-Options, X-Content-Type-Options, CSP,
  Referrer-Policy, Permissions-Policy)
- Duplicate warranty phrase removed from feed
- "inquire" → "enquire" (UK spelling)
- VDP title improved: "Used Land Rover Discovery Sport for Sale | a dealer Car Sales Ltd"
- VDP JSON-LD enhanced: numberOfDoors, vehicleEngine, brand, vehicleModelDate added

## Still open after retest (5 of 24)

| # | Finding | Severity | Notes |
|---|---------|----------|-------|
| 4 | HTTP→HTTPS redirect | Critical | Staging-specific — live already has 301 |
| 11 | Missing colour on 8/12 vehicles | High | Feed mapping issue — still missing |
| 16 | GDPR consent on VDP enquiry + contact forms | Medium | Sell Your Car form has it; other two don't |
| 20 | "online.." double period | Low | Contact page still has double period |
| 23 | VDP H1 whitespace gap | Low | Extra spaces between make and model in raw HTML |
| 24 | Warranty provider not named | Low | Warranty page still doesn't name the underwriter |

## Items not in the platform owner's control (client/DSC)

| # | Finding | Owner | Notes |
|---|---------|-------|-------|
| 13 | Opening hours mismatch with AT | Client | Needs client to confirm correct hours |
| 14 | Directory NAP mismatch | DSC | Directory listing has wrong address + phone |

## Lessons for future the platform audits

1. **the platform developers can fix most SEO fundamentals in one pass** — meta descriptions,
   canonicals, OG tags, title tags, JSON-LD, favicon, robots.txt, sitemap, security
   headers are all within their control and were fixed promptly.
2. **Feed-level data issues (colour mapping, HPI text) may take a second round** —
   the colour feed mapping was NOT fixed in the first pass despite the HPI typo
   being fixed. Check feed-level issues separately after the platform fixes.
3. **GDPR consent checkboxes on forms are easily missed** — the Sell Your Car form
   had one but the VDP enquiry and contact forms didn't. This pattern repeats.
4. **Small content typos (double period, H1 whitespace) may persist** — these are
   template-level fixes that are easy to overlook. Flag them specifically.
5. **Staging-specific issues (HTTP redirect, server headers) resolve when deployed**
   — don't block a go-live on these if the live domain already has them.
