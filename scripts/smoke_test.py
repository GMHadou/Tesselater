#!/usr/bin/env python3
"""Headless smoke test (prefer: pytest)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tesselater.mesh_io import center_on_bed, load_mesh
from tesselater.pipeline import run_pipeline


def main() -> int:
    stl = ROOT / "Files" / "Blade.stl"
    if not stl.is_file():
        print("SKIP: no sample STL")
        return 0
    mesh = center_on_bed(load_mesh(stl), 220, 220)
    report = run_pipeline(mesh)
    print("summary:", report.summary)
    print("supports:\n", report.results["supports"].message)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
