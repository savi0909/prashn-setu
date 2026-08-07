"""Shared test configuration.

``tests/unit`` must stay free of I/O and finish in a couple of seconds (§13.1).
Anything that needs a real Postgres lives in ``tests/integration`` and gets it
from a throwaway container — see ``tests/integration/conftest.py``.
"""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
