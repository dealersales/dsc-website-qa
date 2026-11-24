# The dealer estate: enumerating it, and what to report

For "give me a list of all the dealer websites", "what is on the platform owner's server", and any estate-wide
defect count — the population has to come from the host, not from memory. Sections 1–4 are the
inventory; §5 is how to sample vehicle pages across the estate's mixed template generations, and §6
is the shape of the review document that follows. The recurring failure is
answering from the client table: the DSC roster, the directory network and the hosted sites are three
different populations and only one of them lives on this box.

## 1. List the host, live — never the mirror

Every the platform dealer site sits under one Hostinger account, one directory per domain. The local mirror
`~/Documents/<project>/ftp-mirror/` is a dated copy and drifts (it was missing a live domain on the day it
was checked), so read the server. Credentials are in the macOS keychain as `<keychain-item>` (account
`u426059964`); resolve them inside the command so the secret never reaches the transcript:

```bash
PW=$(security find-generic-password -s <keychain-item> -w)   # sanity-check without revealing it
printf 'keychain entry length=%s\n' "${#PW}"
curl -s --user "u426059964:$PW" -m 40 "ftp://<host-ip>/domains/" \
  | awk '{print $NF}' | sed 's#/$##' | sort > /tmp/domains_live.txt
wc -l < /tmp/domains_live.txt
```

Never `echo "$PW"` to debug — a missing keychain item shows as an empty string and a shorter length,
which is enough to diagnose it.

## 2. Classify by fetching, not by domain name

Domain names lie in both directions: `carsforsalemanchester.co.uk`, `carsforsaleinmanchester.com`
and `carsinmanchester.com` are the same directory, and a dealer's name can appear in none of its
domains. Fetch every homepage once, in parallel, and bucket on the title and the build signature:

```python
# per domain: (status, <title>, platform markers, sitemap, robots)
# platform markers that identify a platform PHP build: <platform-host>, sitemap.php,
# /assets/css/whitered.css, /cars.php, /stock.php; WordPress: wp-content; Click Dealer: clickdealer
```

Four buckets, and keep them apart in the answer:

| Bucket | What it is | Counted as dealer sites? |
|---|---|---|
| Dealer website | one dealership's own site | yes |
| Directory network | `carsforsale.directory` + regional/local variants | no |
| Platform / company | the CRM product sites, the demo dealer site, the owner's other companies | no |
| Other | anything hosted but not the platform (restoration specialist, a WordPress site) | no, but list it |

**A two-domain dealer is one business.** Two live domains serving identical titles and layouts
(`x.co.uk` + `x.com`) are an alias pair, not two clients — count businesses and domains separately,
or the headline inflates.

## 3. The value of the sweep is the defect column

A list of names is worth one minute. The same pass yields the estate's live defect matrix, which is
what anyone will act on — probe `/sitemap.xml` and `/robots.txt` for the dealer subset:

```bash
for d in <dealer domains>; do
  s=$(curl -s -m 20 -A "$UA" "https://$d/sitemap.xml")
  printf '%-34s locs=%s devhost=%s robots=%s\n' "$d" \
    "$(printf '%s' "$s" | grep -o '<loc>' | wc -l | tr -d ' ')" \
    "$(printf '%s' "$s" | grep -c '127.0.0.1')" \
    "$(curl -s -m 15 -A "$UA" "https://$d/robots.txt" | grep -qi '<html' && echo soft404 || echo real)"
done
```

Report it as a split, never as one estate verdict: *real sitemap* / *committed dev sitemap
(127.0.0.1 locs)* / *serves HTML (soft-404)* / *no file (404)*, and the same for robots. The four
states have four different fixes, and the dev-file group is a per-site deploy step that was missed —
so name those domains individually and offer that fix. `404` on both is a different ticket from
`200` with HTML on both.

**The same four-state reading applies to any file-availability question** — `llms.txt`, a verification
file, a staging `.htpasswd`. Two rules that decide whether the column is true:

- **The live response is the verdict, not the docroot listing.** FTP tells you what was *deployed*;
  a rewrite can serve a generated file where no file exists, an alias docroot can redirect to its
  primary, and a docroot can carry the generator instead of the output. Use the listing to explain a
  state, never to assign one.
- **Grep the raw listing for the file's name; do not column-split it.** `awk '{print $NF}'` over an
  `ls -l`-style listing drops rows and mis-picks the field often enough to manufacture "no file here"
  for a docroot that plainly contains it — `grep -oiE '<token>[a-z.]*'` over the raw response, or a
  real FTP client, is the reliable read.
- **A `000` is a gap in the measurement, not a missing file.** Retry with `curl --http1.1` (a managed
  host can close an HTTP/2 stream mid-response where 1.1 answers), and if curl still gets an empty
  reply, re-fetch the same URL through a second egress (`web_extract`) before recording anything.
  Report unresolved domains as **unverified** — neither clean nor missing — because the client's own
  browser will contradict a "missing" verdict raised from a blocked request.

## 4. Say which population you answered for

The DSC client roster, the directory network's dealer table and this box's hosted sites overlap
without matching. Some clients are directory-only listings; others (WordPress/SiteGround builds) are
nowhere near this server; and the box holds dealers who are not clients at all. State that in the
reply — otherwise a list of sixteen looks like it contradicts a client table that names thirty-four.

## 5. Vehicle pages across mixed template generations

One host can carry three generations of the same platform at once — `/car/<id>/<slug>`, `car.php?id=<hash>`, and `/used-cars/<slug>.html`. An id-anchored link regex therefore finds stock on some sites and **zero** on others, and zero reads as "no vehicles" rather than "wrong pattern". Discover by validation, not by URL shape:

1. Try listing paths in turn until one returns a real page: `/cars`, `/vehicles`, `/stock`, `/cars.php`, `/vehicles.php`, `/stock.php`, `/used-cars`, `/used-cars.html`.
2. Collect internal hrefs, drop nav/static/asset links, and keep only paths containing a digit.
3. Fetch a candidate and accept it as a vehicle page only if it contains a price in `£` **and** a mileage figure. Everything else is a category page or a sold-stock stub.

**Never take the sample from `/sitemap.xml`.** On the dev-file sites the sitemap lists the demo dealer's cars on `127.0.0.1`, so a sitemap-derived sample either fails to fetch or quietly samples another business's inventory and reports the dealer as having the wrong stock.

**Do not count blank descriptions from a parsed description block.** The block sits in a different place in every generation, so a `Description</h2><div><p>` regex returns empty text on half the estate and manufactures a "no description" column that is a parser artefact. When the question is encoding or copy, scan the **whole page** for the fault patterns (`&amp;(quot|amp|#0?39|gt|lt);`, `\bu00[0-9a-f]{2}`) and only parse the block when the finding is about the description itself.

Photo counts are the same trap — `<img>` counting and CDN-filename counting disagree per template, and lazy-loaded galleries undercount. Treat gallery thinness as a per-dealer manual check, not an automated column.

**State the sample in the document.** "Six vehicle pages per site on eleven of the sixteen; the other five are untested because their listings expose no scrapeable vehicle links" — an untested site is neither clean nor faulty, and saying so is what stops a sampled count being read as a stock-wide measurement.

## 6. The deliverable: one review, owner-labelled

An estate review is a different document from a client audit. Shape that works:

1. **A one-line verdict** naming the pattern that runs through the population, then the population table — one row per dealer, columns for the defect states, using ✔ / ✘ / "not sampled" rather than prose.
2. **Workstreams numbered P1…Pn**, each with the count, the domains it hits, and the fix. A template defect is one workstream with a count of affected sites, never sixteen findings — the count is the argument for fixing it once in the build.
3. **Phases split by who can act:** platform/template build, our per-site deploy and verification, the dealer's regulated and content decisions. Put hours against each phase, because the platform owner is deciding whether to schedule it this week. **Check who actually holds the write access before you assign the template work to the platform owner** — on this estate we had FTP to every docroot, so the honest plan flipped: the template patch became ours, the platform owner kept only the piece that genuinely needs his pipeline (the feed import, which happens before anything reaches the site), and the shared-file items carried an explicit "not both of us" so they are not applied twice. A plan that books hours against the wrong party is a plan that stalls; when the split changes after the first draft, re-cut the phases and the cover's owner line in the same pass rather than leaving a document that contradicts its own opening page.
4. **Two short "what we need" lists**, one per recipient — the decision you need from the platform owner, and the decisions you need from the coordinator. Never one merged list.
5. **A closing paragraph saying which defects are the build's and not the dealers'.** It is true, it decides the tone of a conversation where a dealer is leaving over one of them, and it keeps the document from reading as a bill of indictment against sixteen small businesses.

Reuse the same P-numbers in the chat reply and the digest that the document carries, so a verbal "P3 is done" means the same thing in every artefact.

## Pitfalls

- **Never build the list from the client table or from memory.** Both are partial and neither is
  scoped to the host; the FTP listing is the only authoritative population.
- **A parked or default host is not a dealer site.** A `*.hostingersite.com` entry is a leftover
  Hostinger default hostname; it will not resolve on https and belongs in the "other" bucket.
- **The demo dealer site explains the dev sitemaps.** The platform's own demo build sits on the same
  box; the `dealer-sites/template1/v2` path inside a dealer's stale sitemap points back at it. Useful
  context for the fix, not a separate finding.
- **Give the answer as a table plus a CSV.** Woody asks for lists to forward and to paste; a chat-only
  list cannot be reused. Save `<topic>-inventory.csv` beside the report and attach it.
- **A sampled figure is not a stock-wide figure — label it.** Six vehicles per site establishes a pattern ("every sampled title is generic"); it does not establish a count. Where a full-stock pass exists for one site, quote that site's real number separately and say the rest are samples.
- **A headline number can go stale inside the same engagement.** The defect a dealer is complaining about may be repaired between your passes — re-measure the headline before the document is rendered, put the measurement time on the cover, and state in the body that the item has since been fixed if it has.
