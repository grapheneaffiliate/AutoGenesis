"""L3.3 — Formal correctness of the procedure's structural invariants.

AI-generated artifacts are broken by default; the only ground-truth defense is a
proof, not a test suite (§6). We prove two structural invariants of the repair
procedure; the ordering invariant is discharged to Z3 over *free* symbolic
position variables so the solver genuinely reasons about the structure (rather
than ratifying a precomputed Python boolean).

  * **INV-CONSERVATION** — every part disassembled for access is reassembled
    (no part left out), with exactly one removal (the faulty part) and one
    installation (its replacement). A repair must not silently delete material.

  * **INV-ORDERING** — the procedure is a valid inverse-then-forward traversal.
    Encoded as a structural *spec* over free integer position variables o[step]:
      - **permutation/contiguity** — ``Distinct(o)`` and ``0 ≤ o < N`` (so the
        orders form a genuine linear schedule; checked *inside* the solver);
      - **phase** — every disassembly precedes the removal, removal precedes
        installation, installation precedes every reassembly;
      - **LIFO mirror** — for every pair of access parts (a, b),
        ``(o[Da] < o[Db]) ⇔ (o[Rb] < o[Ra])`` — reassembly is the exact reverse
        permutation of disassembly (generalises "reasm == reverse(disasm)");
      - **hierarchy precedence** (when the genome is supplied) — for every pair
        where part *a* is built on top of part *b*, disassembly removes *a*
        before *b* and reassembly installs *b* before *a*. This ties the proof
        to the assembly hierarchy, so a mirror-consistent but
        hierarchy-violating order is rejected.

    Two Z3 obligations are discharged: **compliance** — the procedure's concrete
    order satisfies the spec (UNSAT of its negation); and **consistency** — the
    spec is satisfiable, i.e. the hierarchy admits a valid LIFO traversal (a SAT
    search over free variables). A faithful native re-check evaluates the same
    predicate; any z3/native disagreement is a hard fail.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from ..genome.schema import Genome
from ..synthesis.repair import RepairProcedure
from . import _smt


@dataclass
class FormalResult:
    passed: bool
    engine: str
    invariants: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _access_precedence(genome: Genome, disasm) -> list[tuple[str, str]]:
    """Return (top_part, deep_part) pairs among the disassembled parts, where
    ``top_part`` is built on top of (transitively depends on) ``deep_part`` in
    the assembly hierarchy — so it must be removed first / installed last."""
    steps = {s.step_id: s for s in genome.assembly}
    preds = {sid: set(s.predecessors) for sid, s in steps.items()}

    def transitive_preds(sid: str) -> set[str]:
        seen: set[str] = set()
        stack = list(preds.get(sid, ()))
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            stack.extend(preds.get(p, ()))
        return seen

    access_ids = {s.step_id for s in disasm if s.step_id}
    pairs: list[tuple[str, str]] = []
    for a in access_ids:
        for b in transitive_preds(a):
            if b in access_ids:
                pairs.append((steps[a].part_id, steps[b].part_id))
    return pairs


def check_formal(procedure: RepairProcedure,
                 genome: Optional[Genome] = None) -> FormalResult:
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
    n = len(steps)
    rm = removes[0] if removes else None
    ins = installs[0] if installs else None
    # access part -> its (unique) disassembly and reassembly step
    Dstep = {s.part_id: s for s in disasm}
    Rstep = {s.part_id: s for s in reasm}
    parts = list(Dstep)
    prec_pairs = (
        _access_precedence(genome, disasm)
        if genome is not None and all(s.step_id for s in disasm)
        else []
    )

    # The structural spec, evaluated natively over an assignment ``o`` mapping
    # each step object to an integer position. This is the *same* predicate the
    # solver encodes below.
    well_formed = (
        rm is not None and ins is not None
        and set(Dstep) == set(Rstep)
        and len(Dstep) == len(disasm) and len(Rstep) == len(reasm)
    )

    def native_spec() -> bool:
        # Evaluate the structural spec over the procedure's own ``.order`` values.
        if not well_formed:
            return False
        if sorted(s.order for s in steps) != list(range(n)):   # permutation
            return False
        if not all(d.order < rm.order for d in disasm):        # phase
            return False
        if not (rm.order < ins.order):
            return False
        if not all(ins.order < r.order for r in reasm):
            return False
        for a in parts:                                        # LIFO mirror
            for b in parts:
                if a == b:
                    continue
                if ((Dstep[a].order < Dstep[b].order) !=
                        (Rstep[b].order < Rstep[a].order)):
                    return False
        for top, deep in prec_pairs:                           # hierarchy precedence
            if not (Dstep[top].order < Dstep[deep].order):
                return False
            if not (Rstep[deep].order < Rstep[top].order):
                return False
        return True

    native_ok = native_spec()

    def _spec_clauses(o, z):
        """The structural spec as a list of z3 constraints over position vars
        (``o`` maps ``id(step)`` -> a free z3 Int)."""
        c = [z.Distinct(*[o[id(s)] for s in steps])]
        for s in steps:
            c += [o[id(s)] >= 0, o[id(s)] < n]
        c += [o[id(d)] < o[id(rm)] for d in disasm]
        c.append(o[id(rm)] < o[id(ins)])
        c += [o[id(ins)] < o[id(r)] for r in reasm]
        for a in parts:
            for b in parts:
                if a == b:
                    continue
                c.append((o[id(Dstep[a])] < o[id(Dstep[b])]) ==
                         (o[id(Rstep[b])] < o[id(Rstep[a])]))
        for top, deep in prec_pairs:
            c.append(o[id(Dstep[top])] < o[id(Dstep[deep])])
            c.append(o[id(Rstep[deep])] < o[id(Rstep[top])])
        return c

    ordering = native_ok
    consistency = native_ok          # planner's valid order witnesses SAT
    if _smt.HAVE_Z3 and well_formed:
        # compliance: pin the concrete order, prove it satisfies the spec.
        def build_compliance(s, z):
            o = {id(st): z.Int(f"o{i}") for i, st in enumerate(steps)}
            for st in steps:
                s.add(o[id(st)] == st.order)
            s.add(z.Not(z.And(*_spec_clauses(o, z))))

        # consistency: free vars, prove the spec is satisfiable (search).
        def build_consistency(s, z):
            o = {id(st): z.Int(f"o{i}") for i, st in enumerate(steps)}
            for clause in _spec_clauses(o, z):
                s.add(clause)

        proved = _smt.prove_unsat(build_compliance)
        sat = _smt.check_sat(build_consistency)
        ordering = proved
        consistency = bool(sat)
        if ordering != native_ok:
            ordering = False
            reasons.append("ordering: z3/native disagreement")

    invariants.append({"name": "ordering", "passed": ordering})
    invariants.append({"name": "consistency", "passed": consistency})
    if not native_ok:
        reasons.append(
            "ordering: not a valid inverse-then-forward LIFO traversal "
            "(permutation, phase, mirror or hierarchy precedence violated)"
        )

    return FormalResult(
        passed=conservation and ordering,
        engine=_smt.engine_name(),
        invariants=invariants,
        reasons=reasons,
    )
