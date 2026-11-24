# Cloned Elementor sites: finding and fixing contamination

When a site was built by cloning a template kit or another client's build, it carries the
original owner's links, images and fonts. They are invisible on a healthy-looking page —
the design renders fine, the link just goes to someone else's business.

Proven on Zagros Tyre and Auto Centre (Sep 2026), where the footer's Google icon had been
sending customers to **K.N Automotive Ltd** in Thorpe Arch for months.

## First: establish that it IS a kit import (`wp plugin list`)

Provenance is in the plugin inventory, and it is the cheapest evidence you will get:

```
envato-elements        active     # the kit delivery plugin
wordpress-importer     active     # what imported the kit's demo content
```

Those two together mean the build came from an **Envato Elements template kit**, which predicts
the whole finding set before you look at a page:

- the kit author's **demo address, phone number and map pin** in the shared footer and on the
  contact page (a US address and a landmark map embed are both common)
- the kit's **stock testimonial names and photographs**, presented as the client's own customers
- **lorem ipsum** in any section the builder did not fill
- the kit's **promo videos**, embedded from the author's own YouTube channel
- images still **hot-linked from the author's demo server**

Name the kit. The demo asset URLs carry it (`elementor-kits-0N.<author>.com/<kit-slug>/
wp-content/uploads/...`), and it tells the client exactly which content is a placeholder and
which is theirs.

### Hot-links to the author's demo server are a different defect from a stale staging host

A stale staging host is the *client's own* dead domain. A hot-link is worse in one specific way:
the asset lives on a **third party's** server that can be tidied away at any time, so the page
loses images with no change on the client's side at all. Count them out of `_elementor_data`
rather than the rendered page — Elementor may not render a section at all, so the served HTML
understates the exposure — and report the count as the exposure.

## The sweep — run this before trusting any cloned site

Enumerate every distinct external URL in the stored Elementor data and the menus, then
check each one actually belongs to the client:

```php
$rows = $wpdb->get_results(
  "SELECT p.post_id, p.meta_key, p.meta_value, po.post_type, po.post_title
   FROM {$wpdb->postmeta} p JOIN {$wpdb->posts} po ON po.ID = p.post_id
   WHERE ( p.meta_key LIKE '%elementor_data%' OR p.meta_key LIKE '%menu_item_url%' )
     AND po.post_status NOT IN ( 'inherit', 'trash', 'auto-draft' )"
);
// then str_replace( '\\/', '/', $meta_value ) and regex for https?://[^\s"'<>\\]+
```

**Filter out `post_status = 'inherit'` or the result is useless.** Elementor stores a
revision per save, and every one still holds the old URLs. A first pass on Zagros returned
~40 hosts; almost all were revisions of the same two templates. Only the live rows matter.

Sort by host and group by post. What to look for:

- **Another business's name** in a social or Maps link (`facebook.com/people/KHautos-...`)
- **The staging host** in image, background and font URLs
- **Another client's domain** (`saautos.co.uk`, `example.com`)
- Bare social domains with no profile (`https://www.instagram.com`) — a dead end, flag it

Resolve every short link rather than eyeballing it. `g.co/kgs/...` resolves to a Google
search URL whose `q=` and `kgmid=` identify the business:

```bash
curl -sS -L -A "<browser UA>" --max-time 45 -o out.html -w '%{url_effective}' "https://g.co/kgs/XXXXXXX"
```

`maps.app.goo.gl/...` serves a JS-redirect stub to a desktop UA; use a **mobile** UA to get
the real destination. That is exactly how the Zagros footer link gave itself up.

## Fixing a wrong Maps link

**Also check for duplicate social profiles, not just links.** The same cloning that puts another
business's link on the site often means the page itself was renamed from a different business —
look for a legacy vanity URL that still redirects (Zagros's Facebook was originally
`facebook.com/Leeds-Tyre-Barrack-Road-...`, renamed but with the old URL live). And check whether
the client has *more than one* page for the same business, exactly as you would check for
duplicate Google Business Profiles: Zagros had two — a 27-follower page linked from the site and
an unlinked 7-like `people/Zagros-Tyre/...` page — which splits the same audience the two GBPs do.
Search `facebook.com`, `instagram.com`, `tiktok.com`, `youtube.com` and `x.com` for the business
name plus town before concluding an account does not exist; then say plainly that absence of
evidence is not proof, because a small garage's account may simply not rank.

The correct destination is the **CID**, not a short link and not a name query. Open the
listing in a browser, capture the place URL, and take the hex after `0x...:` in the `1s`
parameter — that is the CID in hex:

```
.../maps/place/<Name>/data=!4m7!3m6!1s0x48795f031df65437:0x247e364134b98e1f!8m2!3d53.78...
                                             ^^^^^^^^^^^^^^^^^^ CID
```

```python
int('247e364134b98e1f', 16)   # -> 2629598886116298271
```

Then link `https://maps.google.com/?cid=<decimal>`. Short, permanent, survives a business
rename, and opens the Maps app on mobile. The documented `maps/search/?api=1&query=...` +
`query_place_id=ChIJ...` form also works — both verified.

## The ghost-font bug (whole site renders in fallback type)

Elementor downloads Google Fonts locally to `wp-content/uploads/elementor/google-fonts/`
and bakes the **site URL at download time** into the generated CSS:

```
wp-content/uploads/elementor/google-fonts/css/montserrat.css   <- src: url(http://staging-host/...)
```

If the site was styled on staging, every `@font-face` src points at the dead staging domain.
The fonts are on disk and serve 200 from the live domain — only the URL is wrong. SG
Optimizer concatenates these files into the combo bundles, so the bad URLs spread site-wide.

**Flushing Elementor's CSS cache does NOT fix it** — the stale URL is in a static file, not
in generated CSS. Rewrite the files:

```bash
cd wp-content/uploads/elementor/google-fonts/css
cp *.css ~/font-css-backup-$(date +%Y%m%d-%H%M%S)/
sed -i 's|http://<staging-host>|https://<live-domain>|g' *.css
```

Then `wp sg purge` and `wp elementor flush_css`. Verify from the **served bundle**, not the
source files: fetch the `siteground-optimizer-combined-css-*.css` the page actually links,
and confirm 0 stale refs and a matching count of live ones. Confirm a sampled file really is
a font by its magic bytes (`wOF2` = `774f4632`) — a 200 only proves *something* came back.

Elementor also bundles `placeholder.png` as the default for empty backgrounds. A section
cloned from a template carries it as a real background image. Blank the URL rather than
leaving a 404: it is a grey placeholder, never a design asset.

## A CTA rendering `href="#"` has no `link` setting — not an empty one

Scanning `_elementor_data` for empty or `#` URL values finds **nothing** on these builds, which
reads as "no dead links". A button widget the kit never wired up simply has no `link` key at all
— the key is absent, not blank — and Elementor renders `href="#"` for that case. So detect it
from the rendered markup and fix it from the data; the two need different patterns:

```bash
# detect: the button markup itself, not the stored data
grep -o -E '<a[^>]*elementor-button[^>]*href="#"' page.html
```

Distinguish this from a *lapsed* destination (a subdomain or short link that used to resolve and
now does not) — that one is present in the data and only fails when fetched, so a data scan finds
it and a markup scan does not.

Fix by adding the missing `link` setting to that widget's settings object, applying the safe-write
pattern below (snapshot, `wp_slash`, delete the Elementor caches). **Wire only the CTAs whose
destination is unambiguous.** A menu item for a product that has no page, or a "More Info" band
pointing at nothing, is a content question for the client — list those rather than picking a
target, and report how many buttons are affected either way.

## Editing stored Elementor JSON safely

**Elementor stores escaped forward slashes (`\/`).** `get_post_meta()` returns the stored
value as-is, so `strpos( $data, 'https://example.com/page' )` returns false even though the
link is right there. Match the escaped form, or normalise both sides first:

```php
$s = str_replace( '\\/', '/', $data );   // normalise, then match normally
```

**This bites `wp search-replace` too, and it fails silently.** Replacing a full URL
(`example.com/page` → `target.com/page`) reports only a handful of matches because the
Elementor data holds `example.com\/page`. Replace the **host only** and let the trailing slash
fall where it lands — the host has no slashes in it, so the pattern matches inside both the
escaped and the plain form, and both produce the right URL:

```bash
# catches https://old.com/x  AND  https:\/\/old.com\/x
wp search-replace 'old.com' 'new.com/target-page' --all-tables --skip-columns=guid
```

Confirm the scale with `--dry-run --format=table` first, and check for variants the pattern
misses: `metadata LIKE '%old.com%' AND metadata NOT LIKE '%old.com/%'` is what exposes the
escaped rows (85 of them on Zagros).

### Sweeping a stale staging host out of a whole database

The Elementor data, not just the CSS, is full of the old staging domain. Order matters — host
first, scheme second:

```bash
wp search-replace 'staging-host.com' 'live-domain.co.uk' --all-tables --skip-columns=guid
wp search-replace 'http://live-domain.co.uk' 'https://live-domain.co.uk' --all-tables --skip-columns=guid
wp option update siteurl 'https://live-domain.co.uk'
wp option update home    'https://live-domain.co.uk'
wp rewrite flush --hard
```

`--skip-columns=guid` always: the guid is a permanent identifier, never a URL to fetch, and
rewriting it is wrong even though it looks untidy. Check the http→https redirect is already
working before you flip the options, or you take the site down. The count that matters is rows,
not occurrences — `--format=count` per table tells you which tables you are actually touching
(revisions included, which is fine and desirable).

This also means round-tripping data through `json_decode`/`json_encode` in Python produces
plain slashes and is **not** byte-identical to what Elementor wrote — harmless to Elementor,
but it will fail a naive equality check. Prefer `str_replace` on the raw stored string for a
pure URL swap so the diff is exactly the strings you meant to change; when the change is
**structural** (adding or removing a widget, rewriting nested settings) you have to decode and
re-encode, and that is where the trap below lives.

### Re-encoding a structurally-edited tree — the double-escape trap

**Never `str_replace( '/', '\\/', $json )` on `wp_json_encode()` output.** `json_encode`
*already* escapes every `/` as `\/`, so the extra pass turns it into `\\/`, which decodes back to
a literal backslash and prints on the page as visible text: `</p>` renders as `<\/p>` and a link
becomes `https:\\/\\/…`. It is easy to introduce while "matching Elementor's own escaping", and
it corrupts good data as well as bad. The correct write is exactly this and nothing more:

```php
update_post_meta( $id, '_elementor_data', wp_slash( wp_json_encode( $tree ) ) );
```

Verify by **decoding what you stored** and asserting no settings string still contains a
backslash — an equality or byte-length check passes happily while the page is visibly broken:

```php
$left = 0;
$w = function ( $n ) use ( &$w, &$left ) {
    if ( ! is_array( $n ) ) return;
    foreach ( ( $n['settings'] ?? [] ) as $v ) {
        if ( is_string( $v ) && false !== strpos( $v, '\\' ) ) $left++;
    }
    foreach ( $n as $c ) $w( $c );
};
$w( json_decode( get_post_meta( $id, '_elementor_data', true ), true ) );
```

To repair data that is already double-escaped, collapse any run of backslashes standing before a
slash, then re-encode normally: `preg_replace( '/\\\\+\//', '/', $v )` on each settings string.

**Detect it in the rendered page, not the data.** A literal `<\/p>`, `<\/span>`, `<\/a>` or
`<\/strong>` in the served HTML **is** double-escaped stored data. Sweep for it with
`grep -o -E '<\\+/[a-z0-9]+>'` on the live page — and note a footer credit line is a common
casualty, so our own branding can be the thing rendering as broken code.

**`_elementor_data` is a top-level ARRAY of elements, not an object.** A recursive walker that
starts at the root with `$tree['elements']` silently finds nothing and reports "0 matches, nothing
to fix" on the key you are hunting. The array *does* use `elType` / `widgetType` / `elements`, but
only from the first element down:

```php
foreach ( $tree as &$top ) { $walk( $top ); }   // NOT $walk( $tree['elements'] )
```

Missing this is how a widget-removal pass reports "recaptcha widgets removed: 0" on a page that
plainly has one. If a walker returns zero, check the root shape before believing it.

Pattern that makes every write reversible and self-checking:

```php
update_post_meta( $id, '_elementor_data_backup_YYYYMMDD', wp_slash( $current ) );  // rollback copy
update_post_meta( $id, '_elementor_data', wp_slash( $new ) );
foreach ( [ '_elementor_css', '_elementor_element_cache', '_elementor_page_assets' ] as $k ) {
    delete_post_meta( $id, $k );   // or the edit will not show
}
WP_CLI::line( get_post_meta( $id, '_elementor_data', true ) === $new ? 'OK' : 'DIFFERS' );
```

Guard the write on the old value still being present, and abort if not — that is what stops
a script clobbering an edit the client made in the editor in the meantime.

## `wp eval-file` argument gotchas

- **`--anything` is parsed as a WP-CLI global flag**, not passed to your script; you get
  `Error: unknown --apply parameter`. Pass **positional** args and read `$args`:
  `wp eval-file script.php apply` → `in_array( 'apply', $args, true )`.
- Put the script in a file and `scp` it, rather than piping a heredoc over SSH. Heredocs
  mangle PHP (backslashes, parentheses, nested quotes) and fail in ways that look like PHP
  bugs — including `wp eval-file /dev/stdin`, which errors outright because the redirect
  never creates the file. Every heredoc attempt on Zagros broke; every `scp` + `wp eval-file`
  worked.
- **`wp option patch update` only works on JSON options.** Yoast stores `wpseo_titles`,
  `wpseo_social` and `wpseo` as serialised PHP arrays, so it fails with `Error: No data exists
  for key "..."`. Use `wp eval-file` and update the array directly.

## Scope discipline

Rewriting the client's own navigation to point at a new page, or changing the entity name in
a legal line, alters something the client set up deliberately. Fix what is **provably broken**
(a dead host, a link to another business, a stale year) and report the rest with the exact
command. On a copyright line, the registered entity name is checkable at Companies House —
verify it there rather than inferring it from the domain or the trading name.
