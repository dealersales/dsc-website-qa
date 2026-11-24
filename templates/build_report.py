#!/usr/bin/env python3
"""Markdown findings -> branded HTML -> PDF (Chrome) + DOCX (python-docx).

Copy into the client's QA folder as build_report.py and edit the CONFIG block.
Deliberately dumb: one source of truth for content, two renderers, so the PDF and
the DOCX cannot disagree.

    python3 build_report.py            # writes <OUT_STEM>.pdf and .docx

Requires: pip install markdown python-docx pypdf
"""
import re
import subprocess
import sys
from pathlib import Path

try:
    import markdown
    from docx import Document
    from docx.shared import Pt
    from pypdf import PdfReader
except ImportError as exc:  # fail early with the install line, not a traceback
    sys.exit(f"missing dependency: {exc}. pip install markdown python-docx pypdf")

# ---- CONFIG -----------------------------------------------------------------
SRC = Path("QA-FINDINGS.md")          # the findings markdown
OUT_STEM = "Client-QA-audit"
TITLE = "Website QA"
BRAND = "#1D1D1B"                    # DSC dark tile
ACCENT = "#FF8300"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# ----------------------------------------------------------------------------

CSS = f"""
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #222; font-size: 10.5pt; line-height: 1.45; }}
h1 {{ color: {BRAND}; border-bottom: 3px solid {ACCENT}; padding-bottom: 6px; }}
h2 {{ color: {BRAND}; margin-top: 22px; page-break-after: avoid; }}
h3 {{ color: {ACCENT}; margin-top: 16px; page-break-after: avoid; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }}
th {{ background: {BRAND}; color: #fff; text-align: left; padding: 5px 7px; }}
td {{ border-bottom: 1px solid #ddd; padding: 5px 7px; vertical-align: top; }}
tr {{ page-break-inside: avoid; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 12px; color: #555; }}
code {{ background: #f4f4f4; padding: 1px 4px; }}
"""


def to_html(md_text: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "attr_list"])
    return (f"<!doctype html><meta charset='utf-8'><title>{TITLE}</title>"
            f"<style>{CSS}</style><body>{body}</body>")


def build_pdf(html: str, out: Path) -> None:
    html_file = out.with_suffix(".html")
    html_file.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", html_file.resolve().as_uri()], check=True)


def build_docx(md_text: str, out: Path) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    for block in md_text.split("\n"):
        line = block.rstrip()
        if not line.strip():
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.lstrip().startswith(("- ", "* ")):
            doc.add_paragraph(line.lstrip()[2:].strip(), style="List Bullet")
        elif re.match(r"^\|?(\s*)-{3,}", line):
            continue                      # table rules: handled loosely, see note below
        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line.strip())
            doc.add_paragraph(clean)
    doc.save(out)


if __name__ == "__main__":
    if not SRC.exists():
        sys.exit(f"no source at {SRC.resolve()}")
    md_text = SRC.read_text(encoding="utf-8")
    pdf, docx_out = Path(OUT_STEM + ".pdf"), Path(OUT_STEM + ".docx")
    build_pdf(to_html(md_text), pdf)
    build_docx(md_text, docx_out)

    # Verify the artefacts before claiming them - see
    # references/render-and-artefact-verification.md
    pages = len(PdfReader(str(pdf)).pages)
    print(f"PDF {pdf} {pdf.stat().st_size} bytes, {pages} pages")
    print(f"DOCX {docx_out} {docx_out.stat().st_size} bytes, "
          f"{len(Document(str(docx_out)).paragraphs)} paragraphs")
