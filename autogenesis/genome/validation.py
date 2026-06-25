"""L0 — The validation gate.

Ingestion is a gate, not a pass-through. A genome that fails required-module
or referential-integrity checks never receives a content address and therefore
can never be referenced by a certificate or the ledger. Validation returns a
structured report (errors hard-fail; warnings flag graceful-degradation gaps)
so the autonomy loop gets a *number*, not a vibe (§12).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import Genome


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:          # truthy iff valid
        return self.ok


def validate(genome: Genome) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    # -- required modules ---------------------------------------------------
    if not genome.robot_id:
        errors.append("robot_id is required")
    if not genome.links:
        errors.append("kinematics: at least one link is required")
    if not genome.joints:
        errors.append("kinematics: at least one joint is required")
    if not genome.parts:
        errors.append("bom: at least one part is required")
    if genome.safety is None:
        errors.append("safety envelope is required")

    # -- safety envelope sanity --------------------------------------------
    if genome.safety is not None:
        for fld in ("max_force_N", "max_speed_mps", "max_power_W"):
            val = getattr(genome.safety, fld)
            if val is None or val <= 0:
                errors.append(f"safety.{fld} must be positive (got {val})")

    # -- referential integrity ---------------------------------------------
    part_ids = {p.id for p in genome.parts}
    if len(part_ids) != len(genome.parts):
        errors.append("bom: duplicate part ids")
    for p in genome.parts:
        if p.parent_id is not None and p.parent_id not in part_ids:
            errors.append(f"bom: part {p.id} references unknown parent {p.parent_id}")
        if p.quantity <= 0:
            errors.append(f"bom: part {p.id} quantity must be positive")
        if p.make_or_buy not in ("make", "buy"):
            errors.append(f"bom: part {p.id} make_or_buy invalid: {p.make_or_buy}")

    link_names = {l.name for l in genome.links}
    for j in genome.joints:
        if j.parent not in link_names:
            errors.append(f"joint {j.name} references unknown parent link {j.parent}")
        if j.child not in link_names:
            errors.append(f"joint {j.name} references unknown child link {j.child}")
        if j.type in ("revolute", "prismatic") and j.upper < j.lower:
            errors.append(f"joint {j.name}: upper limit below lower limit")

    for t in genome.tolerances:
        if t.part_id not in part_ids:
            errors.append(f"tolerance references unknown part {t.part_id}")

    for fm in genome.failure_modes:
        if fm.part_id not in part_ids:
            errors.append(f"fmea {fm.id} references unknown part {fm.part_id}")
        if fm.repair_part_id and fm.repair_part_id not in part_ids:
            errors.append(f"fmea {fm.id} repair_part {fm.repair_part_id} unknown")
        if not 1 <= fm.severity <= 10:
            errors.append(f"fmea {fm.id} severity out of range 1..10")
        if fm.detection_signal and genome.signal(fm.detection_signal) is None:
            warnings.append(
                f"fmea {fm.id} references signal '{fm.detection_signal}' "
                "not in telemetry schema"
            )

    step_ids = {s.step_id for s in genome.assembly}
    if len(step_ids) != len(genome.assembly):
        errors.append("assembly: duplicate step ids")
    for s in genome.assembly:
        if s.part_id not in part_ids:
            errors.append(f"assembly step {s.step_id} references unknown part {s.part_id}")
        for pre in s.predecessors:
            if pre not in step_ids:
                errors.append(
                    f"assembly step {s.step_id} predecessor {pre} unknown"
                )

    # -- graceful-degradation advisories -----------------------------------
    if not genome.failure_modes:
        warnings.append("no FMEA: diagnosis will be unavailable")
    if not genome.assembly:
        warnings.append("no assembly graph: repair sequencing will be inferred/limited")
    if not genome.telemetry:
        warnings.append("no telemetry schema: predictive maintenance unavailable")
    if not genome.tolerances:
        warnings.append("no tolerances: spec-conformance proofs will be weak")

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)
