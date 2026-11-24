# Handing a produced document to Woody

Read this before the final message of any session that produces a file — QA report,
SEO audit, GBP audit, monthly report, invoice, developer message. The failure mode is
**silent**: the document exists, the chat shows nothing usable, and the session ends
with the user saying they cannot open or download it.

**How the document should read is a separate concern:** see
`references/document-style-and-tone.md` for the internal-document voice (informal, first names, team
framing), the pagination rules that stop a six-section summary running to seven half-empty pages, and the
footer/date check that catches a renderer inherited from an earlier job.

## Producing the file: one content source, two renders

When a document has to exist as both an editable `.docx` and a `.pdf`, build both from **one content
list** rather than maintaining two copies — they drift, and the PDF ends up contradicting the Word file
the user just edited. Keep volatile values (prices, dates, client name) in a single dict at the top of
the generator so a change is one edit and one re-run.

- **`textutil -convert html` is not a PDF route.** It drops embedded images and table shading, so the
  logo and the brand colour silently vanish and the result looks unbranded. It also emits Times with
  per-paragraph inline styles. Build the branded HTML yourself instead.
- **Chrome headless prints it**:

  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
    --no-pdf-header-footer --print-to-pdf=/abs/out.pdf file:///abs/in.html
  ```

  There is no LibreOffice and no pandoc on this machine, so this is the printing route rather than a
  fallback.
- **Chrome can write the PDF and then fail to exit** inside a subprocess timeout. Judge success on the
  file — present and non-trivial in size — not on the exit code, and do not delete and re-run on a
  timeout that produced a good PDF.
- **Verify a reissue rather than eyeballing it.** Extract text from both renders and assert what must be
  gone and what must remain (`'Signature' not in text`, `'£900' in text`), check the table and image
  counts where a block was removed, then render the affected pages to PNG at ~100 dpi and look at them.
  A removed table leaves no trace in a text diff but can leave a visible gap.
- **Date the document from `date`.** Do not infer "today" from timestamps inside a pasted thread: a
  thread that is days old, or a session resumed later, puts a visibly wrong date on a client document.
- **A re-date renames the whole set, not just the cover.** The date lives in four places: the source front
  matter, the generator's cover config, the footer note (a separate constant from the cover, and the one
  that gets missed), and the **output filename**, which is what the recipient sees in their mail client
  before they open anything. Change all four, rebuild, then move the superseded `.md`/`.html`/`.pdf`/`.docx`
  into `<project>/reports/archive/<old-date>/` and delete them from
  `~/.hermes/profiles/dsc/cache/documents/`, so a saved link or an earlier message's card cannot deliver the
  old one. Probe the rebuilt artefacts for the new date's presence **and** the old date's absence in both
  formats. The printed date is his decision about when the document issues, not a claim that the findings
  were verified that day: do not "correct" it back to the date of the pass, and record the actual
  re-verification date separately in the project notes.
- **When the generator writes into the delivery cache, sync cache → project folder.** Copying the other
  way silently restores the previous version — sizes look plausible and the edits appear to have
  vanished. After every reissue, confirm the two copies match.

## The directive

Files reach the chat on a `MEDIA:` line:

```
MEDIA:/absolute/path/to/file.pdf
```

Two properties, both enforced, both silent when broken:

- **Bare, unformatted, alone on its line.** The standalone-line matcher expects
  whitespace, then at most one quote or backtick, then `MEDIA:`. Markdown around the
  tag — `**MEDIA:/path**`, backticks, a `-` bullet, a table cell — stops it being
  read as a standalone media line and the file drops out of the deliverable list.
  Emit it at column 0, nothing else on the line, a blank line either side.
- **Inside an allowed delivery root.** A file outside the gateway's media-delivery
  roots does not attach. The profile cache directories are the allowed roots and are
  the only reliable staging point:

  ```
  ~/.hermes/profiles/dsc/cache/documents/     # reports, messages, PDFs, .docx
  ~/.hermes/profiles/dsc/cache/{images,audio,videos,screenshots}/
  ```

  This is narrower than "anywhere in the home folder". `~/Documents/...` is not
  guaranteed, so a report written straight to the project folder and attached from
  there is the likeliest cause of a card that will not preview or download. Neither
  is an arbitrary home-root folder: a `~/<project>/` convenience copy created for
  Finder access is **outside every root** and will not attach either. Verify rather
  than assume — `scripts/check_media_delivery_path.py`.

  The allow list is built at check time from the profile cache dirs of *every*
  profile plus a `trust recent files` recency window, so it survives multiplexing and
  profile switching; the root-restriction is the deliberate part, not an accident of
  this machine.

## Procedure

1. Do the work and keep working copies where the project lives
   (`~/Documents/<project>/<client>/`): source markdown, generator script, raw evidence.
2. **Copy — do not move** — the finished deliverables into the profile cache
   directory. The project folder stays the single source of truth.
3. Emit one bare `MEDIA:` line per file, each on its own line.
4. Say what each file is and which one to act on (the one to send / the editable copy
   / the message to forward). A row of unexplained attachments is not a handover.
5. If the user reports a file will not open, **do not re-send the same thing.** Offer
   the two routes that bypass the chat entirely: paste the content inline in the
   reply, and open the file natively on the Mac (`open <path>` — launches Preview for
   a PDF, Word for a .docx).

## Prove the path is deliverable before you claim it is

Do not reason about the roots from memory — ask the gateway's own resolver. Run this
with the **repo's `venv/bin/python`**, which is the interpreter that can import the
gateway package (the bare system `python3` cannot):

```bash
cd ~/.hermes/hermes-agent && ./venv/bin/python \
  ~/.hermes/profiles/dsc/skills/dsc/dsc-website-qa/scripts/check_media_delivery_path.py \
  /path/to/report.pdf
```

It prints the allow list, the recency window, and `ALLOWED` / `NOT ALLOWED` per path
— exit 1 if any path is refused, so it works as a gate in the handover step. Use it
whenever a handover has failed once, and before repeating a claim that a file
**should** attach.

## Diagnose from source, not from guesswork

These are properties of the delivery code, so re-read them when a handover fails
rather than theorising. A bad path, a formatting choice and a root restriction all
produce the identical symptom.

- Desktop parser and its regexes: `apps/desktop/src/app/artifacts/`
- Gateway allowed-roots policy: `hermes_cli/web_server_files.py`
  (`_managed_files_policy`, `_resolve_managed_path`, `_path_is_under`)
- Electron read path, size cap and sensitive-path denylist:
  `apps/desktop/electron/hardening.ts` (`readFileDataUrlForIpc`,
  `sensitiveFileBlockReason`)

Two things that are *not* the cause, so don't spend a pass on them: the managed-file
routes allow any absolute path under the user's home (no locked root on a desktop
install), and the size caps sit far above a normal report (100 MB for the download
route, 16 MiB for the in-app data-URL preview).

**Check the desktop's connection mode before blaming the path.** Two small state files
settle it without any guesswork:

```bash
python3 -c "import json;print(json.load(open('$HOME/Library/Application Support/Hermes/connections.json')))"
python3 -c "import json;print(json.load(open('$HOME/Library/Application Support/Hermes/backend-ownership.json')))"
```

`connections.json` gives `mode`/`primary` (`local` vs `remote`); `backend-ownership.json`
lists which `hermes --profile <p> serve` process owns which profile and on what port, so
you can tell which backend the app is actually talking to. In **remote** mode the file
lives on the *gateway* machine, not this one, so a locally-staged report cannot preview
or download no matter which allowed root it sits in — and re-staging will never fix it.
Only in `local` mode is the path root the deciding gate.

## Confirming the native-open fallback landed

`open` exiting 0 only means the launch request was accepted, so it is not proof the user
saw anything. This is the one fallback whose success you *can* verify, and it is worth
doing before telling someone their file is on screen:

```bash
open -a Preview "/abs/path/report.pdf" && sleep 3
lsappinfo list | grep -i -A2 preview     # expect the app, its pid, and "(in front)"
osascript -e 'tell application "System Events" to get name of every process whose name contains "Preview"'
```

`open -R <path>` instead opens Finder with the file **selected** — the right call when the
ask is "where is it" rather than "show me it", and the one that survives being on the
other Mac less badly, since the folder path is at least something they can type.

If the question behind the handover is "where is finding X in this report?", do not
supply a page number you have not checked — page-map the finished PDF first:
`dsc-seo-audit` → `references/render-and-artefact-verification.md` §3, "Locating a finding
by page". A finding normally sits on three pages (severity table, write-up, priority
list), so give all of them; one page number sends the user hunting.

## When the user asks for the file as a download

*"download as a pdf"* means **put a copy where they can find it in Finder**, not just re-attach
the card. Copy — never move — the already-verified PDF into `~/Downloads` under a clear,
dated, human filename, confirm the copy is byte-identical to the source, and say where it is:

```bash
cp report.pdf ~/Downloads/DSC-<Report-Name>-<D><Mon><YYYY>.pdf
shasum -a 256 report.pdf ~/Downloads/DSC-<Report-Name>-<D><Mon><YYYY>.pdf   # must match
```

A matching hash is the point: it proves the download is the verified artifact rather than a
re-render that could have drifted. Still emit the `MEDIA:` line per the directive above — and note
that a copy made *now* attaches because of the recency window, not because `~/Downloads` is a
delivery root; a file that sits there for weeks will not. Keep working from the project-folder
original (`~/Documents/<project>/<client>/`) when a revision is requested, so the Downloads copy can
never become the de-facto source.

## Emailing the finished document to a third party

"Send this now" is an instruction to send, not to re-draft. The route that works from this profile:

1. **Build the message as MIME in Python, never by hand.** `email.message.EmailMessage`,
   `set_content(body, subtype="plain", charset="utf-8")`, then `add_attachment(data,
   maintype="application", subtype="pdf", filename=<basename>)`. Write the `.eml` to the scratch dir and
   read the headers back with `message_from_binary_file` before sending. UTF-8 plain text carries em dashes
   and `Citroën` correctly, so send the approved wording **verbatim** — do not flatten its punctuation into
   hyphens at the send step, which silently changes a document he already approved.
2. **Send with himalaya from the profile's own config**, which is narrowed to the DSC client mailbox:

   ```bash
   himalaya -c ~/.hermes/profiles/dsc/himalaya/config.toml -a <mail-account> message send --save sent < msg.eml
   ```

   v2.1 syntax: the mailbox flag is `-m "<mailbox>"` and there is no `--folder` and no `--no-headers`.
3. **The `From` can be `paul@sales-consultants.com`** — a working send-as alias on the Gmail account, and
   Gmail keeps it rather than rewriting it to the Gmail address. Set `Reply-To` to the same. Genuinely
   originating from the DSC mailbox means the `[accounts.dsc]` entry in `~/.config/himalaya/config.toml`,
   whose password comes from the `<mail-account>` Keychain item; add that item rather than changing the From
   to something the client does not recognise.
4. **`--save sent` leaves two copies** in Gmail, because Gmail auto-saves SMTP mail and `--save` appends
   another. That is one delivery, not two — do not report a double send. Drop `--save` when a single copy
   matters.
5. **Verify by reading the message back, then check for a bounce.** List `[Gmail]/Sent Mail`, read the new
   id, and confirm the `From` survived, the `To` is the intended recipient and the attachment is the
   expected name and byte count; then list the inbox after ~45 s looking for a Mail Delivery Subsystem /
   "Undelivered Mail" entry. `Message successfully saved and sent` is the client's own claim, not evidence.
6. **Check the approved draft's factual claims before it ships.** An opening sentence asserting the client
   already has the review, or that someone has been copied, is checkable from Sent Mail — if the record
   does not support it, say so in the reply instead of letting the claim go out unexamined.
7. **Report the evidence, not the intention**: recipient, time, From as delivered, attachment name and
   bytes, bounce check. Then record the send in the project `NOTES.md` and the digest, since "drafted" and
   "sent" are the two states that get confused three sessions later.

## Pitfalls

- **A card already sent keeps its old path forever.** Attachments are resolved from
the message text as it was written; re-staging a file and emitting a corrected
`MEDIA:` line does **not** repair earlier cards in the transcript. When a handover
failed, say so explicitly and tell the user to use **only the newest message's
cards** — otherwise they retry a card that cannot ever work and conclude the fix
failed. Do not quietly re-send and hope.
- **The native-open fallback only reaches the machine Hermes runs on.** Woody works
  across two Macs, so `open <path>` on the host is invisible if he is on the other
  one. Confirm which machine he is on before relying on it, and pair it with the two
  routes that always work regardless: paste the section inline, or offer to email the
  file (it is usually going to a third party anyway).
- **Do not claim a delivery worked.** A tool call that emits the directive proves
  nothing; only the user opening the file does. When a delivery has failed once,
  state which mechanism you changed and why before asking them to try again.
- **Never describe an artefact you did not build and list in this session.** A render
  that was only planned reads exactly like a real one in prose — page count, design
  choices, file names — until the user tries to open it and reports that nothing
  works. If the files are missing, say so in one line and build them; do not re-describe
  them, and never let a generator's "wrote …" log stand in for `ls -l` of the output.
- **Do not stage only in the project folder and assume the card will work** — that is
  the default habit and it is the one that breaks.
- **A staged copy does not stay staged.** The profile cache is swept, so a card emitted for a file staged
  days earlier fails both preview *and* download while the project copy is untouched — which reads exactly
  like a render fault. `ls` the staged path before re-emitting any `MEDIA:` line, re-copy from
  `~/Documents/<project>/<client>/` if it is gone, and name the swept cache as the cause rather than rebuilding
  the document.
- **Run the diagnostic sweep once, then change channel.** The complete list is: the
delivery root, the `MEDIA:` formatting, the desktop connection mode, the size caps, and
whether the staged copy is actually current (hash it against the source — a convenience
copy refreshed before later edits is stale and looks identical in Finder). If all five
check out and the card still fails, the fault is in the app rather than in your staging,
and a fourth attach is a fourth failure. State what you ruled out as a short list, then
move to a route that bypasses chat. Continuing to poke at the same mechanism spends the
user's time to prove nothing.
- **An extension the chat cannot render still delivers.** `.md`, `.html`, `.pdf`,
  `.docx` are all fine; for a long report an `.html` copy is usually the most
  readable in-app option because it renders styled instead of downloading.
