#!/usr/bin/env python3
"""brain2.py — COMPATIBILITY SHIM. Do not build on this.

The collection was renamed: BRAIN² is now BRAIN¹ (the pure-fly base;
BRAIN² = BRAIN¹ + enhancement modules). The orchestrator lives in
brain1/brain1.py as class Brain1.

This shim exists for exactly one reason: body_sim.py is sealed (Cory's
standing rule — never modify it) and still does
`from brain2 import BrainSquared, DEFAULT_ROUTING`. The shim re-exports
the renamed names so the sealed file keeps working untouched.

New code: `from brain1 import Brain1`.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_p = os.path.join(_HERE, "brain1")
if _p not in sys.path:
    sys.path.insert(0, _p)

from brain1 import Brain1 as BrainSquared  # noqa: E402,F401
from brain1 import DEFAULT_ROUTING  # noqa: E402,F401

__all__ = ["BrainSquared", "DEFAULT_ROUTING"]
