"""L0 — Ingestion adapters.

No OEM ships data in the canonical schema, so the substrate must *build* a
compliant genome from messy real-world inputs. Each adapter maps one external
format onto the canonical schema; they are intentionally small and additive so
new formats (USD, MJCF, SDF, spreadsheet BOMs) drop in behind the same seam.

Implemented here:
  * ``from_dict``  — a structured bundle (the canonical interchange form)
  * ``from_urdf``  — kinematics & geometry from a URDF/XML string
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .schema import (
    AssemblyStep,
    FailureMode,
    Genome,
    Joint,
    Link,
    MaintenanceTask,
    Part,
    SafetyEnvelope,
    Signal,
    Tolerance,
)


def _build(cls, items):
    return [cls(**it) if isinstance(it, dict) else it for it in (items or [])]


def from_dict(data: dict[str, Any]) -> Genome:
    """Build a genome from a structured bundle (lists of plain dicts)."""
    safety_data = data.get("safety")
    safety = (
        SafetyEnvelope(**safety_data)
        if isinstance(safety_data, dict)
        else (safety_data or SafetyEnvelope())
    )
    return Genome(
        robot_id=data["robot_id"],
        version=data.get("version", "0.0.0"),
        links=_build(Link, data.get("links")),
        joints=_build(Joint, data.get("joints")),
        parts=_build(Part, data.get("parts")),
        tolerances=_build(Tolerance, data.get("tolerances")),
        failure_modes=_build(FailureMode, data.get("failure_modes")),
        assembly=_build(AssemblyStep, data.get("assembly")),
        maintenance=_build(MaintenanceTask, data.get("maintenance")),
        telemetry=_build(Signal, data.get("telemetry")),
        safety=safety,
    )


def from_urdf(urdf_xml: str, robot_id: str | None = None) -> Genome:
    """Extract links and joints from a URDF document.

    Only kinematics & geometry are carried; the remaining modules are left
    empty for richer adapters / extraction to fill. Joint limits map directly
    onto the canonical schema.
    """
    root = ET.fromstring(urdf_xml)
    rid = robot_id or root.get("name") or "urdf_robot"

    links: list[Link] = []
    for link_el in root.findall("link"):
        name = link_el.get("name", "")
        mass = 0.0
        inertial = link_el.find("inertial")
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass = float(mass_el.get("value", "0") or 0)
        links.append(Link(name=name, mass=mass))

    joints: list[Joint] = []
    for joint_el in root.findall("joint"):
        name = joint_el.get("name", "")
        jtype = joint_el.get("type", "fixed")
        parent = joint_el.find("parent")
        child = joint_el.find("child")
        limit = joint_el.find("limit")
        lower = upper = effort = velocity = 0.0
        if limit is not None:
            lower = float(limit.get("lower", "0") or 0)
            upper = float(limit.get("upper", "0") or 0)
            effort = float(limit.get("effort", "0") or 0)
            velocity = float(limit.get("velocity", "0") or 0)
        joints.append(
            Joint(
                name=name,
                type=jtype,
                parent=parent.get("link", "") if parent is not None else "",
                child=child.get("link", "") if child is not None else "",
                lower=lower,
                upper=upper,
                effort=effort,
                velocity=velocity,
            )
        )

    # Each link becomes a buyable part by default; richer BOM data merges later.
    parts = [Part(id=f"part_{l.name}", name=l.name) for l in links]
    return Genome(robot_id=rid, links=links, joints=joints, parts=parts)
