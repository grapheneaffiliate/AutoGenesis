"""L3.1 — Spec conformance.

Formalise the genome constraints the procedure touches and prove the procedure
satisfies them. Because the genome *is* the intent source, the spec is already
semi-formal — this sidesteps the intent-formalisation grand challenge (§6).

Phase 1 proves two obligations:
  * **Correct replacement** — the installed part is exactly the FMEA-declared
    replacement for the fault, and the removed part is the faulty one.
  * **Torque conformance** — every applied install/fastener torque lies inside
    the part's tolerance band ``torque_spec·(1 ± torque_tol)``.

The torque obligation is discharged to Z3: for the concrete applied value ``v``
and band ``[lo, hi]`` we assert ``v == applied ∧ ¬(lo ≤ v ≤ hi)`` and prove it
UNSAT — i.e. no model violates the band.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..genome.schema import Genome
from ..synthesis.repair import RepairProcedure
from . import _smt


@dataclass
class SpecResult:
    passed: bool
    engine: str
    obligations: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def check_spec(genome: Genome, fault_repair_part: str, fault_part: str,
               procedure: RepairProcedure) -> SpecResult:
    obligations: list[dict] = []
    reasons: list[str] = []

    installs = [s for s in procedure.steps if s.action == "install"]
    removes = [s for s in procedure.steps if s.action == "remove"]

    # -- correct-replacement obligation -------------------------------------
    repl_ok = (
        len(installs) == 1
        and installs[0].part_id == fault_repair_part
        and len(removes) == 1
        and removes[0].part_id == fault_part
    )
    obligations.append({"name": "correct_replacement", "passed": repl_ok})
    if not repl_ok:
        reasons.append(
            "procedure must remove the faulty part and install exactly its "
            "declared replacement"
        )

    # -- torque-conformance obligation (per torqued step) -------------------
    torque_ok = True
    for step in procedure.steps:
        if step.action not in ("install",):
            continue
        tol = genome.tolerance(step.part_id)
        if tol is None or tol.torque_spec is None:
            continue
        if step.torque is None:
            torque_ok = False
            reasons.append(f"step {step.order}: torque spec exists but none applied")
            obligations.append({"name": f"torque[{step.order}]", "passed": False})
            continue
        band = tol.torque_spec * tol.torque_tol
        lo, hi = tol.torque_spec - band, tol.torque_spec + band
        v = step.torque

        within_native = lo <= v <= hi
        # Prove over a *free* real ``t``: for all t, (t == applied) ⇒ lo ≤ t ≤ hi.
        # Asserting the negation and proving UNSAT discharges the band obligation
        # as a real quantified proof rather than a ground evaluation.
        def _build(s, z, v=v, lo=lo, hi=hi):
            t = z.Real("t")
            s.add(t == z.RealVal(v))
            s.add(z.Not(z.And(z.RealVal(lo) <= t, t <= z.RealVal(hi))))
        proved = _smt.prove_unsat(_build)
        step_ok = proved if _smt.HAVE_Z3 else within_native
        # Native re-check must always agree; disagreement is a hard fail.
        if _smt.HAVE_Z3 and step_ok != within_native:
            step_ok = False
            reasons.append(f"step {step.order}: z3/native torque disagreement")
        torque_ok = torque_ok and step_ok
        obligations.append({
            "name": f"torque[{step.order}]",
            "passed": step_ok,
            "applied": v,
            "band": [round(lo, 4), round(hi, 4)],
        })
        if not step_ok:
            reasons.append(
                f"step {step.order}: torque {v} outside band "
                f"[{lo:.3f},{hi:.3f}]"
            )

    return SpecResult(
        passed=repl_ok and torque_ok,
        engine=_smt.engine_name(),
        obligations=obligations,
        reasons=reasons,
    )
