"""L3 — the moat: spec, formal, safety, certificate (incl. tamper detection)."""

import copy
import dataclasses

from autogenesis.genome import address, from_dict
from autogenesis.synthesis import diagnose, plan_repair_procedure
from autogenesis.twin import assess
from autogenesis.verify import (
    certify,
    check_formal,
    check_safety,
    check_spec,
    fingerprint,
    verify_against,
)
from examples.rrbot import RRBOT_BUNDLE


def _setup():
    g = address(from_dict(RRBOT_BUNDLE))
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    return g, fault, proc


# -- spec -------------------------------------------------------------------
def test_spec_passes_for_valid_procedure():
    g, fault, proc = _setup()
    res = check_spec(g, fault.repair_part_id, fault.part_id, proc)
    assert res.passed


def test_spec_fails_on_out_of_band_torque():
    g, fault, proc = _setup()
    install = next(s for s in proc.steps if s.action == "install")
    install.torque = 5.0                    # band is [2.25, 2.75]
    res = check_spec(g, fault.repair_part_id, fault.part_id, proc)
    assert not res.passed


def test_spec_fails_on_wrong_replacement_part():
    g, fault, proc = _setup()
    install = next(s for s in proc.steps if s.action == "install")
    install.part_id = "chassis"
    res = check_spec(g, fault.repair_part_id, fault.part_id, proc)
    assert not res.passed


# -- formal -----------------------------------------------------------------
def test_formal_passes_for_valid_procedure():
    _, _, proc = _setup()
    res = check_formal(proc)
    assert res.passed


def test_formal_fails_when_reassembly_missing():
    _, _, proc = _setup()
    proc.steps = [s for s in proc.steps if s.action != "reassemble"]
    res = check_formal(proc)
    assert not res.passed
    assert any("conservation" in r for r in res.reasons)


def test_formal_fails_on_broken_ordering():
    _, _, proc = _setup()
    # Swap install before remove -> invalid inverse-then-forward order.
    rm = next(s for s in proc.steps if s.action == "remove")
    ins = next(s for s in proc.steps if s.action == "install")
    rm.order, ins.order = ins.order, rm.order
    res = check_formal(proc)
    assert not res.passed


# -- safety -----------------------------------------------------------------
def test_safety_gate_passes_within_limits():
    g, _, proc = _setup()
    res = check_safety(g, assess(g, proc))
    assert res.passed


def test_safety_gate_hard_stops_on_breach():
    bundle = {**RRBOT_BUNDLE, "safety": {**RRBOT_BUNDLE["safety"], "max_force_N": 5.0}}
    g = address(from_dict(bundle))
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    res = check_safety(g, assess(g, proc))
    assert not res.passed


# -- certificate ------------------------------------------------------------
def test_certificate_passes_and_is_machine_checkable():
    g, fault, proc = _setup()
    cert = certify(g, proc, fault.part_id, fault.repair_part_id)
    assert cert.passed
    assert cert.genome_hash == g.content_hash
    assert all(c["passed"] for c in cert.checks.values())
    # Independent re-check confirms it.
    assert verify_against(cert, g, proc, fault.part_id, fault.repair_part_id)


def test_certificate_rejects_tampered_procedure():
    g, fault, proc = _setup()
    cert = certify(g, proc, fault.part_id, fault.repair_part_id)
    # Tamper after issuance: bump a torque out of band.
    tampered = copy.deepcopy(proc)
    next(s for s in tampered.steps if s.action == "install").torque = 9.9
    assert fingerprint(tampered) != cert.artifact_hash
    assert not verify_against(cert, g, tampered, fault.part_id, fault.repair_part_id)


def test_certificate_fails_for_unsafe_genome():
    bundle = {**RRBOT_BUNDLE, "safety": {**RRBOT_BUNDLE["safety"], "max_force_N": 5.0}}
    g = address(from_dict(bundle))
    fault = diagnose(g, {"elbow_temp": [90]})[0]
    proc = plan_repair_procedure(g, fault)
    cert = certify(g, proc, fault.part_id, fault.repair_part_id)
    assert not cert.passed
    assert not cert.checks["safety"]["passed"]
