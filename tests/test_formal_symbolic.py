"""L3 — the symbolic ordering proof reasons over the assembly hierarchy.

After the §9-ratified strengthening, INV-ORDERING is discharged over free Z3
position variables with the LIFO mirror and the hierarchy precedence as solver
constraints (plus a satisfiability proof). These tests pin down the behaviour
that distinguishes the strengthened proof from the old structural compare:

  * a mirror-consistent but *hierarchy-violating* disassembly order is rejected
    when the genome is supplied (the precedence clause catches it), while the
    genome-less check — which only knows the mirror — cannot; and
  * the consistency obligation (the hierarchy admits a valid LIFO traversal) is
    recorded for a valid procedure.
"""

import copy

from autogenesis.genome import address, from_dict
from autogenesis.synthesis import plan_repair_procedure
from autogenesis.synthesis.diagnosis import Fault
from autogenesis.verify import check_formal
from examples.rrbot import RRBOT_BUNDLE


def _deep_proc():
    g = address(from_dict(RRBOT_BUNDLE))
    fault = Fault(
        id="f_shoulder", failure_mode_id="synthetic", part_id="shoulder_servo",
        mode="bearing wear", signal="shoulder_vib", observed=1.0, threshold=0.0,
        comparator=">", severity=6, score=6.0, repair_part_id="shoulder_servo",
    )
    return g, plan_repair_procedure(g, fault)


def _reorder(proc, disasm_parts, reasm_parts):
    """Rebuild the procedure with the given disassembly/reassembly part orders,
    reassigning contiguous ``.order`` indices (phase structure preserved)."""
    p = copy.deepcopy(proc)
    d = {s.part_id: s for s in p.steps if s.action == "disassemble"}
    r = {s.part_id: s for s in p.steps if s.action == "reassemble"}
    rm = next(s for s in p.steps if s.action == "remove")
    ins = next(s for s in p.steps if s.action == "install")
    tail = [s for s in p.steps if s.action == "calibrate"]
    seq = ([d[x] for x in disasm_parts] + [rm, ins]
           + [r[x] for x in reasm_parts] + tail)
    for i, s in enumerate(seq):
        s.order = i
    p.steps = seq
    return p


def test_valid_deep_procedure_passes_with_and_without_genome():
    g, proc = _deep_proc()
    assert check_formal(proc).passed            # genome-less
    assert check_formal(proc, g).passed         # hierarchy-aware


def test_consistency_invariant_recorded_for_valid_procedure():
    g, proc = _deep_proc()
    res = check_formal(proc, g)
    inv = {i["name"]: i["passed"] for i in res.invariants}
    assert inv["ordering"] and inv["consistency"] and inv["conservation"]


def test_hierarchy_violation_caught_only_with_genome():
    """forearm→elbow_servo→upper_arm is the valid (top-first) disassembly.
    Swapping elbow_servo and upper_arm keeps a consistent LIFO mirror but
    removes upper_arm before the elbow_servo stacked on top of it — a hierarchy
    violation. Only the genome-aware proof, which encodes the precedence edge,
    can reject it."""
    g, proc = _deep_proc()
    bad = _reorder(
        proc,
        disasm_parts=["forearm", "upper_arm", "elbow_servo"],
        reasm_parts=["elbow_servo", "upper_arm", "forearm"],   # exact reverse
    )
    # The mirror still holds, so the genome-less check is satisfied...
    assert check_formal(bad).passed
    # ...but the hierarchy-aware proof rejects the precedence violation.
    res = check_formal(bad, g)
    assert not res.passed
    assert any("ordering" in r for r in res.reasons)


def test_strengthened_proof_still_accepts_correct_hierarchy_order():
    g, proc = _deep_proc()
    good = _reorder(
        proc,
        disasm_parts=["forearm", "elbow_servo", "upper_arm"],
        reasm_parts=["upper_arm", "elbow_servo", "forearm"],
    )
    assert check_formal(good, g).passed
