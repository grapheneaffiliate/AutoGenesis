"""L0 — Canonical genome schema.

The genome is the single source of engineering intent. Every robot-specific
fact lives here; the substrate (L1-L6) is reusable across morphologies. The
schema is intentionally a plain, JSON-serialisable dataclass tree so it can be
content-addressed (hashed) and round-tripped without surprises.

Modules degrade gracefully: kinematics, BOM and the safety envelope are
required; everything else (tolerances, FMEA, assembly graph, telemetry) makes
the substrate able to do *more*, but its absence never crashes ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Kinematics & geometry
# --------------------------------------------------------------------------- #
@dataclass
class Link:
    name: str
    mass: float = 0.0


@dataclass
class Joint:
    name: str
    type: str                       # revolute | prismatic | fixed | continuous
    parent: str
    child: str
    lower: float = 0.0              # rad or m
    upper: float = 0.0
    effort: float = 0.0             # N·m or N
    velocity: float = 0.0           # rad/s or m/s


# --------------------------------------------------------------------------- #
# Bill of materials
# --------------------------------------------------------------------------- #
@dataclass
class Part:
    id: str
    name: str
    parent_id: Optional[str] = None  # hierarchical BOM
    quantity: int = 1
    make_or_buy: str = "buy"         # make | buy
    sourcing: Optional[str] = None


# --------------------------------------------------------------------------- #
# Tolerances & specs (for repair synthesis)
# --------------------------------------------------------------------------- #
@dataclass
class Tolerance:
    part_id: str
    dimension: str = "fit"
    nominal: float = 0.0
    plus: float = 0.0
    minus: float = 0.0
    material: Optional[str] = None
    torque_spec: Optional[float] = None   # N·m, fastener install torque
    torque_tol: float = 0.10              # fractional tolerance band on torque


# --------------------------------------------------------------------------- #
# Failure modes (FMEA)
# --------------------------------------------------------------------------- #
@dataclass
class FailureMode:
    id: str
    part_id: str
    mode: str
    symptoms: list[str] = field(default_factory=list)
    detection_signal: Optional[str] = None
    threshold: Optional[float] = None
    comparator: str = ">"            # > | < | >= | <=
    severity: int = 5               # 1..10 (FMEA severity)
    repair_part_id: Optional[str] = None  # replacement; defaults to part_id


# --------------------------------------------------------------------------- #
# Assembly graph
# --------------------------------------------------------------------------- #
@dataclass
class AssemblyStep:
    step_id: str
    part_id: str
    predecessors: list[str] = field(default_factory=list)  # step_ids built first
    mating: str = "fastener"         # fastener | press_fit | connector | weld
    access_clearance_mm: float = 20.0
    tooling: list[str] = field(default_factory=list)
    torque: Optional[float] = None   # N·m applied at this step
    lever_arm_m: float = 0.05        # for force estimation in L1


# --------------------------------------------------------------------------- #
# Maintenance plan
# --------------------------------------------------------------------------- #
@dataclass
class MaintenanceTask:
    task_id: str
    part_id: str
    interval_hours: float
    consumable: Optional[str] = None
    calibration: bool = False


# --------------------------------------------------------------------------- #
# Telemetry schema
# --------------------------------------------------------------------------- #
@dataclass
class Signal:
    name: str
    semantics: str = ""
    nominal_min: Optional[float] = None
    nominal_max: Optional[float] = None
    unit: str = ""


# --------------------------------------------------------------------------- #
# Safety envelope (required)
# --------------------------------------------------------------------------- #
@dataclass
class SafetyEnvelope:
    max_force_N: float = 150.0
    max_speed_mps: float = 2.0
    max_power_W: float = 500.0
    iso_zone: str = "collaborative"   # ISO 10218 / TS 15066 zone
    estop_behavior: str = "category_1"


# --------------------------------------------------------------------------- #
# Genome
# --------------------------------------------------------------------------- #
@dataclass
class Genome:
    robot_id: str
    version: str = "0.0.0"
    links: list[Link] = field(default_factory=list)
    joints: list[Joint] = field(default_factory=list)
    parts: list[Part] = field(default_factory=list)
    tolerances: list[Tolerance] = field(default_factory=list)
    failure_modes: list[FailureMode] = field(default_factory=list)
    assembly: list[AssemblyStep] = field(default_factory=list)
    maintenance: list[MaintenanceTask] = field(default_factory=list)
    telemetry: list[Signal] = field(default_factory=list)
    safety: SafetyEnvelope = field(default_factory=SafetyEnvelope)
    content_hash: Optional[str] = None   # filled by content.address()

    # -- convenience lookups -------------------------------------------------
    def part(self, part_id: str) -> Optional[Part]:
        return next((p for p in self.parts if p.id == part_id), None)

    def tolerance(self, part_id: str) -> Optional[Tolerance]:
        return next((t for t in self.tolerances if t.part_id == part_id), None)

    def failure_mode(self, fm_id: str) -> Optional[FailureMode]:
        return next((f for f in self.failure_modes if f.id == fm_id), None)

    def signal(self, name: str) -> Optional[Signal]:
        return next((s for s in self.telemetry if s.name == name), None)

    def step_for_part(self, part_id: str) -> Optional[AssemblyStep]:
        return next((s for s in self.assembly if s.part_id == part_id), None)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
