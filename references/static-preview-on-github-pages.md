# Publishing a static preview of a PHP build, for review

A client or colleague wants a link that shows progress before the build is live. GitHub Pages is the
cheap host; it cannot run PHP, so the artefact is a **crawl of the running build** with its URLs
rewritten. (`dsc-demo-site-hosting` covers the same pipeline for *demos* and carries the account rules —
this file is the QA-preview variant and the rewrite traps.)

## What to publish

- the site itself, every page type, from the local Apache instance;
- a **progress page** at `/progress/` — one row per finding: ref, owner, state, what proved it — so one
  link answers "where are we" as well as "what does it look like";
- a **banner** on every page saying what the static host cannot do: forms, the finance widget, live stock.
  Without it, a blank finance panel and a form that does nothing read as defects in the build rather than
  as artefacts of the host.
- `noindex` on every page, a disallow-all `robots.txt`, and `.nojekyll`.

## URL rewriting — three passes, not one

Map pages to clean directories (`/stock.php` → `stock/index.html`, `/vehicle/<slug>` →
`vehicle/<slug>/index.html`) and prefix everything with the project path (`/<repo>/`), because a project
Pages site is not served from the domain root.

1. **Attributes** — `href`, `src`, `action`, `poster`, and each candidate inside `srcset`.
2. **Inline CSS** — `style="background-image:url('/assets/hero0.jpg')"` has no `src` to rewrite. Prefix
   `url('/…` and `url("/…` or the homepage hero renders as a black band.
3. **JSON in a data attribute** — hero frames arrive as
   `data-hero-slides='["/assets/hero0.jpg", …]'` and are applied by the site's own JS at runtime. Prefix
   the `"/assets/` occurrences inside the attribute. If any pass can run twice, collapse a doubled prefix
   (`/repo/repo/`) at the end rather than depending on the order.

Then **offset the site's fixed header** by the banner's height — `body{padding-top:<h>}` plus
`header#header.fixed-top{top:<h>}` — or the injected banner disappears under the nav on every page.

## Verify on the published site, not locally

First build is 30–90 s and the first request often 404s; poll until 200. Then request a page, a VDP,
`/progress/`, the CSS, one vendored asset and `assets/logo.png`, and **screenshot the published URL** —
a local screenshot cannot show that Pages served an unstyled page or a black hero. Re-check with a
cache-buster (`?v=2`) after a rebuild; Pages serves the previous build for a minute or two.

## Pitfalls

- **A builder that wipes its output directory deletes `.git`.** The repo lives in that directory once it is
  published. Remove the children except `.git` (and `README.md`), or clone the repo fresh before each run.
- **`gh repo create … --source=. --push` can create the repo and fail the push**, leaving an empty public
  repo. Push again over SSH with the DSC key rather than creating a second repo:
  `GIT_SSH_COMMAND="ssh -i ~/.ssh/dsc_github -o IdentitiesOnly=yes" git push -u origin main`.
- **HTTPS pushes of a few MB fail with `RPC failed; HTTP 400` / `send-pack: unexpected disconnect`.** Raise
  `http.postBuffer`, and if that does not settle it, SSH is the reliable route.
- **A public repo is a public site.** No credentials, no customer data, and nothing the dealer has not
  published. `noindex` plus a disallow-all `robots.txt` keeps it out of the index while it is reviewed.
- **Say what it is not.** The preview cannot submit an enquiry, cannot price finance, and its stock is a
  snapshot. A reader who is told that in one sentence stops reading the gaps as build defects.
