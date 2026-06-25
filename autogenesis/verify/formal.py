"""L3.3 — Formal correctness of the procedure's structural invariants.

AI-generated artifacts are broken by default; the only ground-truth defense is
a proof, not a test suite (§6). We prove two structural invariants of the
repair procedure and discharge the ordering invariant to Z3.

  * **INV-CONSERVATION** — every part disassembled for access is reassembled
    (no part left out), there is exactly one removal (the faulty part) and one
    installation (its replacement). A repair must not silently delete material.

  * **INV-ORDERING** — the procedure is a valid inverse-then-forward traversal:
    all disassembly precedes the removal, removal precedes installation,
    installation precedes all reassembly, and reassembly is the exact reverse
    (LIFO) of disassembly. Encoded over the concrete step positions; we assert
    the negation of the conjoined ordering predicate and prove it UNSAT.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..synthesis.repair import RepairProcedure
from . import _smt


@dataclass
class FormalResult:
    passed: bool
    engine: str
    invariants: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def check_formal(procedure: RepairProcedure) -> FormalResult:
    steps = procedure.steps
    reasons: list[str] = []
    invariants: list[dict] = []

    disasm = [s for s in steps if s.action == "disassemble"]
    reasm = [s for s in steps if s.action == "reassemble"]
    removes = [s for s in steps if s.action == "remove"]
    installs = [s for s in steps if s.action == "install"]

    # -- INV-CONSERVATION ---------------------------------------------------
    disasm_parts = Counter(s.part_id for s in disasm)
    reasm_parts = Counter(s.part_id for s in reasm)
    conservation = (
        disasm_parts == reasm_parts
        and len(removes) == 1
        and len(installs) == 1
    )
    invariants.append({"name": "conservation", "passed": conservation})
    if disasm_parts != reasm_parts:
        missing = (disasm_parts - reasm_parts) + (reasm_parts - disasm_parts)
        reasons.append(f"conservation: access parts not balanced ({dict(missing)})")
    if len(removes) != 1 or len(installs) != 1:
        reasons.append(
            f"conservation: expected 1 remove/1 install, got "
            f"{len(removes)}/{len(installs)}"
        )

    # -- INV-ORDERING -------------------------------------------------------
    # Concrete positions, then prove the ordering predicate via UNSAT-of-negation.
    pos = {s.order: s for s in steps}
    ordered = sorted(steps, key=lambda s: s.order)
    # contiguity / uniqueness of order indices
    contiguous = [s.order for s in ordered] == list(range(len(ordered)))

    rm = removes[0].order if removes else -1
    ins = installs[0].order if installs else -2
    disasm_pos = [s.order for s in disasm]
    reasm_pos = [s.order for s in reasm]

    def ordering_holds() -> bool:
        if not contiguous:
            return False
        if not (all(p < rm for p in disasm_pos)):
            return False
        if not (rm < ins):
            return False
        if not all(ins < p for p in reasm_pos):
            return False
        # reassembly is the reverse of disassembly (LIFO access)
        if [s.part_id for s in reasm] != [s.part_id for s in reversed(disasm)]:
            return False
        return True

    native_ok = ordering_holds()

    # Z3 encoding of the same predicate over the concrete positions.
    def build(s, z):
        D = [z.IntVal(p) for p in disasm_pos]
        R = [z.IntVal(p) for p in reasm_pos]
        RM, INS = z.IntVal(rm), z.IntVal(ins)
        clauses = [d < RM for d in D] + [RM < INS] + [INS < r for r in R]
        # reverse pairing constraint encoded positionally
        rev_ok = [s.part_id for s in reasm] == [s.part_id for s in reversed(disasm)]
        pred = z.And(*clauses) if clauses else z.BoolVal(True)
        s.add(z.Not(z.And(pred, z.BoolVal(rev_ok and contiguous))))

    proved = _smt.prove_unsat(build) if (removes and installs) else False
    ordering = proved if _smt.HAVE_Z3 else native_ok
    if _smt.HAVE_Z3 and ordering != native_ok:
        ordering = False
        reasons.append("ordering: z3/native disagreement")
    invariants.append({"name": "ordering", "passed": ordering})
    if not native_ok:
        reasons.append("ordering: not a valid inverse-then-forward LIFO traversal")

    return FormalResult(
        passed=conservation and ordering,
        engine=_smt.engine_name(),
        invariants=invariants,
        reasons=reasons,
    )
