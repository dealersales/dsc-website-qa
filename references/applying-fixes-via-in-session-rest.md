# Applying client-site fixes via in-session REST (WordPress / Elementor)

Companion to `dsc-website-qa`. Use when the QA pass turns into *making* the fixes the client asked
for, on a site whose `/wp-json` is not reachable by scripts.

## Why in-session REST

SiteGround's `sgcaptcha` can gate the entire `/wp-json` path for outside clients — reads included:

```bash
curl -s -D - -A "<browser UA>" https://CLIENT/wp-json/wp/v2/pages
# HTTP/2 202
# sg-captcha: challenge        <- body is a /.well-known/sgcaptcha/ meta-refresh
```

That also defeats Application Passwords, and it can start **mid-session** after a burst of requests
(IP/rate based). The workaround: call REST from inside a logged-in wp-admin tab — same origin, real
session cookie, challenge already passed.

```python
import json
nonce = js("(() => (window.wpApiSettings && window.wpApiSettings.nonce) || '')()")
def rest(path):
    return js("fetch('/wp-json/wp/v2/%s',{headers:{'X-WP-Nonce':%s}}).then(r=>r.json())"
              % (path, json.dumps(nonce)))
# writes: same fetch with method PUT/POST + Content-Type: application/json + JSON-string body
```

Do the JSON traversal **inside the JS** (`JSON.parse` → walk → `JSON.stringify`) and print only
small summaries — `_elementor_data` is megabytes and will flood context if it round-trips through
the agent.

## The edit method is a risk decision, not a convenience one

**Do not open the Elementor editor to change a single value.** For one string — an email
address, a phone number, a label — the editor is the most expensive way to do it: it boots
Elementor's full PHP/JS stack and pulls the entire `_elementor_data` payload (megabytes on a
busy site) into memory. On a memory-tight host that can fatal PHP and take the **whole site**
down, frontend and wp-admin together, which removes the admin access you would use to fix it.

Rank the methods, safest first:

1. `wp post meta get/update`, or a `wp eval-file` script, over SSH — no browser, no builder, and a
   PHP fatal prints to `debug.log` where you can read it. **This is the only method that reliably
   writes `_elementor_data`.**
2. In-session REST `PUT` on `meta._elementor_data` (below) — same-origin, nonce-authenticated — but
   only where that meta key is exposed to REST. On a stock Elementor site it is **not**, and the write
   is dropped in silence while the response still looks successful. Read the value back before
   believing it; if it did not change, stop and go to (1).
3. Browser editor publish — **only** when you specifically need a publish to regenerate the
   compiled CSS, and never as the first move.

**Never test a write path with a placeholder payload** (`{'meta': {'_elementor_data': 'test'}}` and
similar). On a site where the key *is* registered that write succeeds, and you have replaced a page's
entire design with the string `test` on a live client site. Probe on a throwaway draft, or make the
real write once and verify it read-back. WordPress's REST posts controller persists only `meta` keys
exposed in the schema (registered with `show_in_rest`); unregistered keys are ignored, so a 200 means
nothing. Detail: `wordpress-elementor-rest-api` → "A 200 on this PUT is not evidence of a write".

If it has already happened, the payload is recoverable — see *When a payload is already destroyed*
below.

The dashboard offers no fallback for this key either: the classic Custom Fields metabox hides
`_`-prefixed keys from its dropdown by design, and forcing `_elementor_data` through its `add-meta`
AJAX loader with a multi-megabyte value fatals the request. SSH/WP-CLI, `wp search-replace`, or the
host's SQL tool — or nothing.

**Snapshot before every write, and before opening the editor at all.** The editor can take the site
down before you have changed anything, so a snapshot taken afterwards proves nothing:

```bash
wp post meta get <id> _elementor_data > backups/<id>.json
```

**Line up host access before doing the risky thing.** A 500 from an editor session needs SSH or the
host file manager to clear. If you have neither, do not open the editor — do not gamble a client's
live site on a rescue you cannot perform. Re-check the site root returns 200 after every write, not
just the page you edited.

If it does go down anyway: `references/site-down-triage.md`.

## When a payload is already destroyed

A wrecked `_elementor_data` **does not show on the live page.** The rendered HTML is cached
separately from the payload, so a page whose data has been replaced by a short string keeps serving
its old, complete markup — sometimes for hours — and the site looks perfectly healthy. This is the
trap that makes a placeholder write so expensive: the page you would check to confirm the damage
is the one artefact that cannot show it. Judge the payload by reading it **out of the database**:

```sql
SELECT post_id, CHAR_LENGTH(meta_value) AS len, LEFT(meta_value, 60) AS head
FROM <prefix>postmeta WHERE post_id = <id> AND meta_key = '_elementor_data';
```

A healthy payload is large (tens of KB upward) and its head reads `[{"id":"…","elType":"section"`.
A handful of bytes or a bare word means it was destroyed.

**Elementor's own revisions each carry their own `_elementor_data`, so the page is almost always
recoverable even with no snapshot** — which is why the snapshot rule above is a convenience, not the
only safety net. Do not rebuild the layout by hand:

```sql
-- newest revisions that actually hold a real payload
SELECT p.ID, p.post_date, LEFT(pm.meta_value, 50) AS head
FROM <prefix>posts p
JOIN <prefix>postmeta pm ON pm.post_id = p.ID AND pm.meta_key = '_elementor_data'
WHERE p.post_parent = <id> AND p.post_type = 'revision'
ORDER BY p.post_date DESC LIMIT 5;
```

Copy the newest revision whose `head` is a JSON array back over the live post, then confirm the
write landed and rebuild the output:

```sql
UPDATE <prefix>postmeta pm
JOIN <prefix>postmeta rev ON rev.post_id = <revision_id> AND rev.meta_key = '_elementor_data'
SET pm.meta_value = rev.meta_value
WHERE pm.post_id = <id> AND pm.meta_key = '_elementor_data';
SELECT ROW_COUNT();   -- expect 1
```

```bash
wp elementor flush_css      # rebuild the compiled per-post CSS
wp sg purge                 # then the host cache
```

Re-read the published payload to confirm the design is back, then fetch the page **from the server**
(`ssh … 'curl -s https://CLIENT/page/ | grep -c "<expected>"'`) — a server-side request is not
intercepted by the host's proxy cache or bot challenge the way one from your machine is, so it is the
only fetch that tells you whether the data is right or the cache is merely stale.

## Copy that is not in the page's own data

If a string renders on a page but is absent from that page's `_elementor_data` — an email address, a
phone number, a footer line — it lives in a **Theme Builder template**, and editing the page changes
nothing. List them and their type over SSH:

```bash
wp post list --post_type=elementor_library --fields=ID,post_title,post_name --format=table
wp post meta get <id> _elementor_template_type   # section | page | header | footer | single | archive
```

A "Get In Touch" block appearing on every service page is usually one `section` template: fix it once
and every page it renders on is corrected in the same pass. Confirm which template a page uses from
the live HTML (`data-elementor-id="<id>"`) before assuming the page owns the string.

## Locate widgets by context, not by data-id

A widget keeps its `data-id` when a section is copied between pages, so the same id appears on
several pages. Walk the tree tracking the nearest preceding heading / text-editor text:

```javascript
let lastHeading=''; const out=[];
(function walk(els){(els||[]).forEach(el=>{
  if(el.elType==='widget' && ['heading','text-editor'].includes(el.widgetType)){
     let t=String(el.settings.title||el.settings.editor||'').replace(/<[^>]+>/g,' ').trim();
     if(t) lastHeading=t.slice(0,60); }
  if(el.elType==='widget' && el.widgetType==='icon-list')
     out.push({id:el.id, after:lastHeading, items:(el.settings.icon_list||[]).map(i=>i.text)});
  if(el.elements) walk(el.elements); });})(data);
```

## Append a bullet to a checklist section

Bullets are usually split across **two** icon-list widgets for a 2-column layout (1-3 in one,
4-6 in the other) — append to the widget holding the **tail** of the section so the new bullet
lands last.

```javascript
list.push({text:"Jaguar / Land Rover EV and Hybrid Diagnostics and Repairs",
           _id:Math.random().toString(16).slice(2,9),
           link:{url:'#', is_external:'', nofollow:'', custom_attributes:''}});
// PUT /wp-json/wp/v2/pages/<id>   body: {meta:{_elementor_data: JSON.stringify(data)}}
```

No new CSS is needed — Elementor renders widget HTML from the DB per request, so the bullet is live
as soon as the meta saves and the cache is purged. **Confirm the meta saved by reading it back** — if
the value is unchanged, the REST write was dropped and the bullet never existed.

**Editing an existing bullet** (a stale email address, a phone number) is the same walk, and the
label and the link must move together. A contact item is two fields — `icon_list[i].text` and
`icon_list[i].link.url` — so changing one and reloading leaves a bullet whose visible address reads
correct while the `mailto:`/`tel:` still routes to the old recipient. Fix both in the same write, then
confirm the rendered `href` in the live HTML rather than the widget label.

## Create a page that renders as Elementor

`POST /wp-json/wp/v2/pages` → `{title, slug, status:'publish', content:'', meta:{...}}`

| meta key | value | why |
|---|---|---|
| `_elementor_edit_mode` | `'builder'` | **required** — without it the page ignores `_elementor_data` and renders the theme default |
| `_elementor_template_type` | `'wp-page'` | |
| `_elementor_version` | the site's Elementor version | |
| `_elementor_data` | `JSON.stringify([...])` | |

```javascript
[{id:"s1",elType:"section",settings:{layout:"boxed"},elements:[
  {id:"c1",elType:"column",settings:{_column_size:100,_inline_size:null},elements:[
    {id:"h1",elType:"widget",widgetType:"heading",settings:{title:"Gallery",header_size:"h2",align:"center"},elements:[]},
    {id:"g1",elType:"widget",widgetType:"image-gallery",settings:{
        wp_gallery:[{id:867,url:"https://…/x.jpeg"}],gallery_columns:"3",
        thumbnail_size:"large",gallery_link:"file",open_lightbox:"yes",gallery_display_caption:""},elements:[]}
  ]}]}]
```

## Insert a menu item at a position

```javascript
// 1) bump the item that should FOLLOW it
fetch('/wp-json/wp/v2/menu-items/<followingId>',{method:'POST',headers:H,body:JSON.stringify({menu_order:8})})
// 2) create the new item
fetch('/wp-json/wp/v2/menu-items',{method:'POST',headers:H,body:JSON.stringify(
  {title:'Gallery',type:'post_type',object:'page',object_id:1020,parent:0,menu_order:7,menus:2,status:'publish'})})
```

Partial POSTs need only the changed field. Read the menu id from `/wp-json/wp/v2/menus` and current
orders from `/wp-json/wp/v2/menu-items?menus=<id>&per_page=50&_fields=id,title,menu_order,type,url`.

## Purge caches after edits

- Elementor: `DELETE /wp-json/elementor/v1/cache` → 200.
- SiteGround: `document.querySelector('#wpadminbar a[href*="admin_bar_purge_cache"]')` — fetch that
  href, the nonce is in it.

## Widget pitfalls proven in practice

- **Elementor Pro Gallery injected via REST renders nothing.** `widgetType:'gallery'` enqueued
  `widget-gallery` CSS and generated `post-<id>.css` but produced zero markup. The free
  `image-gallery` widget rendered 6 images immediately. **CSS enqueued ≠ markup output** — check
  the DOM (`document.querySelectorAll('.gallery-item img')`, `naturalWidth > 0`).
- **Screenshot ≠ proof of rendering.** Lazy images below the fold photograph as blank; confirm with
  DOM geometry (`naturalWidth`, `getBoundingClientRect().height`) before calling a widget broken.
- **Templates/globals live in `elementor_library`**, not `pages`. Find the active one in the live
  HTML: `data-elementor-id="<id>" class="… elementor-location-header|footer"`.
- **Staging URLs survive migration** — grep the fetched HTML for the old host (`*.sg-host.com`).

## Verifying when curl is blocked

```python
js("fetch('/the-page/',{credentials:'same-origin'}).then(r=>r.text()).then(t=>({n:(t.match(/TEXT/g)||[]).length}))")
```

Counting in JS like this is the correct habit — **`grep -c` counts matching *lines*, and an Elementor
page is one enormous minified line**, so it answers 1 for a pattern occurring ninety times and reads as
"the content is not there". On curl output use `grep -o '<pattern>' file | wc -l`.

**Cache-bust before concluding anything is missing.** A dynamic-cache hit can serve a stale or partial
copy — one URL came back 49 KB where the live page is 71 KB, which looks exactly like the page having
lost its sections. Re-fetch with a unique query string (`?nocache=$(date +%s)`) or purge the cache, and
confirm from the rendered DOM in the logged-in browser, before reporting content as gone.

Nav-label regex `menu-item-\d+"><a href="[^"]*">([^<]*)` **skips the current page's own item**
(extra classes change the markup) — a "missing" current item in the scraped list is an artefact.

## Browser harness recovery

- `Runtime.evaluate timed out` / IPC `TimeoutError` = wedged daemon, not a broken page:
  `pkill -f browser_harness.daemon`, then retry — the harness respawns.
- Chrome's **"Allow remote debugging?"** modal is the user's click, never yours; alternatively they
  grant Accessibility to the launching app so `browser-harness mac-approve` can accept it.
