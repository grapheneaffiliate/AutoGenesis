"""Thin SMT helper.

Proof obligations are discharged to Z3 when available. To keep the test suite
and CI hermetic when the solver is absent, every obligation also has a faithful
native re-check; the recorded ``engine`` field tells which produced the verdict.
The two paths implement the *same* predicate, so a passing certificate means
the same thing either way — Z3 simply provides the machine-checkable proof.
"""

from __future__ import annotations

try:
    import z3  # type: ignore
    HAVE_Z3 = True
except Exception:  # pragma: no cover - exercised only without z3 installed
    z3 = None
    HAVE_Z3 = False


def engine_name() -> str:
    return "z3" if HAVE_Z3 else "native"


def prove_unsat(build) -> bool:
    """Return True iff the constraint set built by ``build(solver)`` is UNSAT.

    Callers add the *negation* of the property they want proved; UNSAT then
    means the property holds for all models (a proof). Returns ``False`` if z3
    is unavailable so callers fall back to their native check.
    """
    if not HAVE_Z3:
        return False
    s = z3.Solver()
    build(s, z3)
    return s.check() == z3.unsat


def check_sat(build):
    """Return True iff the constraint set built by ``build(solver)`` is SAT,
    or ``None`` when z3 is unavailable. Used to prove a structural spec is
    *satisfiable* (e.g. the access hierarchy admits a valid LIFO traversal),
    which is a genuine solver search rather than a ground evaluation.
    """
    if not HAVE_Z3:
        return None
    s = z3.Solver()
    build(s, z3)
    return s.check() == z3.sat
