# Delivering the QA report — building and handing over the file

Split verbatim out of `dsc-website-qa` SKILL.md §5 so the delivery rules stay readable. Each paragraph is the original text in full.

**Stamp the cover date from `date` when you build, not from the session's opening context.** A session
that spans midnight, or resumes the next morning, will otherwise publish yesterday's date on a document
whose findings were re-verified today — and the cost is a full rebuild of the `.md`, the PDF, the `.docx`
and the staged copies, plus deleting the superseded version everywhere it exists. Run `date` in the same
command that renders the report and reconcile it against the `Audited:` line.

**Verify the built `.docx` and `.pdf` with their own parsers before sending** — a
byte-level grep of either one finds nothing and reads as "content missing", and `.docx`
text sitting in table cells is missed by a paragraphs-only read. Recipes:
`dsc-seo-audit` → `references/render-and-artefact-verification.md` §3.

**Don't hand-roll the renderer.** The DSC house style (cover block, navy/slate CSS,
severity-tagged headings, markdown → HTML → Chrome PDF plus a `.docx` sibling) already
exists as a working script: copy `dsc-seo-audit` → `templates/build_report.py` and change
the CONFIG block at the top. Both the the template build and a dealer reports were produced from it. **The cover block already carries the title, so the source markdown must not repeat it as an `# H1` immediately after the `---`** — the renderer prints the cover and then the body heading, and the document opens with the same title twice. Start the body at `## Summary`.

**Handing the files over: read `references/deliverable-handover.md` first, and `references/document-style-and-tone.md` for voice and pagination.** Copy the
finished report and the developer message into the profile cache directory and attach
each on a bare `MEDIA:` line of its own. A document left in `~/Documents` and attached
with a formatted `MEDIA:` line produces a card the user cannot open — and the failure is silent, so it surfaces only when they tell you.

**Prove the staging path is deliverable rather than assuming it** — the allowed roots
are narrower than "anywhere in the home folder", so a convenience copy made at the home
root will not attach:

```bash
cd ~/.hermes/hermes-agent && ./venv/bin/python \
  ~/.hermes/profiles/dsc/skills/dsc/dsc-website-qa/scripts/check_media_delivery_path.py \
  /path/to/report.pdf
```

Exit 1 means at least one path is outside every root. When a handover has already
failed, note that **cards in earlier messages keep their original path and can never be
repaired** — point the user at the newest message only, and offer the two routes that
bypass chat entirely (paste the section inline, or open the file natively on the host).

**Internal documents are informal: first names only, team voice (we/us), no "Prepared for:" and no "Owner" column — and own your own slips in the narrative rather than writing a document where nothing went wrong.** Shape and wording: `references/internal-comms-and-doc-tone.md`. Fixes applied to a live site get a re-runnable harness — `references/live-site-fix-verification.md`.
