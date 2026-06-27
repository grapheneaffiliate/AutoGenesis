"""L3 — Certificate composition: proof-carrying maintenance.

An artifact is inseparable from a machine-checkable certificate that it
satisfies its specification. This module composes the four checks — spec
conformance, physical feasibility, formal correctness, safety envelope — into
one certificate bound to a content hash of the exact procedure and the exact
genome it was issued against.

Two properties make this the moat:
  * **Machine-checkable** — ``recheck`` recomputes every obligation from the
    genome + procedure, so a verifier sub-agent can confirm the certificate
    independently of whoever produced it.
  * **Tamper-evident** — the certificate pins ``artifact_hash``. Mutating the
    procedure after issuance changes its hash, so ``verify_against`` rejects it.
    Nothing without a passing, matching certificate may reach an executor.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field

from ..genome.content import canonical_json
from ..genome.schema import Genome
from ..synthesis.repair import RepairProcedure
from ..twin.feasibility import assess
from .formal import check_formal
from .safety import check_safety
from .spec import check_spec


def fingerprint(procedure: RepairProcedure) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(asdict(procedure)).encode()
    ).hexdigest()


@dataclass
class Certificate:
    artifact_hash: str
    genome_hash: str | None
    passed: bool
    checks: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _run_checks(genome: Genome, procedure: RepairProcedure,
                fault_part: str, fault_repair_part: str) -> tuple[bool, dict, list[str]]:
    spec = check_spec(genome, fault_repair_part, fault_part, procedure)
    feas = assess(genome, procedure)
    formal = check_formal(procedure, genome)
    safety = check_safety(genome, feas)

    checks = {
        "spec": {"passed": spec.passed, "engine": spec.engine,
                 "obligations": spec.obligations, "reasons": spec.reasons},
        "feasibility": {"passed": feas.feasible,
                        "max_force_N": feas.max_force_N,
                        "max_speed_mps": feas.max_speed_mps,
                        "max_power_W": feas.max_power_W,
                        "reasons": feas.reasons},
        "formal": {"passed": formal.passed, "engine": formal.engine,
                   "invariants": formal.invariants, "reasons": formal.reasons},
        "safety": {"passed": safety.passed, "limits": safety.limits,
                   "observed": safety.observed, "reasons": safety.reasons},
    }
    passed = spec.passed and feas.feasible and formal.passed and safety.passed
    reasons = (spec.reasons + feas.reasons + formal.reasons + safety.reasons)
    return passed, checks, reasons


def certify(genome: Genome, procedure: RepairProcedure,
            fault_part: str, fault_repair_part: str) -> Certificate:
    """Issue a certificate for ``procedure`` against ``genome``."""
    passed, checks, reasons = _run_checks(
        genome, procedure, fault_part, fault_repair_part
    )
    return Certificate(
        artifact_hash=fingerprint(procedure),
        genome_hash=genome.content_hash,
        passed=passed,
        checks=checks,
        reasons=reasons,
    )


def verify_against(cert: Certificate, genome: Genome, procedure: RepairProcedure,
                   fault_part: str, fault_repair_part: str) -> bool:
    """Independently re-check a certificate against a (possibly tampered)
    procedure. Returns True only if the artifact hash still matches *and* all
    obligations re-pass. This is the executor-side gate."""
    if fingerprint(procedure) != cert.artifact_hash:
        return False
    if genome.content_hash != cert.genome_hash:
        return False
    passed, _, _ = _run_checks(genome, procedure, fault_part, fault_repair_part)
    return passed and cert.passed
