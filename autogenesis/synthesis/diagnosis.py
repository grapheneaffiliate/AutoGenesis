"""L2 — Diagnosis.

Map a telemetry window onto FMEA-declared faults. A fault opens when a
detection signal crosses its threshold in the declared direction. Faults are
ranked by a score combining FMEA severity with how far the signal exceeded the
threshold (exceedance), so the worst, most-confident faults surface first.

This layer *proposes*; it is never trusted directly — every downstream repair
must pass the L3 gate before it can reach an executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..genome.schema import Genome

_CMP = {
    ">": lambda x, t: x > t,
    "<": lambda x, t: x < t,
    ">=": lambda x, t: x >= t,
    "<=": lambda x, t: x <= t,
}


@dataclass
class Fault:
    id: str
    failure_mode_id: str
    part_id: str
    mode: str
    signal: str
    observed: float
    threshold: float
    comparator: str
    severity: int
    score: float
    repair_part_id: str
    symptoms: list[str] = field(default_factory=list)


def _aggregate(values: Sequence[float], comparator: str) -> float:
    """Pick the worst-case sample for the comparator direction."""
    if comparator in (">", ">="):
        return max(values)
    return min(values)


def diagnose(genome: Genome, telemetry_window: dict[str, Sequence[float]]) -> list[Fault]:
    """Return ranked faults implied by a telemetry window.

    ``telemetry_window`` maps signal name -> a sequence of recent samples.
    """
    faults: list[Fault] = []
    for fm in genome.failure_modes:
        if not fm.detection_signal or fm.threshold is None:
            continue
        samples = telemetry_window.get(fm.detection_signal)
        if not samples:
            continue
        observed = _aggregate(samples, fm.comparator)
        test = _CMP.get(fm.comparator, _CMP[">"])
        if not test(observed, fm.threshold):
            continue

        # Exceedance: fractional distance past the threshold, normalised.
        denom = abs(fm.threshold) if fm.threshold else 1.0
        exceedance = abs(observed - fm.threshold) / (denom or 1.0)
        score = fm.severity * (1.0 + min(exceedance, 1.0))

        faults.append(
            Fault(
                id=f"fault_{fm.id}",
                failure_mode_id=fm.id,
                part_id=fm.part_id,
                mode=fm.mode,
                signal=fm.detection_signal,
                observed=observed,
                threshold=fm.threshold,
                comparator=fm.comparator,
                severity=fm.severity,
                score=round(score, 4),
                repair_part_id=fm.repair_part_id or fm.part_id,
                symptoms=list(fm.symptoms),
            )
        )

    faults.sort(key=lambda f: f.score, reverse=True)
    return faults
