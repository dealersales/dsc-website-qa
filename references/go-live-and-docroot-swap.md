# Taking a rebuilt dealer site live

The phase between "the QA fixes are in" and "the dealer's domain serves it". Applies to a
the template build/the platform-derived PHP build; the estate-specific access details live in the
`platform-estate-deploy` skill.

## Start from the blank template, never from another dealer's build

`customer-websites/_template` in the dealer-websites repo is the working build with every trace of
the previous dealer removed: placeholders for name/town/phone/address/FRN/socials/analytics, both
CodeWeavers keys blanked, reviews emptied, neutral images.

```bash
cd customer-websites/_template && ./new-dealer.sh
```

It asks for the dealer's details, copies itself to `customer-websites/<domain>`, fills the
placeholders, writes `config.php` with `IS_STAGING` on, and runs `check-setup.sh` — which exits
non-zero while any placeholder, another dealer's name, a placeholder key or an unattributed review
remains. `SETUP.md` in the same folder lists the traps.

**Copying a finished dealer is the same job with a different donor and no guard rail.** Every
previous-dealer defect on this estate came from a copy: another dealer's finance key, invented
testimonials badged "verified", stock photographs of cars the dealer does not sell, and a hero of a
forecourt holding hundreds of cars at a family dealership. A template plus a check that fails on
leftovers is what makes "it's done" mean something.

Still manual after the script: the local copy, hero/logo/favicons, the redirect map from the
outgoing site's sitemap, and the reviews.

## Staging

1. Stage at `~/domains/<domain>/<newsite>/` — **beside** `public_html`, never inside it. A subfolder
   inside the web root cannot be a preview: the build's asset paths are absolute (`/assets/…`,
   `/vehicle/…`) and resolve against the old site's files, so the preview looks broken for a reason
   that is not real.
2. Build `config.php` there from the old docroot's values — it is excluded from every repo and no
   sync recreates it. A missing `config.php` on a staging copy looks exactly like a broken build.
3. Prove it runs on that server, not just locally: `php -l` every file with the server's own binary,
   then render a page through PHP CLI with a faked `$_SERVER` and assert on the output (byte count, a
   known string, no `Fatal error`). Different PHP version, different extensions, different result.

## The swap

```bash
cd ~/domains/<domain>
sed -i "s/define('IS_STAGING', true);/define('IS_STAGING', false);/" <newsite>/config.php
mv public_html public_html_old_$(date +%Y%m%d)
mv <newsite> public_html
```

Rollback is the reverse pair — seconds, not a re-upload.

**`IS_STAGING` is the trap that eats a launch.** The flag emits `noindex, nofollow` on every page and
the rename does not clear it, so a promoted build goes live invisible and fully ignored, silently, for
weeks. Flip it **in the same command as the rename**, never "after we've checked a few pages".

Conversely, leaving it true is the best held-launch available: the real domain, no DNS change, no
subdomain, testable down to the domain-bound third-party embeds. A subdomain preview needs both a
DNS record at the domain's DNS provider *and* an hPanel subdomain, and will still fail those embeds
because the keys are tied to the live hostname.

## Verify by newness, not by status

After the swap, assert the **new** markup is served — a string only the new build has — because both
docroots answer 200. Then walk the page types: home, stock, one VDP (does the finance widget render
and quote?), reviews, contact, finance; plus `/sitemap.xml`, `/robots.txt`, `/llms.txt`, a legacy URL
that should 301, and non-www → www → https. Two hops in a redirect chain is worth noting but not a
defect; a 404 on an indexed URL is.

## Establish the access route before reporting a blocker

"I can't deploy" is almost always wrong, and saying it costs trust that the delay does not. Check
before claiming a wall:

- `gh auth status` — several accounts may be logged in and **the active one may not own the repo**;
  switch, push, switch back.
- `ls ~/.ssh` and try the estate's SSH port, not just 22.
- On a large push: `unexpected disconnect` is the payload, not auth — set
  `git config http.postBuffer 524288000` and `http.version HTTP/1.1`.
- `Repository not found` on a repo that exists means the wrong account's credentials are in play.

Quote the verbatim error when something genuinely is blocked; a paraphrase gets argued with.
