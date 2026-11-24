# Building the redirect map for a dealer site migration

Trigger: a dealer site has moved to a new build and the old URLs 404, and the developer needs the
301 map itself — "draft the redirect map", "we need the redirects", a launch that half-mapped.

A redirect map is a **deliverable**, not a diagnosis. Report coverage first (see the SKILL.md
pitfall on probing by URL shape), then build the thing they can paste.

## Procedure

### 1. Source the old URL set from the Wayback CDX index, not from a crawl

The outgoing site is frequently already gone by the time the map is asked for — on one build the
old domain was DNS-dead and the previous host's copy had 404'd, so crawling returned nothing at all.
The archive still has it.

```bash
curl -s "http://web.archive.org/cdx/search/cdx?url=<OLD-DOMAIN>/*&output=json\
&fl=original,timestamp,statuscode&collapse=urlkey&limit=20000" -o cdx.json
```

Filter out assets (`.css .js .png .jpg .svg .woff .xml .ico`), normalise to paths, dedupe. Two
things this buys you that a crawl cannot:

- **Every historical generation at once.** A dealer site usually carries three-or-more failed URL
  schemes (a WordPress-era one, an intermediate one, the site it just left). One map has to cover
  all of them, and only the archive still remembers the oldest.
- **The bare-slug share links.** The old WhatsApp/share URLs are a *different shape* from the
  site's own links and appear nowhere in navigation — they are what customers have in old messages.

If the outgoing site **is** still up, crawl it too and take the union of both sets.

**When the CDX API is unavailable, do not stop — the old URL set is still recoverable from search.**
The Internet Archive goes down, and the outage is served as an **HTML page where JSON was expected**,
so a parser fails while a status-code-only check passes; read the body, not the status. The fallback
that works: a `site:<old-domain>` query returns the still-indexed URL shapes — the previous
generation's `/vehicles/<make>-<reg>/`, `/warranty/` and `/contact/` forms came back this way, along
with the stale snippet still carrying another dealer's name — and Search Console's Pages report gives
the complete list for a domain you have access to. Say in the coverage report which source each part
of the map came from, and re-run the CDX pass later to catch the tail.

### 2. Classify into URL families, then write one rule per family

mod_rewrite is first-match-wins with `[L]`, so rule ORDER is part of the design: specific rules
above their family's catch-all. Families that recur on dealer rebuilds:

| Family | Shape | Target |
|---|---|---|
| Static pages | `/finance`, `/contact-us` (old site had no extension) | `/finance.php`, `/contact.php` |
| Listing entry points | `/stock`, `/used-cars`, `/search`, `/featured` | `/stock.php` |
| Make / type landing pages | `/stock/used-volvos-in-<town>` | `/stock.php?make=Volvo` |
| Vehicle detail | `/vehicle/<slug>-<uuid>` | `/stock.php?make=<Make>` |
| Older generations | `/search/<make>/`, `/used-car/<make>/…`, `/used/cars/<make>/` | make filter, else `/stock.php` |

### 3. Guard the vehicle-detail patterns with the OLD format's own fingerprint

**This is the step that decides whether the map is safe.** A blanket `/vehicle/*` rule redirects the
live inventory, because the new build's own VDPs sit at the same path prefix — the one rule that
looks most obvious is the one that breaks the site.

Find a token the **old** format always has and the **new** format never does, and anchor every
pattern to it. On these builds it is the trailing UUID:

```
OLD  /vehicle/audi-a4-…-in-bradford-west-yorkshire-4232bb72-04df-4685-9632-b35200c38009
NEW  /vehicle/2019-69-reg-volvo-s90-2-0-t4-r-design-plus-auto-euro-6-4dr-automatic-aj19bkz
```

So every `/vehicle/` rule requires that UUID tail, and the new inventory can never match:

```apache
RewriteRule ^vehicle/([^/]+)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/?$ /stock.php [R=301,L]
```

Do the same for the bare-slug share form (`^<slug>-in-<town>-<county>-<uuid>$`).

### 4. Anchor every pattern so it cannot match its own target

`^finance/?$` is safe; `^finance` also matches `/finance.php` and redirects it to itself — an infinite
loop. Anchor with `$` and use `/?` for the optional trailing slash. Same for every extension
promotion: the rule that adds `.php` must not match a URL that already has it.

**Exclude live resources explicitly.** `/` and `/robots.txt` are real and must never redirect; note
them in the coverage output as "live resource — correctly not redirected" rather than leaving them
looking unmapped.

### 5. Validate BOTH directions — and 0 false positives is the gate

Simulate mod_rewrite in Python: apply the patterns **in rule order** to `path.lstrip('/')`, take the
first hit, and run two assertions.

1. **Every archived old URL is caught** by some rule.
2. **NO live-site URL is caught.** Feed it every live page, the sitemap's `<loc>` list, and a sample
   of current vehicle detail URLs.

A map that passes direction 1 and fails direction 2 has broken the live site — which is a worse
outcome than the 404s it was written to fix. Direction 2 is the one to be pedantic about, and it is
the one a spot-check misses.

Report the result as a count (`206 archived URLs → 204 caught, 2 live resources, 0 false positives`).

### 6. Verify the TARGETS resolve to real content before pointing traffic at them

Probe every distinct destination and read what it actually serves. **A make filter that returns zero
stock is a worse landing page than the generic stock page** — request each `?make=` target and read
the returned vehicle count, not the status code. Where a marque has no stock, send it to `/stock.php`
and record why; where the make is still sold, the filter page is the better destination. This also
surfaces open client questions — a make still in the dropdown selling nothing is a content gap to
raise, not just a dead target.

### 7. Improve redirects that already exist but land too generically

Read what is already in place before writing the map. Some redirects work but dump a *keyworded*
landing page on the generic stock page while a real make filter exists for it. Correct those inside
the map so there is one source of truth, and say plainly which of them you changed — otherwise the
developer's existing rules and yours disagree and the first-match-wins order decides it arbitrarily.

### 8. Dead-end legacy paths go to 410, not 404

Old API endpoints and framework artifacts have no equivalent and no link value. `[G,L]` tells Google
to drop them faster than a 404. Keep them in their own labelled section.

### 9. Ship three artefacts

- **the rules file** (`.htaccess` — the right target here, since the LiteSpeed hosts read it)
- **a CSV of every old → new mapping**, so the developer can review the full list without reading regex
- **a short README**: what it is, the validation result, deployment notes, and a post-deploy test

Stage and attach per `deliverable-handover.md`. Say in the README where the rules go — **above any
catch-all "route everything to index.php" rule**, and with the hand-written rules they supersede
removed so the file does not carry two sets.

**These three are the pack, not the report.** The developer also needs a document addressed to them —
the findings, the deployment steps and the post-deploy tests, in house style — because a rules file
arriving on its own reads as a file-drop and comes back as "where's the report?". See the SKILL.md
§5 rule, "Ship one document addressed to whoever has to act".

## Pitfalls

- **Apache does not support inline comments after a directive.**
  `RewriteRule ^finance/?$ /finance.php [R=301,L]   # old /finance` — the trailing tokens are parsed
  as additional arguments, the config fails to load, and the whole file's rewrite behaviour goes with
  it. The note goes on its own `#` line **above** the rule. This is worth catching in your own draft
  before it reaches a developer.
- **Validate the generated file's syntax in code, not by reading it.** Assert per `RewriteRule` line:
  exactly four whitespace-separated tokens (directive + pattern + substitution + flags), the flags
  token matching `\[[A-Za-z0-9=,;]+\]`, balanced parentheses in the pattern, a root-relative or `-`
  substitution, a zero `<IfModule>` balance, and no `#` anywhere on a rule line. Report the count of
  rules and the flag set.
- **Group the rules by family with a heading comment per section.** A flat 130-rule file is
  unreviewable; a developer will not read it and will hand-write their own. The section headings are
  what make the map reviewable and correctable.
- **A rule note is not a rule.** Keep the human note in the `#` comment and the CSV, and keep the
  rule line itself to the three fields Apache expects.
- **Never write the map against a domain you have not confirmed is the canonical one.** If the site is
  mid-migration and the canonical host is still unsettled (see `domain-migration-and-ips-tags.md` §5),
  use root-relative substitutions so the rules inherit whatever host serves them, rather than
  hardcoding a domain that may change.
