"""Ensure the repo root is importable so ``autogenesis`` and ``examples`` resolve."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
