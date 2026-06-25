"""L2 — Repair synthesis by assembly-by-disassembly.

Given a fault, synthesise a repair procedure: disassemble exactly the parts
that block access to the faulty part (in reverse assembly order), remove the
faulty part, install its certified replacement, reassemble the access parts (in
forward order), then recalibrate affected joints.

The planner derives everything from the genome's assembly graph, so the
resulting procedure is *structurally* a valid inverse-then-forward traversal —
a property the L3 formal check independently proves rather than trusts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..genome.schema import AssemblyStep, Genome
from .diagnosis import Fault


@dataclass
class RepairStep:
    order: int
    action: str            # disassemble | remove | install | reassemble | calibrate
    part_id: str
    step_id: Optional[str] = None
    mating: str = ""
    tooling: list[str] = field(default_factory=list)
    torque: Optional[float] = None
    access_clearance_mm: float = 20.0
    lever_arm_m: float = 0.05


@dataclass
class RepairProcedure:
    fault_id: str
    target_part_id: str
    replacement_part_id: str
    target_step_id: Optional[str]
    steps: list[RepairStep] = field(default_factory=list)

    def actions(self) -> list[str]:
        return [s.action for s in self.steps]


class RepairSynthesisError(ValueError):
    pass


def _topo_order(genome: Genome) -> list[AssemblyStep]:
    """Kahn topological sort of assembly steps by predecessors."""
    steps = {s.step_id: s for s in genome.assembly}
    indeg = {sid: 0 for sid in steps}
    children: dict[str, list[str]] = {sid: [] for sid in steps}
    for s in genome.assembly:
        for pre in s.predecessors:
            if pre in steps:
                indeg[s.step_id] += 1
                children[pre].append(s.step_id)
    queue = sorted([sid for sid, d in indeg.items() if d == 0])
    order: list[str] = []
    while queue:
        sid = queue.pop(0)
        order.append(sid)
        for c in sorted(children[sid]):
            indeg[c] -= 1
            if indeg[c] == 0:
                queue.append(c)
        queue.sort()
    if len(order) != len(steps):
        raise RepairSynthesisError("assembly graph contains a cycle")
    return [steps[sid] for sid in order]


def _dependents(genome: Genome, target_step_id: str) -> set[str]:
    """All steps that (transitively) depend on the target step — i.e. parts
    built on top of the target and thus blocking access to it."""
    children: dict[str, list[str]] = {}
    for s in genome.assembly:
        for pre in s.predecessors:
            children.setdefault(pre, []).append(s.step_id)
    out: set[str] = set()
    stack = list(children.get(target_step_id, []))
    while stack:
        sid = stack.pop()
        if sid in out:
            continue
        out.add(sid)
        stack.extend(children.get(sid, []))
    return out


def plan_repair_procedure(genome: Genome, fault: Fault) -> RepairProcedure:
    """Synthesise (but do not certify) a repair procedure for ``fault``."""
    target_step = genome.step_for_part(fault.part_id)
    if target_step is None:
        raise RepairSynthesisError(
            f"no assembly step for faulty part {fault.part_id}; "
            "cannot sequence repair"
        )

    topo = _topo_order(genome)
    pos = {s.step_id: i for i, s in enumerate(topo)}
    blockers = _dependents(genome, target_step.step_id)
    # Disassemble blockers in reverse assembly order (last built, first removed).
    disasm = sorted(blockers, key=lambda sid: pos[sid], reverse=True)
    reasm = sorted(blockers, key=lambda sid: pos[sid])           # forward order
    by_step = {s.step_id: s for s in genome.assembly}

    tol = genome.tolerance(fault.repair_part_id) or genome.tolerance(fault.part_id)
    install_torque = tol.torque_spec if tol else target_step.torque

    steps: list[RepairStep] = []
    order = 0

    for sid in disasm:
        s = by_step[sid]
        steps.append(RepairStep(order, "disassemble", s.part_id, sid, s.mating,
                                list(s.tooling), s.torque, s.access_clearance_mm,
                                s.lever_arm_m))
        order += 1

    steps.append(RepairStep(order, "remove", fault.part_id, target_step.step_id,
                            target_step.mating, list(target_step.tooling),
                            target_step.torque, target_step.access_clearance_mm,
                            target_step.lever_arm_m))
    order += 1

    steps.append(RepairStep(order, "install", fault.repair_part_id,
                            target_step.step_id, target_step.mating,
                            list(target_step.tooling), install_torque,
                            target_step.access_clearance_mm,
                            target_step.lever_arm_m))
    order += 1

    for sid in reasm:
        s = by_step[sid]
        steps.append(RepairStep(order, "reassemble", s.part_id, sid, s.mating,
                                list(s.tooling), s.torque, s.access_clearance_mm,
                                s.lever_arm_m))
        order += 1

    # Recalibrate the joints whose child link corresponds to the swapped part.
    steps.append(RepairStep(order, "calibrate", fault.repair_part_id,
                            target_step.step_id))

    return RepairProcedure(
        fault_id=fault.id,
        target_part_id=fault.part_id,
        replacement_part_id=fault.repair_part_id,
        target_step_id=target_step.step_id,
        steps=steps,
    )
