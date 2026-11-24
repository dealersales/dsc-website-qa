#!/usr/bin/env python3
"""Extract a finished DSC website-QA report into a findings table.

Why this exists: walking a client through an audit from a chat summary drops items and
mis-states severities. Parsing the .docx the client is actually holding guarantees all N
findings appear, in their real severity, ready for a call pack, a spreadsheet or an owner
column.

The house QA layout this expects:

    Heading 2  ->  "12. Vehicle structured data is too thin to earn rich results"
    Normal     ->  "Medium  -  All vehicle detail pages"        (severity, then location)
    Normal     ->  "Expected: ..."
    Normal     ->  "Actual: ..."
    Normal     ->  "Evidence: ..."
    Normal     ->  "Recommendation: ..."

Usage:
    python3 findings-to-table.py report.docx              # TSV to stdout + counts
    python3 findings-to-table.py report.docx --json out.json --tsv out.tsv

The `owner` column is emitted blank on purpose: fill it per client (their decision / us /
the incumbent supplier) before the table goes into a call pack.
"""
import argparse
import json
import re
import sys

from docx import Document

SEVERITY_RE = re.compile(r"^(Critical|High|Medium|Low|Info)\s*[·\u00b7\-–]\s*(.*)$")
FIELD_RE = re.compile(r"^(Expected|Actual|Evidence|Recommendation):\s*(.*)$")
NUMBER_RE = re.compile(r"^(\d+)\.\s*(.*)$")


def parse(path):
    doc = Document(path)
    findings = []
    cur = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style.name == "Heading 2":
            m = NUMBER_RE.match(text)
            num, title = m.groups() if m else (None, text)
            cur = {
                "n": int(num) if num else len(findings) + 1,
                "title": title.strip(),
                "severity": "",
                "where": "",
                "expected": "",
                "actual": "",
                "evidence": "",
                "recommendation": "",
                "owner": "",
            }
            findings.append(cur)
            continue
        if cur is None:
            continue
        m = SEVERITY_RE.match(text)
        if m and not cur["severity"]:
            cur["severity"] = m.group(1)
            cur["where"] = m.group(2).strip()
            continue
        m = FIELD_RE.match(text)
        if m:
            cur[m.group(1).lower()] = m.group(2).strip()
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--json")
    ap.add_argument("--tsv")
    args = ap.parse_args()

    findings = parse(args.docx)
    if not findings:
        sys.exit("No Heading 2 findings found - is this the house QA layout?")

    # Integrity: numbering should be a clean run, or the report itself is broken.
    nums = [f["n"] for f in findings]
    gaps = [n for n in range(1, max(nums) + 1) if n not in nums]
    dupes = sorted({n for n in nums if nums.count(n) > 1})

    cols = ["n", "severity", "title", "where", "owner", "actual", "recommendation"]
    rows = ["\t".join(cols)]
    for f in findings:
        cells = [str(f[c]).replace("\t", " ").replace("\n", " ") for c in cols]
        rows.append("\t".join(cells))
    tsv = "\n".join(rows)

    if args.tsv:
        open(args.tsv, "w", encoding="utf-8").write(tsv)
    if args.json:
        json.dump(findings, open(args.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if not args.tsv and not args.json:
        print(tsv)

    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    print(f"\n{len(findings)} findings: {summary}", file=sys.stderr)
    if gaps or dupes:
        print(f"WARNING - numbering gaps {gaps}, duplicate numbers {dupes}", file=sys.stderr)


if __name__ == "__main__":
    main()
