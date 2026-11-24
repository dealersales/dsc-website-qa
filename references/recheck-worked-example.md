# the dealer group live QA re-verification — worked example

Full worked example of a live-site re-verification pass (Sep 2026), the
companion to `raw-html-recheck-patterns.md`. Client status from the DSC roster:
"QA complete on live site; open: MOT term contradiction, duplicate copyright,
Burnley meta tags" — the task was to re-check those three open items plus look
for anything new.

## Outcome summary

| Open item | Result on re-check |
|---|---|
| MOT term contradiction | **STILL OPEN** — home + about say "minimum of 6 months MOT"; servicing page + its meta description say "complimentary full 12 months MOT"; vehicle detail pages say "fresh 12-month MOT" |
| Duplicate copyright | **RESOLVED** — exactly one `© 2026 the dealer group Wakefield. All rights reserved.` per page (raw count = 1 on all pages incl. detail pages) |
| Burnley meta tags | **RESOLVED** — zero "burnley" hits anywhere; all titles/descriptions reference Wakefield |

New findings surfaced on the same pass:

- US spelling "Specializing / Specializes / specialize" site-wide — homepage body
  (x2), about body, and a shared header/JSON-LD sentence on every inner page
  (one template fix cures the site, but homepage/about body copy is separate).
- Grammar: "use us **in anyway**" → "in any way" (About page).
- Vehicle detail pages carry generic `<title>Vehicle Details - ...</title>` and
  the homepage meta description on every car — Medium SEO finding; each car
  needs its own title/description from make/model/price.

## Technique notes

- The contradiction only appears when claims are TABULATED across pages —
  single-page reads miss it. Extract every MOT/6-month/12-month phrase per page,
  then compare rows.
- Detail pages differ from listing pages: check at least 2 vehicle detail URLs
  (they carry the "fresh 12-month MOT" claim and the generic-title problem).
- `/cars` and `/cars.php` both serve the listing with self-canonicals — benign,
  not duplicate content.
- Phone/NAP: the new number was on every page EXCEPT one stale warranty-page
  block — always grep every downloaded page for all number formats
  (`tel:`, `wa.me/44…`, spaced/compact/E.164), not just the homepage footer.
