#!/usr/bin/env python3
"""Is a file actually deliverable to the chat? Ask the gateway's own resolver.

Reports, audits and developer messages only attach if they sit inside the gateway's
media-delivery allowed roots. The failure is SILENT: the file exists, the card may
even render, and it will not preview or download. Run this instead of reasoning
about the roots from memory.

Usage (MUST use the repo venv python -- it is the one that can import the gateway
package; the bare system python3 cannot):

    cd ~/.hermes/hermes-agent && ./venv/bin/python \
      ~/.hermes/profiles/dsc/skills/dsc/dsc-website-qa/scripts/check_media_delivery_path.py \
      ~/.hermes/profiles/dsc/cache/documents/report.pdf

With no arguments it reports on the profile cache directories themselves, which is
the useful baseline when staging a fresh handover.

Exit codes: 0 = every path allowed, 1 = at least one refused, 2 = could not import
the gateway package (wrong interpreter).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_repo() -> bool:
    """Put the hermes-agent checkout on sys.path. Returns False if not found."""
    candidates = [
        Path(os.environ.get("HERMES_HOME", "")).expanduser().parent / "hermes-agent",
        Path.home() / ".hermes" / "hermes-agent",
        Path(__file__).resolve().parents[4] / "hermes-agent",
    ]
    for candidate in candidates:
        if (candidate / "gateway" / "platforms" / "base.py").is_file():
            sys.path.insert(0, str(candidate))
            return True
    return False


def main(argv: list[str]) -> int:
    if not _load_repo():
        print("Could not locate the hermes-agent checkout to import the gateway policy.")
        return 2

    try:
        from gateway.platforms.base import (  # noqa: PLC0415
            _media_delivery_allowed_roots,
            _media_delivery_denied_paths,
            _media_delivery_recency_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Could not import the gateway media policy: {exc}")
        print("Re-run with the repo venv python: cd ~/.hermes/hermes-agent && ./venv/bin/python ...")
        return 2

    roots = [Path(p).resolve() for p in _media_delivery_allowed_roots()]
    denied = [Path(p).resolve() for p in _media_delivery_denied_paths()]
    home = Path.home().resolve()

    print(f"HERMES_HOME      : {os.environ.get('HERMES_HOME', '(unset)')}")
    print(f"allow roots      : {len(roots)}")
    print(f"recency window   : {_media_delivery_recency_seconds():.0f}s "
          "(a file written inside this window is trusted regardless of root)")

    targets = [Path(a).expanduser() for a in argv[1:]] or [
        Path(os.environ.get("HERMES_HOME", str(home / ".hermes"))).expanduser()
        / "cache" / sub
        for sub in ("documents", "images", "audio", "videos", "screenshots")
    ]

    refused = 0
    for target in targets:
        resolved = target.resolve()
        match = next((r for r in roots if resolved == r or r in resolved.parents), None)
        # A deny-listed path wins, except the running user's own home itself.
        blocked = next(
            (d for d in denied
             if d != home and (resolved == d or d in resolved.parents)),
            None,
        )
        if match and not blocked:
            verdict = "ALLOWED    "
        else:
            verdict = "NOT ALLOWED"
            refused += 1
        note = f"root={match}" if match else "no matching allow root"
        if blocked:
            note += f"  DENIED by {blocked}"
        print(f"{verdict}  {resolved}\n              {note}")

    print()
    if refused:
        print(f"{refused} path(s) will NOT attach. Copy them into one of the roots above")
        print("and emit a bare `MEDIA:/abs/path` line, alone on its own line.")
        return 1
    print("All paths are inside an allowed root.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
