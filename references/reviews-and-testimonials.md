# Dealer reviews and testimonial content

Review pages are the highest-risk block on a dealer site. They are cheap to fill with something
plausible, they carry a compliance consequence, and the client cannot tell good from bad by looking.

## Rule 1 — a review exists only because a customer wrote it

Two mechanisms publish invented reviews, and the second is the one that hides:

1. A bundled array in the theme (`get_reviews()` returning six hand-written entries badged
   "Verified Buyer").
2. **A page that calls the review API correctly and then falls back to that array when it comes back
   empty.** This is the dangerous shape: the integration looks right in code review, the API is
   wired, and the fabricated set publishes precisely when there are no real reviews to show — i.e.
   at launch, when every page is being checked.

Check both. `grep -rn "Verified Buyer\|testimonial" --include='*.php'` and then fetch the endpoint
by hand to see what it actually returns (`No data` counts as empty). If the site renders reviews and
the endpoint returns nothing, the reviews are invented.

Delete the fallback and the array. Render an empty state that says the dealer is collecting reviews
and links to the profile. An empty page is a design problem; a fabricated page is a misleading
commercial practice under the DMCC 2024 and cannot be argued as an oversight.

## Rule 2 — a vendor's "example payload" is content, not a schema

Platform review managers (the platform's included) can seed demo reviews: generic forename+surname pairs,
all five stars, generic cars, template comments. Copying one as your test fixture is fine; copying
the *structure* without reading the content is how a fabricated set reaches production — and at
least one seed set named a real person connected to the account, which removes any "anonymised
demo data" defence.

When a vendor offers a payload "to code against", read every row before you code against it, and say
so if it looks fabricated. The same seed data is then a launch risk for the next dealer who switches
the manager on.

## Rule 3 — source from the Google profile, filter to the good ones, label the selection

The profile is the preferred source: real customers, dated, attributable. Pull verbatim — do not
paraphrase or tidy a review's wording.

Publishing only good reviews is normal practice and acceptable **provided the page does not imply it
is the whole set**. The defensible shape:

- A minimum-rating threshold in config (`REVIEW_MIN_RATING = 4`), so the threshold is a decision the
dealer can change, not a magic number in a template function.
- The block is labelled as a selection: "a selection of the reviews our customers have left".
- A link to the full profile sits with the reviews, saying plainly that every review — including any
  not shown — can be read there.

A five-star-only wall with no route to the rest is a misleading commercial practice. The link is the
thing that makes the filter legitimate, not a courtesy.

## Rule 4 — mirror the feed's record shape

Typical payload: `{"name", "vehicle", "rating", "comment"}` — no date, no id, no source URL. Two
consequences:

- Render `name · vehicle · date` as the byline, not the name as the headline and the vehicle as the
  byline (the usual template mistake).
- If the feed has no date and no source, say where the reviews come from in the section copy instead;
  a review you cannot attribute or date is close to the thing Rule 1 forbids.

Normalise defensively: unknown rating shape, empty name, non-array payload, `No data` string, and
unreachable endpoint all resolve to "no reviews" rather than an exception. Prefer a stale cache over
an invention.

## Rule 5 — do not expect star snippets from self-serving markup

`AggregateRating`/`Review` markup on a business's own review page is self-serving and not eligible
for star review snippets in Google results. Do not add it as an SEO fix, and do not report its
absence as a finding.

## Verification

- Parse a real payload from a *different* dealer to prove the mapping, without publishing it.
- Assert the empty state against `No data`.
- Assert the filter: rows below the threshold are dropped, rows at the threshold are kept.
- Re-fetch the rendered page and confirm no name from the bundled set appears in the text.
