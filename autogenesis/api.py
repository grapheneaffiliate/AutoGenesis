"""The Capability API — the agnostic interface contract (§3).

A company provides a Genome Bundle; the framework exposes this API. Everything
robot-specific lives in the genome; everything reusable lives here. Phase 1
implements the information-spine subset:

    ingest(robot_id, description, modules)  -> Genome           (validated, addressed)
    diagnose(genome, telemetry_window)      -> [Fault]          (ranked)
    plan_repair(genome, fault)              -> VerifiedRepair    (procedure + certificate)

Anything returned as *Verified* carries a machine-checkable certificate. The
``Capability`` object threads an L6 ledger through every call so the full
provenance chain is recorded. Phase 2 adds plan_part / plan_build / closure.
"""

from __future__ import annotations

from dataclasses import dataclass

from .genome import Genome, address, extract, from_dict, from_urdf, validate
from .genome.validation import ValidationReport
from .governance import Ledger
from .synthesis import Fault, diagnose as _diagnose, plan_repair_procedure
from .synthesis.repair import RepairProcedure
from .verify import Certificate, certify, verify_against


class IngestError(ValueError):
    """Raised when a genome fails the L0 validation gate."""

    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__("; ".join(report.errors))


@dataclass
class VerifiedRepair:
    """A repair procedure inseparable from its certificate.

    ``executable`` is the single bit an executor (L4) checks: it is True only
    when the certificate passed *and* still matches the procedure byte-for-byte.
    """
    procedure: RepairProcedure
    certificate: Certificate

    @property
    def executable(self) -> bool:
        return self.certificate.passed


class Capability:
    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()

    # -- L0 -----------------------------------------------------------------
    def ingest(self, robot_id: str, description: dict | str,
               modules: dict | None = None) -> Genome:
        """Validate, extract, content-address and record a genome.

        ``description`` may be a structured bundle dict or a URDF/XML string.
        ``modules`` (optional) is merged over a URDF-derived genome to enrich it.
        """
        if isinstance(description, str):
            genome = from_urdf(description, robot_id=robot_id)
            if modules:
                merged = {**genome.to_dict(), **modules, "robot_id": robot_id}
                genome = from_dict(merged)
        else:
            genome = from_dict({**description, "robot_id": robot_id})

        extract(genome)                       # fill inferable gaps (assembly graph)
        report = validate(genome)
        if not report.ok:
            self.ledger.append("ingest_rejected",
                               {"robot_id": robot_id, "errors": report.errors})
            raise IngestError(report)

        address(genome)
        self.ledger.append("ingest", {
            "robot_id": robot_id,
            "genome_hash": genome.content_hash,
            "warnings": report.warnings,
        })
        return genome

    # -- L2 -----------------------------------------------------------------
    def diagnose(self, genome: Genome,
                 telemetry_window: dict) -> list[Fault]:
        faults = _diagnose(genome, telemetry_window)
        self.ledger.append("diagnose", {
            "genome_hash": genome.content_hash,
            "faults": [{"id": f.id, "part": f.part_id, "score": f.score}
                       for f in faults],
        })
        return faults

    # -- L2 synthesis + L3 gate --------------------------------------------
    def plan_repair(self, genome: Genome, fault: Fault) -> VerifiedRepair:
        """Synthesise a repair (L2) and gate it through the L3 certificate.

        The returned object is always certificate-bound; an executor must check
        ``executable`` before acting. Uncertified procedures never propagate.
        """
        procedure = plan_repair_procedure(genome, fault)
        cert = certify(genome, procedure, fault.part_id, fault.repair_part_id)
        self.ledger.append("certify", {
            "genome_hash": genome.content_hash,
            "fault": fault.id,
            "artifact_hash": cert.artifact_hash,
            "passed": cert.passed,
            "checks": {k: v["passed"] for k, v in cert.checks.items()},
        })
        return VerifiedRepair(procedure=procedure, certificate=cert)

    # -- L4 seam ------------------------------------------------------------
    def admit_to_executor(self, genome: Genome, repair: VerifiedRepair,
                          fault: Fault) -> bool:
        """The executor-side gate: independently re-verify before execution.

        Returns True only if the certificate passes a fresh, independent
        re-check bound to this exact procedure and genome (tamper-evident)."""
        ok = verify_against(repair.certificate, genome, repair.procedure,
                            fault.part_id, fault.repair_part_id)
        self.ledger.append("admit", {
            "genome_hash": genome.content_hash,
            "fault": fault.id,
            "admitted": ok,
        })
        return ok
