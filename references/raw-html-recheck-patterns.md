# Raw-HTML re-verification patterns (live-site pass)

Proven on the dealer group (centremotorgroup.com), Sep 2026, re-checking open
QA findings against the live site.

**Key principle:** rendered-text extraction (web_extract, attached page context,
read_preview) drops the `<head>` entirely. Titles, meta description/keywords,
canonical, and JSON-LD are invisible to it. For anything in the head, work on
raw HTML fetched with curl.

## Fetch every page, then scan

```bash
cd /tmp
curl -sL --max-time 20 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15" \
  "https://CLIENT/" -o page_home.html
# repeat per page template: about, contact, cars/stock, finance, reviews,
# sell-your-car, servicing, warranty + 1-2 vehicle detail URLs
```

## Head checks (per page)

```bash
grep -o '<title[^>]*>[^<]*</title>' page.html
grep -io '<meta name="description" content="[^"]*"' page.html
grep -io 'burnley' page.html | wc -l      # wrong-town scan
```

## Site-wide wrong-text scan (wrong town / other dealer names)

```bash
for f in cmg_*.html; do c=$(grep -io 'burnley' "$f" 2>/dev/null | wc -l | tr -d ' '); echo "$f: $c"; done
```

## Duplicate-copyright check — count, don't eyeball

Expect exactly 1 of each per page:

```bash
grep -o '©' page.html | wc -l
grep -io '&copy;' page.html | wc -l
grep -io 'all rights reserved' page.html | wc -l
```

## Cross-page consistency claims (MOT months, warranty, hours, phone, NAP)

Strip tags, list EVERY occurrence with context per page, then tabulate across
pages — contradictions show up as disagreeing rows:

```bash
python3 - <<'EOF'
import re
html = open('page.html', encoding='utf-8', errors='replace').read()
txt = re.sub(r'<script.*?</script>', ' ', html, flags=re.S|re.I)
txt = re.sub(r'<style.*?</style>', ' ', txt, flags=re.S|re.I)
txt = re.sub(r'<[^>]+>', ' ', txt)
txt = re.sub(r'\s+', ' ', txt)
for m in re.finditer(r'(?i)(.{120}?\bMOT\b.{160}?)', txt):
    print(re.sub(r'\s+',' ',m.group(0)).strip()[:280])
EOF
```

## US-spelling: match VERB forms only

`grep -i specializ` also matches the legitimate UK noun **"specialist"** (same
spelling both sides of the Atlantic). Grep the verb forms:

```bash
grep -io 'specializ\(e\|es\|ing\|ed\)' page.html
```

## Shared template vs page-body copy

A string repeated on every page (e.g. "Specializes in automatic and 4WD
vehicles") usually lives in a shared header/footer or JSON-LD block — one
template fix cures the whole site. But the same phrase can ALSO sit in
per-page body copy (homepage x2 in the the group case). Before advising "one fix
cures the site", show raw context to see which element holds it:

```bash
grep -o '.\{60\}Specializes.\{60\}' page.html
```

## Two URLs serving the same page (/cars vs /cars.php)

Compare canonical/og:url before calling duplicate content — self-canonicals
pointing at each URL make it benign:

```bash
diff <(python3 -c "import sys;print(open('a.html',encoding='utf-8',errors='replace').read().replace(' ',''))") \
     <(python3 -c "import sys;print(open('b.html',encoding='utf-8',errors='replace').read().replace(' ',''))")
# macOS sed strips whitespace but errors on illegal byte sequences; use python
```
