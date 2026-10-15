#!/usr/bin/env python3
"""Backward-compatible launcher. Prefer: python main.py"""

from main import main

if __name__ == "__main__":
    raise SystemExit(main())
