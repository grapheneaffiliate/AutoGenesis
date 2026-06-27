"""L3 — the symbolic ordering proof generalises from chains to DAGs.

rrbot is a linear chain, so its access blockers form a *total* order. This
fixture is a forked assembly: a shared ``column`` carries two independent
branches (left bracket→sensor, right bracket→sensor). Servicing the column
requires disassembling *both* branches, whose relative order is unconstrained —
a genuine partial order. These tests confirm the hierarchy-aware proof:

  * accepts the planner's order and *any* other valid LIFO linearisation
    (independent branches may interleave), and
  * still rejects an order that violates a within-branch precedence edge.
"""

import copy

from autogenesis.genome.schema import (
    AssemblyStep,
    Genome,
    Part,
    SafetyEnvelope,
    Tolerance,
)
from autogenesis.synthesis import plan_repair_procedure
from autogenesis.synthesis.diagnosis import Fault
from autogenesis.verify import check_formal


def _branched_genome() -> Genome:
    parts = [
        Part("base", "Base"),
        Part("column", "Column", parent_id="base"),
        Part("l_bracket", "Left bracket", parent_id="column"),
        Part("l_sensor", "Left sensor", parent_id="l_bracket"),
        Part("r_bracket", "Right bracket", parent_id="column"),
        Part("r_sensor", "Right sensor", parent_id="r_bracket"),
        Part("column_spare", "Column (replacement)"),
    ]
    assembly = [
        AssemblyStep("a0", "base", []),
        AssemblyStep("a1", "column", ["a0"], torque=4.0),
        AssemblyStep("a2", "l_bracket", ["a1"], torque=2.0),
        AssemblyStep("a3", "l_sensor", ["a2"], torque=1.0),
        AssemblyStep("a4", "r_bracket", ["a1"], torque=2.0),
        AssemblyStep("a5", "r_sensor", ["a4"], torque=1.0),
    ]
    tolerances = [Tolerance("column_spare", torque_spec=4.0, torque_tol=0.1)]
    return Genome(
        robot_id="branched", parts=parts, assembly=assembly,
        tolerances=tolerances, safety=SafetyEnvelope(),
    )


def _column_fault() -> Fault:
    return Fault(
        id="f_column", failure_mode_id="synthetic", part_id="column",
        mode="crack", signal="strain", observed=1.0, threshold=0.0,
        comparator=">", severity=7, score=7.0, repair_part_id="column_spare",
    )


def _proc():
    g = _branched_genome()
    return g, plan_repair_procedure(g, _column_fault())


def _reorder(proc, disasm_parts, reasm_parts):
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


def test_branched_fault_disassembles_both_branches():
    _, proc = _proc()
    disasm = {s.part_id for s in proc.steps if s.action == "disassemble"}
    assert disasm == {"l_bracket", "l_sensor", "r_bracket", "r_sensor"}


def test_planner_order_passes_hierarchy_proof():
    g, proc = _proc()
    res = check_formal(proc, g)
    assert res.passed
    assert {i["name"]: i["passed"] for i in res.invariants}["consistency"]


def test_alternative_valid_linearisation_accepted():
    """Left and right branches are independent, so interleaving them differently
    is still a valid LIFO traversal — the proof must accept it (not just the
    planner's exact order). Each branch keeps sensor-before-bracket on the way
    out, and reassembly is the exact reverse."""
    g, proc = _proc()
    alt = _reorder(
        proc,
        disasm_parts=["r_sensor", "l_sensor", "r_bracket", "l_bracket"],
        reasm_parts=["l_bracket", "r_bracket", "l_sensor", "r_sensor"],
    )
    assert check_formal(alt, g).passed


def test_within_branch_precedence_violation_rejected():
    """Removing l_bracket before the l_sensor stacked on it violates a real
    precedence edge — rejected even though the LIFO mirror is intact."""
    g, proc = _proc()
    bad = _reorder(
        proc,
        disasm_parts=["r_sensor", "r_bracket", "l_bracket", "l_sensor"],
        reasm_parts=["l_sensor", "l_bracket", "r_bracket", "r_sensor"],
    )
    assert check_formal(bad).passed            # genome-less can't see it
    res = check_formal(bad, g)
    assert not res.passed                       # hierarchy-aware proof rejects it
    assert any("ordering" in r for r in res.reasons)
