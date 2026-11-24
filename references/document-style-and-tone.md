# Document style and tone

How a DSC document should **read** and **paginate**, as distinct from how it is delivered
(`references/deliverable-handover.md`) or how it is rendered.

## Internal documents: informal, first names, team voice

Anything going to colleagues or partners — the platform owner, the coordinator, the build developer, an internal summary — is
written as one team talking to itself, not as a supplier reporting to a client.

- **First names only.** No surnames, no job titles, no "Prepared for: Name (Company)". A cover meta
  line reads `For: the platform owner and the coordinator`, not `Prepared for: the platform owner (the platform Systems) and the client coordinator
  (Digital Sales Consultants)`.
- **First person for your own actions.** "I changed", "I rolled one back", "files I touched". Passive
  or third-person phrasing ("the fixes were applied") reads like a contractor's invoice.
- **Conversational headings.** A column headed "Owner" becomes "Who's on it", and the cell carries a
  **person's name** ("Paul", "the coordinator", "the platform owner") rather than a team label ("DSC", "Client / lender").
- **Drop blame framing without changing facts.** "The fix list from the pre-launch review hadn't made
  it onto the build" is as accurate as "almost none of the pre-launch fixes had been applied" and
  reads as a shared problem rather than an accusation. Soften the framing, never the finding.
- **Own your own slip in the document.** "Caught it, wrapped the block" reads as more trustworthy than
  a spotless account where nothing ever went wrong — and it tells the reader the verification was real.
- **Say which file to send and which is reference.** A row of unexplained attachments is not a handover.

**Client-facing is different and stays plain.** Where the dealer is the reader: no `curl` output, no tag
or header names in the body, every item owner-labelled, and a closing "what we need from you" list. Keep
compliance findings at full severity and do not demote them to suit the audience.

## Density: a section break is not a page break

A six-section summary that forces `page-break-before: always` on every `#` heading becomes seven pages
averaging half-empty. The reader asked for a summary, not a booklet.

- Let sections flow with a margin rule instead of a break.
- Let the cover run straight into section 1 unless the cover is genuinely a title page.
- **Let long tables break between rows** so a table fills the page it starts on:

  ```css
  table { page-break-inside: auto; }
  tr    { page-break-inside: avoid; }
  thead { display: table-header-group; }   /* header repeats on the next page */
  ```

  `page-break-inside: avoid` on the table itself is what creates the large gaps — the whole table jumps
  to a fresh page and leaves the previous one 45% full.
- Tighten the generic spacing while you are there: section headings, paragraph bottom margins, list and
  table margins all carry a millimetre or two that adds up over six sections.

**Measure the result rather than eyeballing it.** Rasterise every page and read how far down the content
ends; a page under roughly 70% full that is not the last page still has something forcing a break.

```python
import fitz
doc = fitz.open(pdf)
for i, p in enumerate(doc):
    blocks = p.get_text("blocks")
    maxy = max((b[3] for b in blocks), default=0)
    print(i + 1, f"{100 * maxy / p.rect.height:.0f}% full")
    p.get_pixmap(dpi=100).save(f"/tmp/page-{i+1}.png")
```

`pymupdf` (imported as `fitz`) is the reliable rasteriser here; `qlmanage -t` only gives page 1, and
`pdftoppm`/`gs` are not installed.

## Provenance: re-read the footer on every build

The renderer's `FOOT_NOTE` carries the document's own date and subject, and copying a renderer from an
earlier job silently inherits that job's line — a post-launch summary went out footed "Report prepared:
<earlier date> | Pre-launch readiness review" while the cover config looked correct. The same applies to
`TITLE`/`SUB` and any "Audited:" meta. Read the **rendered** footer in both PDF and DOCX, not just the
config block.

## Verify both renders before sending

Extract text with each format's own parser (`pypdf` for the PDF, `python-docx` for the `.docx`, walking
`doc.tables` as well as `doc.paragraphs` — table text is invisible to a paragraphs-only read), then assert
what must be present and what must be gone: the new date present, the old date absent, no literal `**`,
no stray `&mdash;` in the Word file, and every section heading accounted for.
