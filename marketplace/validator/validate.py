#!/usr/bin/env python3
"""Compatibility wrapper for the canonical Antigravity plugin doctor."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from scripts.validate_plugins import main
except ImportError as exc:  # pragma: no cover - startup repair path
    print(f"failed to import canonical plugin doctor: {exc}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    sys.exit(main())
