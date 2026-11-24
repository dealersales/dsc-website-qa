# Getting a dealer's real reviews and opening hours onto a build

Both are facts about the business rather than design decisions, and both are trivially easy to publish
wrong: a misquoted review is a misrepresentation, and wrong hours send a customer to a locked gate. Source
them from a **verbatim export**, store them in one editable data file, and let the template render it.

## Reviews

### Take the text from an export, never from a screenshot

A CSV export (Pleper and similar GBP tools) carries the reviewer name, star rating and the full comment
with its punctuation and emoji intact. That is the only acceptable source for text a customer will read
as a quote.

**OCR of a review screenshot is not a verbatim source, however good it looks.** Two independent passes at
different scales agreed on most words and still disagreed on names and small words — `Geoff Elletson`
came back `Geoft`, `3 years` came back `years`. Cross-pass agreement tells you the *screen* is legible; it
tells you nothing about a particular word. Publishing an OCR transcription of a customer's words is the
same class of error as inventing one: the quote is no longer theirs.

A worked OCR pass is still worth doing on a review-audit screenshot to get the **shape** — how many
reviews, the average rating, which are local guides, the most recent dates — because that is what tells
you whether the export and the live profile agree. Just never let it be the source of the sentences.

### Never fall back to a transcription when the feed is empty

A page that renders nothing is honest; a page that renders a bundled or OCR'd list when the API returns
`No data` is publishing words nobody wrote. If the review manager is empty, the page says so and links to
the Google profile. Keep that branch even after the manager is populated — a feed going quiet is a routine
event, not an error state to paper over.

### Attribution is the point, and dates are the trap

- Every card carries the reviewer's name as posted, the star rating, and a source badge ("Google review").
- **Only show a date the source actually carries.** An export with an empty date column, and a manager
  whose dates are two consecutive days for reviews years apart, are both giving you *entry* dates. A wrong
  date beside a real quote is worse than no date.
- A username (`HULLSJOKER`) is the reviewer's chosen display name — publish it as-is rather than
  "correcting" it to a person's name.

### Filtering to good reviews is fine; hiding the rest is not

Publishing a selection at 4 stars and above is legitimate. Presenting that selection as the whole picture
is a misleading commercial practice under the DMCC, so a filtered list must be labelled as a selection
("a selection of the reviews our customers have left") and must carry a link to the full profile. Put the
threshold in config (`REVIEW_MIN_RATING`) rather than in the template.

### Ship it as an editable data file

`data/reviews.json` — an array of `{name, rating, text, date, source}` — is a file the dealer's coordinator
can correct without touching PHP, and it is reviewable in a diff. Have the page prefer the manager feed and
fall back to the file, or the file alone while the manager is being populated; both return the same shape,
so the swap is one line when the feed is complete.

## Opening hours

- **Read all seven days, from one export or screenshot, before setting any of them.** A single weekday
  reading is not the week: one profile closed at 20:00 on a Thursday and 17:00 on a Friday, so a uniform
  weekday row built from one day is wrong on the other four.
- **The profile is authoritative; match the site to it, not the other way round.** The reverse decision
  (edit the profile to match the site) has been taken on other clients, so confirm which way it runs before
  editing either.
- **One source, four renderers.** Hours appear in the footer block, the contact aside, the open/closed
  badge and the `OpeningHoursSpecification` schema, and drifting between them is the normal failure. Put
  them in one `DEALER_HOURS` config array keyed by ISO day number, generate the schema from the same array,
  and collapse weekdays into a single row only when they are genuinely identical.
- **Expect the weekend to be wrong in both directions** — an outgoing site said Sunday 10:00–16:00 against
  a profile saying 09:00–17:00. Check the weekend explicitly rather than only the weekday close.
- Static files that restate the hours (`llms.txt`, any prose FAQ answer) need the same edit in the same
  pass.

## Where the data comes from when the profile will not co-operate

Maps serves a reduced panel to an automated browser: the hours disclosure ignores synthetic clicks and
CDP mouse events, the reviews are not in the page HTML, and Google Search rate-limits the IP. When that
happens, a hands-on export from the SEO/GMB tool (a Maps screenshot plus a review CSV) is the fast, exact
route — ask for it rather than burning turns on scraping, and say which figures came from which export.
