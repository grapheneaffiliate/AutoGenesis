"""L2 — diagnosis and repair synthesis."""

import copy

from autogenesis.genome import from_dict
from autogenesis.synthesis import diagnose, plan_repair_procedure
from examples.rrbot import RRBOT_BUNDLE


def _genome():
    return from_dict(RRBOT_BUNDLE)


def test_diagnose_detects_overheat_fault():
    g = _genome()
    faults = diagnose(g, {"elbow_temp": [60, 72, 81]})
    assert len(faults) == 1
    f = faults[0]
    assert f.part_id == "elbow_servo"
    assert f.repair_part_id == "elbow_servo_spare"
    assert f.observed == 81


def test_diagnose_quiet_on_nominal_telemetry():
    # Known-bad input for the acceptance gate: nominal telemetry => no fault.
    g = _genome()
    assert diagnose(g, {"elbow_temp": [40, 55, 68]}) == []


def test_diagnose_ranks_by_severity_and_exceedance():
    bundle = copy.deepcopy(RRBOT_BUNDLE)
    bundle["failure_modes"].append({
        "id": "fm_overcurrent", "part_id": "elbow_servo",
        "mode": "overcurrent", "detection_signal": "elbow_current",
        "threshold": 4.0, "comparator": ">", "severity": 4,
        "repair_part_id": "elbow_servo_spare",
    })
    g = from_dict(bundle)
    faults = diagnose(g, {"elbow_temp": [90], "elbow_current": [4.2]})
    assert [f.failure_mode_id for f in faults][0] == "fm_elbow_overheat"
    assert faults[0].score > faults[1].score


def test_plan_repair_builds_disassembly_then_reassembly():
    g = _genome()
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    actions = proc.actions()
    # forearm blocks the elbow servo: disassemble it, swap, reassemble it.
    assert actions == ["disassemble", "remove", "install", "reassemble", "calibrate"]
    assert proc.steps[0].part_id == "forearm"
    assert proc.steps[-1].action == "calibrate"


def test_plan_repair_installs_declared_replacement():
    g = _genome()
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    install = next(s for s in proc.steps if s.action == "install")
    remove = next(s for s in proc.steps if s.action == "remove")
    assert remove.part_id == "elbow_servo"
    assert install.part_id == "elbow_servo_spare"
    assert install.torque == 2.5            # from the replacement's torque spec


def test_plan_repair_conserves_access_parts():
    g = _genome()
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    disasm = [s.part_id for s in proc.steps if s.action == "disassemble"]
    reasm = [s.part_id for s in proc.steps if s.action == "reassemble"]
    assert sorted(disasm) == sorted(reasm)
