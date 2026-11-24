# Applying fixes to a live Elementor site over WP-CLI

For the second half of a QA job: the report is written, access has been granted, and the fixes are
yours to apply. Read `elementor-page-building-via-wp-cli.md` first for the `wp_slash()` and
never-open-the-editor rules; this file covers **editing widgets that already exist**.

## Find where the defect actually lives before editing anything

A string that renders on every page is usually in an `elementor_library` template, not in each
page. Changing it once in the template beats nine page edits.

```bash
wp --path=$W post list --post_type=elementor_library --post_status=any \
   --fields=ID,post_title,post_name
wp --path=$W db query "SELECT post_id, meta_key FROM pza_postmeta \
   WHERE meta_key LIKE '%elementor%' AND meta_value LIKE '%SEARCHSTRING%'"
```

Get the real table prefix from `wp db prefix` — do **not** assume `wp_`. A guessed prefix returns
`Table '...wp_postmeta' doesn't exist` and looks like a permissions problem.

The hit list will include **revisions** (post_type `revision`) and `_elementor_element_cache` rows
alongside the live posts. That is expected and informative: it tells you the blob is duplicated
across revisions and caches, so a single-post edit will not clear it everywhere.

## `_elementor_element_cache` is the trap that makes a correct fix look broken

Elementor stores rendered element HTML in this postmeta key. It **survives `wp search-replace` on
`_elementor_data`**, so a page keeps serving the old text after you have correctly changed the
source data — the classic "my edit didn't take".

Delete it for the affected posts (or all of them; it regenerates) after every data change:

```bash
wp --path=$W db query 'DELETE FROM pza_postmeta WHERE meta_key="_elementor_element_cache"'
wp --path=$W sg purge && wp --path=$W cache flush
```

Three extensions learned the hard way on a live header template:

- It is stored in **two** places — the postmeta key above **and** an option (`%element_cache%` in
  `pza_options`). Clear both.
- When the stale markup is in a **template** (header, footer, global widget), the cache row belongs to
  the *template* post, not to the page you are editing. Deleting it for the page changes nothing, and
  the page keeps serving the old phone number while `get_post_meta` proves the data is correct.
- **Check the response header before concluding anything.** SiteGround answers `x-proxy-cache: HIT`
  from its front cache even for a query-string buster, and `wp sg purge` does not always bust it — so a
  fresh render has to be forced with a User-Agent the site has not seen (`x-proxy-cache: MISS`). A HIT
  is not evidence your write failed.

## Blank-string fixes: `wp search-replace` is safe, and dry-run it first

Serialized and escaped storage is handled for you. Always `--dry-run --report-changed-only` first
and read the counts — a count far higher than the number of pages is the signal that the string is
sitting in revisions and caches too, which is fine; a count that looks like it hit body copy is not.

```bash
wp --path=$W search-replace 'OLD' 'NEW' --all-tables-with-prefix --precise --dry-run --report-changed-only
```

**Do not blanket-replace a hostname prefix.** `pza_posts.guid` is a permanent identifier, is never
rendered as a link, and rewriting it is the classic WordPress own-goal. Scope the replacement to
the tables that emit URLs — usually `pza_postmeta` and `pza_users` — and leave `guid` on the old
scheme. Confirm what you left behind explicitly so it does not read as an oversight:

```bash
wp --path=$W db query 'SELECT COUNT(*) FROM pza_posts WHERE guid LIKE "http://%"' --skip-column-names
```

After clearing `siteurl`/`home`, re-run any generator that used `home_url()` — the URLs it wrote
earlier still carry the old scheme.

## Elementor button widgets with no link render as `href="#"`

A scan for empty `url` values finds **nothing**, because the `link` key is absent from
`settings` entirely — not present-and-blank. Elementor emits `href="#"` for a `button` widget with
no link configured. Enumerate by walking for `elType == 'widget' && widgetType == 'button'` and
printing `settings.text` together with whether `settings.link.url` is set; that inventory is the
finding, and it is what you paste into the report.

Normalise typographic characters before matching button text. Curly apostrophes are the norm in
Elementor content, so `Let's get you moving` will not match the stored `Let’s get you moving`.
Compare on a normalised copy (`’` → `'`, trimmed, lowercased) and keep the original for the write.

## Write `_elementor_data` with a self-verifying, self-rolling-back script

Hand-rolled shell JSON manipulation on live content is where sites break. Put the read, the
mutation, the write and the verification in one `wp eval-file` script, so a failure restores the
original instead of leaving invalid JSON:

1. `get_post_meta($id, '_elementor_data', true)` and write the raw value to a timestamped file.
2. `json_decode`; **abort if it does not decode** — never write to something you could not read.
3. Walk the tree and mutate `settings` on matched widgets.
4. `update_post_meta($id, '_elementor_data', wp_slash(json_encode($data)))`.
5. `clean_post_cache($id)`, re-read with `get_post_meta`, `json_decode` **again**, and confirm the
   expected keys are present.
6. If step 5 fails, `update_post_meta` the original straight back and exit non-zero.

Default the script to dry-run and require an explicit `apply` argument (read it from `$args` in
`wp eval-file`). Then you get the inventory for free, and the destructive path is deliberate.

**Do not pre-escape the slashes on the way out.** Elementor's stored JSON shows `\/`, which tempts
you into `str_replace('/', '\\/', json_encode($data))` before writing. `json_encode` has *already*
escaped them, so that doubles the escape: the value round-trips to a literal backslash and the page
renders `\/p>`, `\/span>`, `\/a>` as visible text — including in whatever widget the **client**
reads, such as the agency credit line in the footer. Write `wp_slash(json_encode($data))` and nothing
else. To detect an existing double-escape, decode and look for a backslash in the *decoded* string
values; grepping the raw JSON for `\/` matches correct files too, so it proves nothing.

React to a refusal correctly: `wp eval-file` returning "no matches" without writing means the map
keys do not equal the stored text — usually the apostrophe case above — not that the widgets are
missing.

## Verifying what you changed

Read the served HTML **from the server** (`curl` the public URL over SSH), never through a
third-party render API — those cache aggressively and will hand you a pre-change page after your
change has landed, which reads exactly like a failed write.

Parse with `python3` on the server, not chained `grep`/`sed`. Three separate false negatives in one
session, all quoting or ordering:

- **Quote style.** WordPress emits `<meta name='robots' content='noindex, nofollow' />` with
  **single** quotes. A grep for `name="robots"` reports the fix as not applied. Use
  `name=['\"]robots['\"]`.
- **Attribute order.** Elementor writes `class` **before** `href` on buttons. A regex assuming
  `href` comes first matches nothing and looks like a failure.
- **`\x` escapes in shell-quoted patterns.** `sed 's/\x27//'` and `grep '[\x27"]'` do not reliably
  expand. If a quoted pattern is getting fiddly, switch to `python3 -c` and stop fighting it.

Check the thing that changed, per page, as a table — page, the fixed attribute, the count of the
old defect (must be 0), and the count of the new value (must be ≥1). A fix counts as verified only
when the old value is absent and the new one is present, not when the command exited 0.

## Mutating a node deep in the tree: references that silently discard the write

Two PHP patterns look correct, produce no error, and write nothing. Both cost a full debugging cycle:

- **A function returning a reference, bound with `=&`.** `$node = &etf_ref($data, $path);` binds to the
  function's *return value* (a temporary), not into `$data`. Reads work; writes vanish. Descend inline
  at the point of use instead:
  ```php
  $n = &$data[$path[0]];                                  // first hop: index into the root array
  for ($i = 1; $i < count($path); $i++) { $n = &$n['elements'][$path[$i]]; }
  ```
- **`foreach` over an expression with `??`.** `foreach ($x['elements'] ?? array() as $i => &$v)` iterates a
  *temporary*, so `$v` is not bound to the stored data. Assign to a variable first, then iterate it.

A recursive closure taking `&$nodes` and mutating `$n` through `foreach ($nodes as &$n)` **does** work —
that pattern is fine. It is specifically functions that `return $n;` that break.

**Path helpers index `elements` arrays, not the node.** A helper that walks `$nodes` and returns
`array_merge($path, array($i))` gives you indices into *successive* `elements` arrays. Descending with
`$d[$p0][$p1][$p2]` is wrong and returns null; the correct traversal has an `elements` hop between every
pair, as above.

**`_elementor_data` decodes to a top-level ARRAY of elements, not an object.** A walker that opens
with `foreach ($data['elements'] as ...)`, or a counter that reads `$data['elements']`, finds nothing
and reports **zero matches** — which reads as "the widget is not on this page" and sends you looking
for a different cause entirely. Iterate the root array itself (`foreach ($data as &$top) { walk($top); }`)
and descend through `elements` from there. Print the decoded root's `gettype` and `count` before writing
any matcher, so an empty result is a finding on your traversal rather than on the site.

## Verify against the rendered output, not just the stored data

A data write can be correct and still change nothing on screen.

- **Slide/carousel backgrounds and many widget styles live in Elementor's generated CSS**, at
  `wp-content/uploads/elementor/css/post-<id>.css` — not inline in the HTML. After changing image URLs in
  `_elementor_data`, run `wp elementor flush_css` and then **view the pages** so the CSS regenerates
  (flushing deletes the files; they rebuild on the next request). Without this the data is right and the
  slider is still blank.
- **Screenshot APIs cache by URL.** A re-fetch can hand back the pre-change render, identical byte size
  and all. Append a unique query string (`?cb=<timestamp>`) to bust it.
- **Elementor entrance animations break headless captures.** Elements with `animation: fadeIn` are served
  with `elementor-invisible` and only appear once Elementor's JS runs. In a screenshot one column may
  show and its neighbour not, which reads exactly like a layout you broke. Check the markup for
  `elementor-invisible` before investigating a layout fault — and note it as a real robustness issue when
  the content is something like a footer phone number.

## Match stored text exactly

Elementor stores a literal `&` in a slide heading, not `&amp;` — a key written as `Black Cab &amp; Uber`
matches nothing while every other key matches, so exactly one slide silently keeps the old image. Print
what is stored and copy it verbatim rather than typing the display text. The same trap applies to
curly apostrophes and to HTML written into widget settings (`Legal &amp; Compliance :`).

## Reading a `wp eval-file` failure

WordPress's fatal-error handler prints a full HTML page, so `tail` on the output shows you CSS and
`<body id="error-page">` while burying the actual `Fatal error:` line above it. Pipe to `head`, and grep
out the noise. A fatal in a script that writes at the end of each block leaves the earlier blocks
applied — so make a follow-up run **idempotent**: look up each target by id and skip it with a note
rather than `WP_CLI::error()`-ing out when it is already done.

## House pattern: a sibling brand is your source of truth

When a new build is for the same client as an existing site, the existing site is the reference for
anything legal or regulatory — address, company number, FRN, VAT, the compliance footer block. Pull
it directly rather than inventing wording. Two corollaries worth raising:

- **A shared form is a shared defect.** If the new site's finance/application form is a copy of the
  sibling's, every defect in it exists on both sites. Say so — it changes the fix from "fix this
  build" to "fix the pattern", and it is the kind of thing the client will want to hear from you
  before they hear it from someone else.
- **Place the regulated wording verbatim or not at all.** A trading-name variant of an FCA
  statement ("X is a trading name of Y Ltd") is a regulated sentence. Confirm the entity with the
  client and reproduce the sibling's block exactly; never paraphrase it into place.
