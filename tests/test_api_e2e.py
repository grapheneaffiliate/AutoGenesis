"""End-to-end — the Capability API and the maintenance flow (§5).

telemetry -> diagnose -> plan_repair (synth + L3 gate) -> admit_to_executor,
with every step recorded on the L6 ledger.
"""

import copy

import pytest

from autogenesis import Capability, IngestError
from examples.rrbot import RRBOT_BUNDLE, RRBOT_URDF


def test_full_maintenance_flow_is_certified_and_admitted():
    cap = Capability()
    genome = cap.ingest("rrbot", RRBOT_BUNDLE)
    assert genome.content_hash

    faults = cap.diagnose(genome, {"elbow_temp": [60, 78, 90]})
    assert faults, "an overheat fault should be opened"

    repair = cap.plan_repair(genome, faults[0])
    assert repair.executable
    assert repair.certificate.passed

    # Executor-side gate independently re-verifies before acting.
    assert cap.admit_to_executor(genome, repair, faults[0])

    events = [e.event for e in cap.ledger.entries]
    assert events == ["ingest", "diagnose", "certify", "admit"]
    ok, broken = cap.ledger.verify_chain()
    assert ok and broken is None


def test_ingest_rejects_invalid_genome():
    cap = Capability()
    bad = copy.deepcopy(RRBOT_BUNDLE)
    bad["joints"] = []                       # required module missing
    with pytest.raises(IngestError):
        cap.ingest("rrbot", bad)
    # The rejection is still recorded for provenance.
    assert cap.ledger.entries[-1].event == "ingest_rejected"


def test_ingest_from_urdf_string():
    cap = Capability()
    # URDF alone lacks an FMEA/safety-complete BOM but must still ingest
    # (kinematics + inferred assembly + default safety envelope).
    genome = cap.ingest("rrbot", RRBOT_URDF)
    assert genome.robot_id == "rrbot"
    assert genome.assembly                    # inferred during extraction


def test_uncertified_repair_is_not_admitted():
    cap = Capability()
    genome = cap.ingest("rrbot", RRBOT_BUNDLE)
    fault = cap.diagnose(genome, {"elbow_temp": [90]})[0]
    repair = cap.plan_repair(genome, fault)
    # Tamper with the procedure post-certification; admission must refuse it.
    next(s for s in repair.procedure.steps if s.action == "install").torque = 9.9
    assert not cap.admit_to_executor(genome, repair, fault)
