"""L3.4 — Safety-envelope gate.

A hard check against the genome's ISO 10218 / TS 15066 envelope. Unlike the
other checks this is not a proof obligation but a guardrail: any breach of
force, speed or power limits is a *hard stop*, not a warning. It consumes the
numeric witnesses produced by the L1 oracle so the verdict cites evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..genome.schema import Genome
from ..twin.feasibility import FeasibilityReport


@dataclass
class SafetyResult:
    passed: bool
    limits: dict
    observed: dict
    reasons: list[str] = field(default_factory=list)


def check_safety(genome: Genome, feas: FeasibilityReport) -> SafetyResult:
    s = genome.safety
    reasons: list[str] = []

    if feas.max_force_N > s.max_force_N:
        reasons.append(
            f"peak force {feas.max_force_N}N > limit {s.max_force_N}N"
        )
    if feas.max_speed_mps > s.max_speed_mps:
        reasons.append(
            f"peak speed {feas.max_speed_mps}m/s > limit {s.max_speed_mps}m/s"
        )
    if feas.max_power_W > s.max_power_W:
        reasons.append(
            f"peak power {feas.max_power_W}W > limit {s.max_power_W}W"
        )

    return SafetyResult(
        passed=not reasons,
        limits={
            "max_force_N": s.max_force_N,
            "max_speed_mps": s.max_speed_mps,
            "max_power_W": s.max_power_W,
            "iso_zone": s.iso_zone,
        },
        observed={
            "max_force_N": feas.max_force_N,
            "max_speed_mps": feas.max_speed_mps,
            "max_power_W": feas.max_power_W,
        },
        reasons=reasons,
    )
