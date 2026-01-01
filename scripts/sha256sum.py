#!/usr/bin/env python3
"""
scripts/sha256sum.py

Small cross-platform SHA256 utility (no external dependencies).

Usage:
  python3 scripts/sha256sum.py path/to/file
  python3 scripts/sha256sum.py path/to/file1 path/to/file2 ...
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from typing import List


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compute SHA256 for one or more files.")
    ap.add_argument("paths", nargs="+", help="File path(s).")
    args = ap.parse_args(argv)

    rc = 0
    for p in args.paths:
        if not os.path.exists(p):
            print(f"ERROR: not found: {p}", file=sys.stderr)
            rc = 2
            continue
        h = sha256_file(p)
        print(f"{h}  {p}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())