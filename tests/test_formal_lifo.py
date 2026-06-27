"""L3 — deeper coverage for the formal/spec proofs (§12: a check must be
*proven able to fail* on a known-bad input).

The rrbot FMEA fault (elbow_servo) has a single access blocker (forearm), so the
multi-element LIFO reverse-pairing and the inclusive tolerance-band boundaries
were never exercised by a known-bad input. These tests drive a *deeper* fault
(shoulder_servo → three stacked blockers) and the exact band edges so the
ordering, conservation and torque obligations are each shown to reject a
deliberately broken artifact — and to accept the valid one.
"""

import copy

import pytest

from autogenesis.genome import address, from_dict
from autogenesis.synthesis import plan_repair_procedure
from autogenesis.synthesis.diagnosis import Fault
from autogenesis.verify import check_formal, check_spec
from examples.rrbot import RRBOT_BUNDLE


def _genome():
    return address(from_dict(RRBOT_BUNDLE))


def _deep_fault():
    """A fault on the deepest serviceable part: shoulder_servo sits under
    upper_arm, elbow_servo and forearm, so three parts must be disassembled to
    reach it — a genuine multi-element LIFO traversal."""
    return Fault(
        id="f_shoulder", failure_mode_id="synthetic", part_id="shoulder_servo",
        mode="bearing wear", signal="shoulder_vib", observed=1.0, threshold=0.0,
        comparator=">", severity=6, score=6.0, repair_part_id="shoulder_servo",
    )


def _deep_procedure():
    g = _genome()
    proc = plan_repair_procedure(g, _deep_fault())
    return g, proc


# -- the multi-blocker traversal is real ------------------------------------
def test_deep_fault_produces_three_blocker_traversal():
    _, proc = _deep_procedure()
    disasm = [s.part_id for s in proc.steps if s.action == "disassemble"]
    reasm = [s.part_id for s in proc.steps if s.action == "reassemble"]
    assert disasm == ["forearm", "elbow_servo", "upper_arm"]   # last-built first
    assert reasm == list(reversed(disasm))                     # LIFO mirror


def test_deep_valid_procedure_passes_formal():
    _, proc = _deep_procedure()
    res = check_formal(proc)
    assert res.passed
    assert all(inv["passed"] for inv in res.invariants)


# -- LIFO mirror is proven able to fail (>1 blocker) ------------------------
def test_lifo_mirror_violation_rejected():
    _, proc = _deep_procedure()
    bad = copy.deepcopy(proc)
    reasm = [s for s in bad.steps if s.action == "reassemble"]
    # Reassemble in the *same* order as disassembly instead of the reverse.
    reasm[0].part_id, reasm[-1].part_id = reasm[-1].part_id, reasm[0].part_id
    res = check_formal(bad)
    assert not res.passed
    assert any("ordering" in r for r in res.reasons)


# -- phase ordering (disassembly before removal) is proven able to fail ------
def test_disassembly_after_removal_rejected():
    _, proc = _deep_procedure()
    bad = copy.deepcopy(proc)
    first_disasm = next(s for s in bad.steps if s.action == "disassemble")
    remove = next(s for s in bad.steps if s.action == "remove")
    first_disasm.order, remove.order = remove.order, first_disasm.order
    res = check_formal(bad)
    assert not res.passed
    assert any("ordering" in r for r in res.reasons)


# -- conservation is proven able to fail when a middle blocker is dropped ----
def test_conservation_rejects_dropped_middle_blocker():
    _, proc = _deep_procedure()
    bad = copy.deepcopy(proc)
    # Drop the reassembly of the middle blocker (elbow_servo) only.
    bad.steps = [
        s for s in bad.steps
        if not (s.action == "reassemble" and s.part_id == "elbow_servo")
    ]
    res = check_formal(bad)
    assert not res.passed
    assert any("conservation" in r for r in res.reasons)


# -- z3 and native must agree (no disagreement on any deep-fault verdict) ----
def test_formal_engine_paths_agree_on_deep_fault():
    _, proc = _deep_procedure()
    res = check_formal(proc)
    # A z3/native disagreement is recorded as an explicit reason and a hard fail.
    assert not any("disagreement" in r for r in res.reasons)
    assert res.engine in ("z3", "native")


# -- tolerance band boundaries are inclusive (closed interval) --------------
@pytest.mark.parametrize("torque,expected", [
    (2.25, True),    # exact lower edge of [2.25, 2.75]
    (2.75, True),    # exact upper edge
    (2.2499, False),  # just below
    (2.7501, False),  # just above
])
def test_spec_torque_band_boundaries(torque, expected):
    g = _genome()
    # elbow_servo fault: install torque on elbow_servo_spare, band [2.25, 2.75].
    fault = Fault(
        id="f_elbow", failure_mode_id="fm_elbow_overheat", part_id="elbow_servo",
        mode="thermal overload", signal="elbow_temp", observed=90.0,
        threshold=75.0, comparator=">", severity=8, score=8.0,
        repair_part_id="elbow_servo_spare",
    )
    proc = plan_repair_procedure(g, fault)
    install = next(s for s in proc.steps if s.action == "install")
    install.torque = torque
    res = check_spec(g, fault.repair_part_id, fault.part_id, proc)
    assert res.passed is expected
