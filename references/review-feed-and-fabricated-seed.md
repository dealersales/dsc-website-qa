# Review feeds, and the three ways a review page publishes fiction

A dealer review page is the one part of a build where the CMS will happily publish content nobody
wrote, and where doing so is a statutory offence rather than a copy error. Treat every review surface
as a data-integrity check, not a page that "loads fine".

## 1. The bundled fallback is the mechanism

The commonest way invented reviews reach a live site is not someone typing them in — it is a well-meant
fallback. The page calls the review service, the service returns nothing (which is the normal state for
a dealer who has just been switched on), and the template renders a bundled array so the page "doesn't
look empty". The defect is exactly inverted: the fabricated reviews appear *precisely when there are no
real ones*, and disappear only if the dealer starts collecting reviews.

```php
// what it looked like
$reviews = fetch_from_service();      // []
if (!$reviews) { $reviews = get_reviews(); }   // six invented testimonials
```

**Rule: a review page has no bundled fallback, ever.** When the service is empty, unreachable, or says
`No data`, the page renders an empty state that points at a real platform ("we have started collecting
reviews — read our Google reviews in the meantime"). Cache server-side and prefer a *stale cache* over
invention, which is the only legitimate fallback here.

Test the empty path as its own case. The state you will meet most often on handover is "no reviews", so
that is the branch that needs the most confidence, not the least.

## 2. A platform's "sample payload" may be fabricated content

When a new feature is switched on, the platform owner often supplies another dealer's endpoint as the
structure to code against. Read that payload as **data to be judged, not a schema to copy**. Signals
that it is seed content rather than real reviews:

- first-name-plus-surname entries that are all generic and interchangeable (the same fictional names
  recur across demo datasets),
- every rating identical — commonly all 5,
- prose written in the same voice, often restating the brief ("Excellent service from start to finish"),
- vehicles from a lineup the dealer does not stock,
- **and the tell: a real, identifiable person connected to the business or the agency** named as a
  customer. That single entry removes any "these are anonymised" defence and turns the finding from a
  data-quality note into a live compliance problem.

On the platform estate the review manager returns the same seven seeded reviews for every dealer it is
switched on for, and at least one estate site is publishing them. So:

- Never copy another dealer's payload into a build as a starting state, and never leave one in a cache
  file the new site reads.
- Check whether the dealer you are working on is *already* publishing them — an estate-wide seed affects
  sites nobody is looking at.
- Raise it as a platform-level issue: if the review manager seeds demo reviews, every dealer switched on
  inherits them, and the fix belongs in the manager, not on sixteen sites.

## 3. Paraphrase is fabrication

Quoting a real review verbatim with the reviewer's name, the date, the rating and a link to the platform
is fine. Rewriting one "to read better", anonymising it into "a customer said…", or translating it are
the same defect as inventing it. A machine translation is not a verbatim quote either — force the locale
(`?hl=en-GB&gl=uk`) and quote the original, or quote nothing.

## 4. Rendering and parsing details that matter

- **The service may return `No data` as a plain string, not JSON.** `json_decode` gives `null` for that
  and for malformed responses alike, so handle `null`, `[]` and a scalar as "the dealer has none" rather
  than as a parse error to be logged and ignored. Cache the empty result too, or every page load re-hits
  an endpoint that will keep saying no.
- **Map the fields to attribution, not to a headline.** The payload is
  `{name, vehicle, rating, comment}`; rendering `name` as the review's heading and `vehicle` as the
  byline reads as a caption rather than a review. Render stars, then the comment, then
  `name · vehicle · date` as one attribution line.
- **Do not add `AggregateRating`/`Review` structured data for reviews of the business on its own site.**
  Google's policy treats that as self-serving review markup. A review widget's own markup is the
  platform's business; markup you add about the dealer on the dealer's page is not.

## 5. Prove the mapping without publishing the data

Write the normaliser as its own function and test it against a payload you are *not* going to publish —
another dealer's real feed — so the parser is exercised on the true shape while the empty state stays
the only thing that renders on the client's page:

```bash
php _test_reviews.php <other-did>     # prints what the template would render, one line per review
```

Then assert both branches in the page itself: with reviews (fields present, attribution correct) and
without (empty state, no fabricated name anywhere in the HTML). Grep the rendered page for the names
from the old bundled list — a presence test on the empty-state sentence alone will pass while a stale
cache or a second fallback still ships them.
