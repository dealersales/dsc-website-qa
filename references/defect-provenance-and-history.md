# Defect provenance and "did we check this before launch?"

Two questions arrive together when a dealer complains, hands in their notice, or asks who broke
something:

1. **Is this defect the template's, the feed's, or the dealer's own data?** The answer decides who
   fixes it and how the conversation is pitched.
2. **Did we ever check this site before it went live?** Answer it from the record, not from instinct.

Both are answerable from what is already on disk. Work in this order.

## 1. Establish the history window before you answer the second question

Session history has a hard start date. Read it before you imply anything about prior checks:

```bash
sqlite3 ~/.hermes/profiles/dsc/state.db \
  "select min(datetime(started_at,'unixepoch')), max(datetime(started_at,'unixepoch')), count(*) from sessions;"
```

If the site launched before that window, the honest answer is "no record exists here, and a check
could not have been recorded in this profile" — not "we never checked". Say which of the two you
mean. A site built and shipped before the profile existed is the common case for older clients.

`session_search` with `sort='oldest'` and no query **does not return the oldest sessions** (browse
mode returns recent ones regardless of sort). To reach back, pass a dated query — `query=...` with
`before=YYYY-MM-DD` — or read the window straight from the DB as above.

Then search by client name, by domain, and by dealer ID (the platform `did`) separately: the domain
appears in directory-data sessions, in estate sweeps and in cron triage, none of which is a QA pass.
List what you found by date and kind so "we checked it" cannot be confused with "it was mentioned".

## 2. The build mirror is the ground truth for template-vs-client

Every the platform dealer site exists twice on disk and neither is the live server:

```
~/Documents/<project>/ftp-mirror/<domain>/                                  # the deployed file tree
~/Documents/<project>/websites/<domain>/     # the same tree in git
```

Read it before attributing anything. What each file proves:

| File | What it settles |
|---|---|
| `sitemap.xml` at the web root | A stale dev sitemap committed in the build = shipped defect. Its absence next to a working `sitemap.php` = the generator is the only source and the live file is a deploy leftover |
| no `robots.txt` in the tree at all | robots was never part of the build, so nobody deleted it |
| `data/*.json` | Seeded content — testimonials, site copy. This is where fabricated reviews come from, including placeholder rows carrying a **real colleague's name** as a test entry |
| `docs/` | The original brief: the launch email, the dealer's supplied page documents (`.docx`/`.rtf`), and any correspondence with the previous supplier |
| `content.json` | The CMS content file, if one ships — often still holding the template's own demo copy |
| `AGENTS.md` / `README*.md` / `package.json` | Which template generation and who built it — and these are frequently **live at the public web root** (see the exposure pitfall in SKILL.md) |

The mirror is a copy, not a witness: confirm it matches live before quoting it (an `admin.php`
of 12 KB on disk against a 1.9 KB login form served live is a normal drift). Check the git import
date too — `git log --reverse -- "customer-websites/<domain>"` — because a bulk import of twenty
sites is a mirroring job, not an audit.

## 3. Read the launch email in `docs/` — it names the cause of cross-dealer copy

Contamination is rarely random. The brief usually says so out loud: a build commissioned as "one
similar to <other dealer>" inherits that site's meta descriptions, town names and headings, and the
template's reviews come seeded. Quote the instruction in the write-up. It moves the finding from
"another dealership's name is in your meta descriptions" (which reads as carelessness) to "the
build was cloned from that dealer's site, which is where the copy came from" — a documented
decision with an owner, and a fix that is a find-and-replace rather than a rebuild.

Same pass: note the **launch date** from the mail. It anchors every "this has been live since …"
statement and explains why there is no QA record — the job predated the pre-launch routine.

## 4. Date the defect class across the estate before claiming it is platform-wide

A template fix is applied **per site at launch**, not rolled out. Two identical builds can sit at
different states because one was regenerated on its go-live day and the other was not:

```bash
for d in <each sibling domain>; do
  out=$(curl -s -m 25 -A "$UA" "https://$d/sitemap.xml")
  echo "$d locs=$(printf '%s' "$out" | grep -o '<loc>' | wc -l) dev=$(printf '%s' "$out" | grep -c '127.0.0.1')"
done
```

Report the split — fixed here, still broken there — rather than one estate verdict. It changes the
ticket from "the platform is broken" (which the platform owner will dispute, because most sites are
fine) to "this deploy step was missed on these two", and it is directly actionable: the sibling that
still serves the dev sitemap is a client we can fix today.

## 5. Write it as a timeline, and separate template-born from client-born

A short table carries this better than paragraphs — date, event, source. Then state plainly which
findings came with the build and which are the dealer's data. That distinction is the deliverable
when the dealer is deciding whether to leave: a client who believes their own adverts are wrong when
the platform is double-encoding them is leaving over a fixable bug, and telling them so costs one
paragraph.

## Pitfalls

- **Do not answer "did we check before go-live" from a failed session search alone.** An empty search
  means the query missed, not that the work did not happen — search by name, domain and dealer ID,
  check the history window, then check the project folders and `new-sites-qa/FINDINGS.md` for a
  written audit before saying no.
- **An estate sweep mentioning a domain is not a QA of that domain.** A robots/soft-404 probe that
  returns a client's name in a list of seven is corroboration, not a check; label it as such.
- **Seeded testimonials in `data/*.json` are builder test data.** One dealer's review set included a
  row in a colleague's own name and a purchase of a car the site does not stock. Report the file path
  as the evidence: it proves the reviews were shipped with the build rather than written by the
  dealer, which is the difference between a build ticket and an accusation.
