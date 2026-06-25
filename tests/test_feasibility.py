"""L1 — analytic feasibility oracle."""

from autogenesis.genome import from_dict
from autogenesis.synthesis import diagnose, plan_repair_procedure
from autogenesis.twin import assess
from examples.rrbot import RRBOT_BUNDLE


def _proc(genome):
    fault = diagnose(genome, {"elbow_temp": [90]})[0]
    return plan_repair_procedure(genome, fault)


def test_feasible_procedure_within_envelope():
    g = from_dict(RRBOT_BUNDLE)
    report = assess(g, _proc(g))
    assert report.feasible
    assert report.max_force_N > 0           # witnesses are real numbers
    assert report.witnesses


def test_infeasible_when_force_exceeds_envelope():
    bundle = dict(RRBOT_BUNDLE)
    bundle = {**bundle, "safety": {**RRBOT_BUNDLE["safety"], "max_force_N": 10.0}}
    g = from_dict(bundle)
    report = assess(g, _proc(g))
    assert not report.feasible
    assert any("force" in r for r in report.reasons)


def test_infeasible_when_clearance_too_tight():
    bundle = {**RRBOT_BUNDLE}
    asm = [dict(s) for s in RRBOT_BUNDLE["assembly"]]
    for s in asm:
        if s["part_id"] == "forearm":
            s["access_clearance_mm"] = 2.0     # below tool minimum
    bundle = {**bundle, "assembly": asm}
    g = from_dict(bundle)
    report = assess(g, _proc(g))
    assert not report.feasible
    assert any("clearance" in r for r in report.reasons)
