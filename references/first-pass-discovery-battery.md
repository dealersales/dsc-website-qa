# First-pass discovery battery (brand-new site)

Proven on Four Plus 4 (fourplus4.co.uk), Sep 2026 — a WordPress + Elementor +
ElementsKit service-garage site with no existing DSC findings. Run this when a
site is dropped in with no prior audit state, before any page-by-page pass.
Complements `raw-html-recheck-patterns.md`, which is for RE-verifying known
findings on a live pass; this file is for the initial sweep from zero.

**Key principle:** never trust rendered-text extraction (web_extract, attached
page context) for encoding, head tags, or structure — it mis-decodes entities
and drops `<head>`. Work on raw HTML fetched with curl.

## 1. Enumerate pages from the sitemap

WordPress exposes `wp-sitemap.xml` (or per-type: `wp-sitemap-posts-page-1.xml`,
`wp-sitemap-posts-post-1.xml`, `wp-sitemap-taxonomies-*.xml`). robots.txt
usually points at it. Also fetch robots.txt for the Disallow list.

```bash
curl -sL --max-time 30 https://CLIENT/sitemap.xml
curl -sL --max-time 30 https://CLIENT/wp-sitemap-posts-page-1.xml | grep -o '<loc>[^<]*</loc>'
# repeat for posts — a hosting-default starter post (e.g. SiteGround's
# "WordPress Resources at SiteGround") often shows up here, live and indexable.
```

**Do not conclude "no sitemap" from `/sitemap.xml` alone — probe the candidate
paths and read what answers.** A dealer site served a real, dynamically-generated
index at `/sitemap-index.xml` (children `sitemap-pages.xml` and
`sitemap-vehicles.xml`) while `/sitemap.xml`, `/sitemap_index.xml` and
`/sitemaps.xml` all returned 404.

```bash
for p in sitemap.xml sitemap_index.xml sitemap-index.xml sitemaps.xml wp-sitemap.xml sitemap/ sitemap.txt; do
  printf '%-20s ' "$p"
  curl -s -o /dev/null -w '%{http_code} %{size_download}b %{content_type}\n' --max-time 20 -A "$UA" "https://CLIENT/$p"
done
```

Then read the child sitemaps and reconcile them against the pages you actually
found: a live 200 page the pages sitemap omits is a finding, and a sitemap entry
for a page served `noindex` contradicts it. Both are one-line fixes that a
"/sitemap.xml 404s, so there is no sitemap" verdict hides entirely. A sitemap
whose vehicle count matches the listing's advertised stock total also corroborates
that count — the one place the advertised figure is independently verifiable.

Pages that exist in the NAV but are ABSENT from the sitemap are prime 404
suspects; pages in the sitemap that 404 (with a browser UA) are broken too.

## 2. Fetch every page with a BROWSER UA

Bare curl gets bot-blocked (403) on many WordPress hosts. Always send a full UA:

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
curl -sL --max-time 40 -A "$UA" "https://CLIENT/" -o page_home.html
# one file per page template from the sitemap
```

## 3. Byte-level encoding check (do this BEFORE flagging mojibake)

Extraction artefacts show `â€™`/`â€“` for clean UTF-8. Verify the raw bytes:

```bash
python3 -c "
import re
raw = open('page_home.html', 'rb').read()
print('replacement char:', raw.count(b'\xef\xbf\xbd'))   # U+FFFD
print('mojibake â count:', raw.count(b'\xc3\xa2'))
# proper entities like we&#8217;ve are FINE — that is correct markup
"
```

Only report an encoding finding if the fault is in the page's actual bytes.

## 4. Head / structure sweep per page

```bash
grep -o '<title[^>]*>[^<]*</title>' page.html
grep -o '<meta name="description" content="[^"]*"' page.html   # empty = finding
grep -io -E '<meta[^>]*(og:|twitter:)[^>]*>' page.html          # empty = no social tags
grep -c 'application/ld+json' page.html                         # 0 = no schema
grep -io -E 'yoast|rank ?math|all in one seo|seopress' page.html  # SEO plugin present?
grep -o '<h1[ >]' page.html | wc -l   # >1 = duplicate H1 (theme entry-title + Elementor heading)
```

Heading inventory with duplicates (catches copyright-as-H2, repeated H2s):

```bash
python3 -c "
import re, html
raw = open('page_home.html').read()
from collections import Counter
for tag in ['h1','h2','h3']:
    hs = [html.unescape(re.sub(r'<[^>]+>','',m)) for m in re.findall(r'<'+tag+r'[^>]*>(.*?)</'+tag+r'>', raw, re.S)]
    hs = [re.sub(r'\s+',' ',h).strip() for h in hs if re.sub(r'\s+',' ',h).strip()]
    dups = [h for h,c in Counter(hs).items() if c>1]
    print(tag.upper(), len(hs), 'dups:', dups)
    for h in hs: print('  -', h[:90])
"
```

## 5. Image alt-text coverage

```bash
python3 -c "
import re
raw = open('page_home.html').read()
imgs = re.findall(r'<img[^>]*>', raw)
empty = [i for i in imgs if re.search(r'alt=\"\"', i)]
missing = [i for i in imgs if 'alt=' not in i]
print('total', len(imgs), '| empty alt', len(empty), '| no alt attr', len(missing))
# Elementor sites: ~all content images empty, only the logo populated
"
```

## 6. Link-state sweep — NAV and BODY separately

WordPress/Elementor sites routinely have the menu correct while homepage
service cards (image-box widgets) point at stale URLs. Enumerate EVERY internal
href, then status-check the ones missing from the sitemap:

```bash
python3 -c "
import re
raw = open('page_home.html').read()
for h in sorted(set(re.findall(r'href=\"(https://CLIENT/[^\"#]*)\"', raw))): print(h)
"
# menu items carry id=\"menu-item-N\" classes; body cards are elementor image-boxes
for u in engine-diagnostics mot-testing; do
  curl -s -o /dev/null -w "/$u/ -> %{http_code}\n" --max-time 20 -A "$UA" "https://CLIENT/$u/"
done
```

Also flag mixed-scheme nav links: `grep -o 'href="http://[^"]*"' *.html` —
"Online Parts Catalogue"-style links are often left on `http://` when the site
moved to HTTPS.

## 7. NAP + entity-name consistency across pages

Strip tags, collect every occurrence variant, tabulate per page. Watch for:
phone spaced vs unspaced (`<phone>` vs `<phone>`), address comma
variants (`Leeds West Yorkshire` vs `Leeds, West Yorkshire`), and entity-name
capitalisation (`four plus 4 Limited` vs `Four Plus 4 Limited` vs `...Ltd`).
Also grep for company number / registered office in the footer — required for
Ltd companies (Companies Act display rules).

```bash
python3 -c "
import re, html
raw = open('page.html').read()
body = re.sub(r'<script.*?</script>', ' ', raw, flags=re.S)
text = html.unescape(re.sub(r'<[^>]+>', '|', body))
print(set(re.findall(r'0113\s?243\s?8116|<phone>', text)))
"
```

## 8. Compliance scope decision

Grep every page for finance wording; a zero result clears FCA but GDPR/Companies
Act checks still apply (privacy policy page, cookie-consent banner — scan for
cookieyes/complianz/cookiebot — reCAPTCHA forms, company details in footer):

```bash
for f in *.html; do echo "$f: $(grep -io -c -E 'finance|APR|credit|subject to status' $f)"; done
grep -io -E 'cookieyes|complianz|cookiebot|onetrust' page_home.html | sort -u
```

## 9. Content-fabrication tell

Template demo content left live is a Critical finding. Signature strings:
"A small river named Duden flows by their place", fake staff names with
US phone `+1 (859)...` and `info@example.com`, lorem ipsum. Grep per page.

## 10. Does the form actually RENDER? (MetForm / client-side forms)

A form plugin's markup being present in the page source proves nothing — MetForm
(and most Elementor form widgets) mount client-side via React from a
`<script type="text/mf" class="mf-template">` template. If the app bundle fails,
the container stays in the DOM at `height: 0` and the visitor sees nothing.
On Zagros Tyre and Auto Centre the contact page shipped with **no `<form>`
element at all** — the fifth Critical on an otherwise-correct build.

```js
// IN THE RENDERED BROWSER, not in the HTML:
document.querySelectorAll('form').length                 // 0 = form never mounted
document.querySelector('.elementor-widget-metform').getBoundingClientRect().height  // 0</js>
<div id="metform-wrap-<id>" class="mf-form-wrapper" ...></div>  // empty mount point
```

Scroll the widget into view and re-measure before concluding — but note that on
Zagros a scroll-into-view + 8s wait did *not* mount it. Check whether SiteGround
Optimizer is serving its own minified copies from
`wp-content/uploads/siteground-optimizer-assets/` (`metform-app.min.js`,
`mf-widget-frontend.min.js`) rather than the plugin's originals — a stale
optimizer cache for those files is the usual cause. Fix = purge + regenerate,
then exclude the bundle from JS minification if it still fails.

## 11. Leaked staging host in the combined asset bundles

SiteGround Optimizer's combined CSS keeps **absolute** `url()` references, and
Elementor's self-hosted Google Fonts cache stores the host that was current when
the cache was built. Migrate a site off `*.sg-host.com` and the live stylesheets
still point at the dead staging host, so **every webfont 404s and the whole site
renders in fallback system fonts**. Zagros carried **1,002 references across the
three live bundles** and 306 of 339 `@font-face` declarations pointed there.

```bash
curl -s --compressed -A "$UA" "https://CLIENT/wp-content/uploads/siteground-optimizer-assets/<combined-css>" -o css.css
grep -c 'sg-host.com' css.css          # count per bundle
grep -o -E 'url\([^)]*\.(woff2?|ttf|eot)[^)]*\)' css.css | sed 's|.*//||' | cut -d/ -f1 | sort | uniq -c
# confirm the host is dead, not just unexpected:
dig +short <host> @1.1.1.1     # NXDOMAIN = font cannot load
```

Confirm the consequence in the rendered page rather than inferring it:
`getComputedStyle(document.querySelector('h1')).fontFamily` returns
`Montserrat, sans-serif` while Montserrat is unreachable. Fix = Elementor →
Tools → Regenerate CSS & Data, then purge and regenerate the optimizer cache.
Same check applies to any `Disallow:`-listed or host-default path.

## 12. WordPress surfaces that expose the developer's own identity

On a client site the agency account is the *only* user, so the default WordPress
user surfaces publish DSC's details:

```bash
curl -s https://CLIENT/wp-sitemap.xml                        # lists users-1.xml, taxonomies, form CPTs
curl -s https://CLIENT/wp-json/wp/v2/users                   # {"name":"paul@sales-consultants.com",...}
curl -s -o /dev/null -w '%{http_code}' https://CLIENT/author/<slug>/   # 200 = indexable author archive
```

Users sitemap + author archive + unauthenticated `/wp/v2/users` together disclose
the agency email, the admin username and (via the slug) the SiteGround account
name. Also check the stored user URL — it is frequently still `http://` after a
move to HTTPS. Fix = disable the user/taxonomy/form sitemaps, set a neutral
public display name, restrict the users endpoint. The REST route map itself being
public is normal WordPress, not a finding.

## 13. macOS curl rejects `br`

`Accept-Encoding: gzip, deflate, br` returns
`curl: (56) Unrecognized content encoding type` on this macOS curl, writing a
0-byte file that reads as a dead page. Send `gzip, deflate` only, and always pair
`--compressed` with `-A "<browser UA>"` — bare curl gets 403 from SiteGround /
Wordfence, and a 403 from a bare UA is not evidence a page is broken.

## 14. Tracking-tag inventory — duplicates fire twice

Count the analytics and ads tags on one page and read which are live. A dealer
site that has changed agency carries the old stack alongside the new, and
multiple tags on one page all fire, so sessions and any duplicated conversion
action are counted more than once — which corrupts the conversion data the PPC
work depends on before it is even used.

```bash
grep -o -E 'GTM-[A-Z0-9]+' page_home.html | sort | uniq -c                    # >1 container = duplicate
grep -o -E 'gtm\.js\?id=GTM-[A-Z0-9]+' page_home.html                          # script-loaded (fires)
grep -o -E 'googletagmanager.com/ns\.html\?id=GTM-[A-Z0-9]+' page_home.html   # noscript iframe only
grep -o -E 'AW-[0-9]+|G-[A-Z0-9]{8,12}|UA-[0-9-]+' page_home.html | sort | uniq -c
grep -o -E '.{0,40}AW-[0-9]+.{0,20}' page_home.html                           # read context: commented out?
```

Three things to read off it: **how many GTM containers** there are, **whether each
is script-loaded or only in a `<noscript>` iframe** (a noscript-only container
never fires with JS on), and **which Ads IDs sit inside an HTML comment** (a
disabled tag is dead code to delete, not a live duplicate). One live dealer
homepage carried three full GTM containers, a GA4 property, one active Ads tag
and one commented-out second Ads tag. Report the set as one finding, name the
single current container, and confirm which Ads account is live against the
account DSC actually manages rather than assuming the first ID is the real one.

## Reusable lesson from this session

- The 403-vs-200 split on /contact-us/ was bot-block on a bare curl UA, not a
  dead page — browser UA returned 200. Confirm status with the browser UA
  before reporting anything broken.
- Heading-widget misuse: ElementsKit `ekit-heading` widgets render section
  titles as H2 — a copyright line built that way pollutes heading structure
  AND hardcodes the year (© 2025 still showing in Sep 2026).
