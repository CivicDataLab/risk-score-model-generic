"""Pytest configuration: make the repository root importable.

The scripts import packages relative to the repository root (e.g.
``from config.loader import load_config`` and ``import scripts.dea``), so the
root must be on sys.path when the tests import them directly.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
