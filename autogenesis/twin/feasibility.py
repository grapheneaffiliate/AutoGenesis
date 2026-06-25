"""L1 — Feasibility oracle (the simulation seam).

Phase 1 ships an *analytic* oracle: it computes numeric witnesses for each
procedure step (access clearance, required force, motion speed, mechanical
power, joint reachability) and checks them against the genome's limits. The
witnesses are real numbers, so the L3 safety gate and certificate quote
evidence, not adjectives.

The seam is the contract: a high-fidelity simulator (collision, contact
dynamics, stability) slots in behind the same ``assess`` signature and the same
``FeasibilityReport`` shape, with no change above L1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..genome.schema import Genome
from ..synthesis.repair import RepairProcedure, RepairStep

# A tool needs at least this much clearance (mm) to engage a fastener/connector.
MIN_TOOL_CLEARANCE_MM = 8.0
# Nominal service motion speed used for power estimation (m/s).
SERVICE_SPEED_MPS = 0.10


@dataclass
class StepWitness:
    order: int
    action: str
    part_id: str
    clearance_mm: float
    required_force_N: float
    speed_mps: float
    power_W: float
    reachable: bool
    feasible: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class FeasibilityReport:
    feasible: bool
    max_force_N: float
    max_speed_mps: float
    max_power_W: float
    witnesses: list[StepWitness] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _force_for_step(step: RepairStep) -> float:
    """Estimate the manipulation force (N) a step demands.

    For torqued matings, F = torque / lever_arm. Non-torqued matings use a
    modest handling force proportional to access tightness.
    """
    if step.torque:
        lever = step.lever_arm_m or 0.05
        return abs(step.torque) / lever
    if step.action in ("disassemble", "reassemble", "remove", "install"):
        return 15.0
    return 0.0


def assess(genome: Genome, procedure: RepairProcedure) -> FeasibilityReport:
    safety = genome.safety
    witnesses: list[StepWitness] = []
    reasons: list[str] = []
    max_force = max_speed = max_power = 0.0

    for step in procedure.steps:
        force = _force_for_step(step)
        speed = 0.0 if step.action == "calibrate" else SERVICE_SPEED_MPS
        power = force * speed
        clearance = step.access_clearance_mm
        reachable = clearance >= MIN_TOOL_CLEARANCE_MM
        step_reasons: list[str] = []

        if not reachable:
            step_reasons.append(
                f"clearance {clearance:.1f}mm < tool minimum "
                f"{MIN_TOOL_CLEARANCE_MM:.1f}mm"
            )
        if force > safety.max_force_N:
            step_reasons.append(
                f"force {force:.1f}N exceeds envelope {safety.max_force_N:.1f}N"
            )
        if power > safety.max_power_W:
            step_reasons.append(
                f"power {power:.1f}W exceeds envelope {safety.max_power_W:.1f}W"
            )

        step_feasible = not step_reasons
        witnesses.append(
            StepWitness(
                order=step.order,
                action=step.action,
                part_id=step.part_id,
                clearance_mm=round(clearance, 3),
                required_force_N=round(force, 3),
                speed_mps=round(speed, 3),
                power_W=round(power, 3),
                reachable=reachable,
                feasible=step_feasible,
                reasons=step_reasons,
            )
        )
        reasons.extend(f"step {step.order} ({step.action}): {r}" for r in step_reasons)
        max_force = max(max_force, force)
        max_speed = max(max_speed, speed)
        max_power = max(max_power, power)

    return FeasibilityReport(
        feasible=all(w.feasible for w in witnesses),
        max_force_N=round(max_force, 3),
        max_speed_mps=round(max_speed, 3),
        max_power_W=round(max_power, 3),
        witnesses=witnesses,
        reasons=reasons,
    )
