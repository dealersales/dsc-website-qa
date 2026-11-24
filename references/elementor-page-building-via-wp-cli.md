# Building Elementor pages safely via WP-CLI over SSH

Proven on Zagros Tyre and Auto Centre (Sep 2026): seven service pages created on a live
Elementor 4.2.4 / Hello Elementor site, matching the existing design, with no editor visit.

Use this whenever a job is **"add N pages to, or insert/restyle a widget on, an existing Elementor
site"**. It is the whole procedure — reconnaissance, generation, import, verification.

## Never open the Elementor editor on a live site

Booting the builder loads the entire `_elementor_data` payload into memory. On a
memory-tight host that can 500 the site outright and take your access with it. Write the
meta directly instead. `wp eval-file` with a script that builds the JSON is the safe route.

## 1. Reconnaissance — what to find before generating anything

```bash
cd ~/www/<domain>/public_html
wp option get siteurl                  # confirm the install AND whether it is http or https
wp post list --post_type=page --fields=ID,post_title,post_name,post_status --format=csv
wp post-type list --fields=name,label --format=csv | grep -i elementor
```

**The single most valuable lookup: the site's own reusable templates.** Elementor keeps
them in `elementor_library`, and a template kit or a previous build often left exactly the
page skeleton you need:

```bash
wp post list --post_type=elementor_library --fields=ID,post_title,post_status --format=csv
# type is in meta, and tells you which are header/footer/section/page templates
wp post meta get <id> _elementor_template_type
```

On Zagros, `Service page template sa` (id 151) was a ready-made service-page skeleton —
hero, intro, content grids, CTA. Cloning its sections is what made the new pages
*indistinguishable* from the existing ones, which hand-authoring would never have achieved.

Confirm what a full page carries, so you replicate it exactly:

```bash
wp post meta list <existing-page-id> --fields=meta_key,meta_value --format=csv
```

## 2. The meta an Elementor page needs

The four that matter, copied from a working page rather than guessed:

| meta key | value | why |
|---|---|---|
| `_elementor_edit_mode` | `builder` | without it Elementor renders nothing |
| `_elementor_template_type` | `wp-page` | `wp-post` is for posts |
| `_elementor_page_settings` | `['hide_title' => 'yes']` | **stops the theme printing a second title alongside your hero H1** |
| `_elementor_data` | JSON, see below | the page itself |

`_wp_page_template` is `default` on Hello Elementor, and `_elementor_version` should match
the site's existing pages, not necessarily the installed plugin version.

## 3. Writing `_elementor_data`

Elementor stores its JSON **slashed**, because `update_post_meta()` unslashes on write:

```php
update_post_meta( $id, '_elementor_data', wp_slash( $json ) );
```

Omit the `wp_slash()` and the stored JSON is subtly corrupted — it looks fine in a
`get_post_meta()` read-back and breaks on render.

Three traps in the JSON itself:

- **Heading titles are stored with a plain `&`, not `&amp;`.** Elementor escapes on output.
  Check an existing page to confirm the convention on that site before writing yours:
  `wp post meta get <id> _elementor_data | grep -o '"title":"[^"]*"'`
- **`header_size` sets the tag.** The hero heading wants `"h1"`; the heading widget defaults
  to `h2` when unset, so body sub-headings need `"h3"` explicitly.
- **Clone, don't hand-author.** Deep-copy sections from the template and change only the
  text, then renumber every `id` (7 hex chars) so they are unique within the page. All the
  responsive padding, global-kit colour references and animation settings come along for
  free — which is exactly what makes the page look native.

Also strip template-kit leftovers. Zagros's template CTA button still pointed at
`https://saautos.co.uk/contact-us/`; a leftover like that is a live link to a stranger's
site. Point CTAs at a **relative** `/contact-us/` so they survive a domain move.

## 4. Import, idempotently

Match on slug with `get_page_by_path()`, so a re-run updates rather than duplicating. After
writing the meta, delete the generated caches so Elementor and SG Optimizer rebuild them:

```php
delete_post_meta( $id, '_elementor_css' );
delete_post_meta( $id, '_elementor_element_cache' );
delete_post_meta( $id, '_elementor_page_assets' );
```

```bash
wp elementor flush_css
wp sg purge
wp cache flush
```

## 5. Verifying — do all four

**Do not verify by comparing the read-back against `wp_slash($json)`.** `get_post_meta()`
returns the *unslashed* value, so that comparison always reports a false MISMATCH. Compare
against the original JSON string:

```php
$stored = get_post_meta( $id, '_elementor_data', true );
$ok = ( $stored === $original_json ) ? 'BYTE-IDENTICAL' : 'DIFFERS';
```

Then:

1. **Fetch the page from the server**, not your workstation — SiteGround's bot wall will
   serve *you* a challenge page and make a working page look broken:
   `ssh … "curl -s https://<domain>/<slug>/"`
2. **Count the headings.** Exactly one `<h1>` (proves `hide_title` worked and the theme is
   not printing its own title), then h2 for sections, h3 for sub-sections.
3. **Visual check.** Local `file://` renders unstyled — the `<link>` to the combined CSS
   either fails or is bot-walled, and you get giant unstyled icons. Fetch the page **and**
   the `siteground-optimizer-combined-css-*.css` bundle from the server, inline the CSS into
   a local copy, then screenshot with headless Chrome and inspect:
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless=new \
     --disable-gpu --hide-scrollbars --no-sandbox --window-size=1440,3400 \
     --virtual-time-budget=15000 --screenshot=out.png "file://$PWD/vis-page.html"
   ```
   Compare the hero region of a new page against an existing one at full resolution — a
   region crop, not the whole downscaled page. The header and hero should be pixel-identical.
4. **Sitemap and canonical.** `wp-sitemap-posts-page-1.xml` should pick up the new pages by
   itself; check each returns 200 with a self-referencing canonical and no `noindex`.

## 6. Menus

```bash
wp menu item add-post <menu-id> <post-id> --parent-id=<parent-db_id> --title="<label>"
wp menu item list <menu-id> --fields=db_id,title,menu_order --format=csv
```

**`menu_order` is a single FLAT sequence across every item in the menu, parents and
children together** — it is not per-parent. Setting a value that collides with an existing
item silently reshuffles the whole menu (Zagros: setting a parent to `2` while a child already
held `2` pulled a page out of the nav entirely). Read the current flat order first, then
assign unique consecutive integers across all items, parent immediately before its children.

Note `wp post get <nav_menu_item_id> --field=post_title` returns empty for menu items even
when the label renders correctly — verify the menu from the rendered HTML, not from that.

## 7. What to leave alone

Building pages is additive and low-risk. Changing `siteurl`/`home`, repointing the client's
existing links, or editing a shared header/footer template are **not** — they alter things
the client deliberately set up. Report them with the exact command and let the owner decide.
Zagros's `siteurl` is `http://` on an HTTPS site; it works because something in the stack
rewrites URLs on output, and it is still worth fixing — but not unasked.

## 8. Inserting or restyling a widget on an existing page

Same mechanics as building a page — decode `_elementor_data`, mutate the tree, write it back with
`wp_slash( wp_json_encode( $tree ) )` — but buttons carry inheritance traps that make a
technically-correct insert look broken.

**Elementor only emits typography controls when `typography_typography` is `'custom'`.** Settling
`typography_text_decoration: 'none'` on a widget that inherits its typography is *silently ignored*;
the theme's `a { text-decoration: underline }` wins and the button renders underlined anyway. Set
the custom flag (with family/weight/size) on anything you need decoration control over, or accept
that the control will not apply.

**A newly inserted widget inherits the theme's `.elementor-button` rules.** Expect an inherited
border, an underline and the site's text colour — none of which match what you intended. Set them
explicitly: `border_border: 'none'`, `typography_text_decoration: 'none'` (with the custom flag
above), `button_text_color`, and the hover siblings.

**Re-purposing an existing button keeps its inherited colours, which may be illegible.** A theme
whose buttons are white-on-yellow is ~1.4:1 contrast; changing only the text and URL leaves it
unreadable. Set `button_text_color` whenever you touch a button's content, and check the contrast
of the theme-wide button style before assuming it is fine.

**When a per-widget fix will not take, use one contained CSS rule — not a global restyle.**
Append to the existing stylesheet rather than replacing it:
`wp_update_custom_css_post( wp_get_custom_css() . $rule )`, targeting the single element id, not
`.elementor-button` site-wide. Changing every button's colour across a client's site is a design
decision for the owner; flag it and let them choose.

**Verify visually, not by counting links in the markup.** An element count proves the button exists
and proves nothing about whether it is legible. Screenshot the CTA region and look at it.

## 9. Header and navigation

A header that "looks basic", or a menu that overlaps its box, is usually **structural** rather than
cosmetic. Diagnose before styling or you make a prettier broken menu.

**Check column widths before touching the nav.** Elementor classic columns size through
`_inline_size` (a percentage). A menu column at ~20% (≈288px at 1440) cannot hold four top-level
items; the `ul` keeps its background while the wrapped row spills *outside* it, which reads as a
broken dark box with a stray link underneath. Rebalance `_inline_size` across the header columns
and keep the sum at 100. Dump the header template's section/column settings first.

**A column carrying `border_border: solid` at 1px renders as a placeholder-looking outline** around
the social icons or the menu. That is a leftover column border, not a theme style — remove it unless
the design genuinely wants a frame.

**An icon list with no icon still draws a box.** PowerPack `pp-info-list` items with
`icon: { value: "", library: "" }` but `icon_size` / `icon_bg_color` set render a bare coloured
square — the "white square above the phone numbers". Hide the wrapper rather than editing items:

```css
.elementor-element-<widget-id> .pp-infolist-icon-wrapper { display: none !important; }
```

**Max Mega Menu markup**, when the nav is MMM:

```
#mega-menu-wrap-<location>
  ul#mega-menu-<location>.mega-menu.max-mega-menu
    li.mega-menu-item > a.mega-menu-link
```

States and parts: `.mega-current-menu-item`, `.mega-current-menu-ancestor`,
`.mega-current-menu-parent`, `.mega-menu-flyout` (dropdown), `.mega-menu-toggle` (mobile). MMM's
theme CSS is high specificity — use `!important` on the properties you must win instead of escalating
selectors. Single-row pattern: `display:flex; flex-wrap:nowrap` on the `ul`, `float:none` on the
`li`, `white-space:nowrap` on the link.

A page that is both current **and** an ancestor of a child lights two items at once
(`.mega-current-menu-item` plus `.mega-current-menu-ancestor`). That is correct behaviour — style it
as a subtle underline so it does not read as two active tabs.

**Adding a CTA item to the nav:**

```php
$id = wp_update_nav_menu_item( $menu_id, 0, [
    'menu-item-title'    => 'Book MOT',
    'menu-item-url'      => home_url( '/mot-testing-leeds/' ),
    'menu-item-status'   => 'publish',
    'menu-item-type'     => 'custom',
    'menu-item-position' => $max_order + 1,
    'menu-item-classes'  => 'menu-cta',
] );
update_post_meta( $id, '_menu_item_classes', [ 'menu-cta' ] );
```

**Write `_menu_item_classes` explicitly.** Passing `menu-item-classes` to `wp_update_nav_menu_item()`
is not reliably persisted on its own, and without the class the CTA selector silently matches nothing.
Style `li.menu-cta > a.mega-menu-link`, and repeat the rule for `:hover` and
`.mega-current-menu-item` so it keeps its look when that page is open.

**Check both widths.** Desktop ~1440 **and** below MMM's `data-breakpoint` (768 by default). A
restyle verified only on desktop routinely leaves the mobile toggle broken or the CTA missing.

**Changing the theme-wide button or nav colour is the owner's design decision.** Apply it to the
element you were asked to change and flag the site-wide version instead — see the contrast note in
§8.
