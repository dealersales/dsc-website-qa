# Publishing reviews and rate claims on a client site

Two classes of content carry legal weight on a dealer site and are routinely shipped wrong. Both are
publishing decisions, not copy edits.

## Reviews

- **Every published review must be a real review, copied verbatim.** Name, rating and words as posted. Fixing a
  customer's spelling, paraphrasing a quote, or filling a gap with a plausible-sounding testimonial are the same
  offence — invented or altered testimonials are banned under the DMCC Act 2024.
- **A fallback list is the easiest way to commit that offence by accident.** A page that falls back to bundled
  testimonials whenever the live feed returns nothing publishes fiction the moment the feed has a quiet week.
  An empty state that says "no reviews yet" is the correct behaviour, not a gap to be filled.
- **A filtered list is a *selection* and must be labelled as one.** Showing 4★ and above is fine when the page
  says it is a selection and carries a visible link to the full profile; the same quotes with no route to the
  rest are a misleading commercial practice. Set the floor in config, label the list, link the profile.
- **Never publish an OCR transcription of a customer's words.** Text good enough to read is not good enough to
  quote. Use the platform export or the review manager's API; if OCR is the only route, hand the text over for
  checking instead of shipping it.
- **No source date means no date.** Review exports frequently omit the posting date, and a manager's date is
  often the date it was entered (two consecutive days for two old reviews is the tell). Blank beats wrong.

## Rate and finance claims

- **Count the rate claims before advising.** Grep the whole build for the rate string and for "representative":
  a site can quote a headline APR fifteen or sixteen times while the representative APR appears once, low on
  one page. That ratio is the finding, not the individual sentences.
- **Pair every mention, or drop the rate.** Either the representative APR travels with each mention in the same
  breath — `from 10.4% APR · 19.9% APR representative` — or most mentions become "finance available" with the
  rate kept for the pages that carry the full representative example. The second reads better and is easier to
  defend.
- **Prominence is the test, not presence.** A representative APR buried in a paragraph below the fold does not
  answer a headline rate in an `<h1>` or a badge. Check headings, hero copy, meta descriptions, badges and any
  shared component (header default meta, FAQ answers, `llms.txt`) separately — they are separately authored.
- **Compliance wording is not yours to change quietly.** Draft the before/after and put it to the dealer's
  compliance contact; flag the third-party finance widget separately, because its own quoted example must
  agree with the rate the page states, and that is the supplier's figure to confirm.
