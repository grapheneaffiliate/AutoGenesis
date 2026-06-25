"""L0 — genome schema, addressing, validation, adapters, extraction."""

import copy

import pytest

from autogenesis.genome import (
    address,
    content_hash,
    extract,
    from_dict,
    from_urdf,
    validate,
)
from examples.rrbot import RRBOT_BUNDLE, RRBOT_URDF


def test_from_dict_roundtrip():
    g = from_dict(RRBOT_BUNDLE)
    assert g.robot_id == "rrbot"
    assert len(g.links) == 3
    assert len(g.joints) == 2
    assert g.part("elbow_servo").sourcing == "ServoCo X1"


def test_content_hash_is_deterministic():
    g1 = from_dict(RRBOT_BUNDLE)
    g2 = from_dict(RRBOT_BUNDLE)
    assert content_hash(g1) == content_hash(g2)
    assert content_hash(g1).startswith("sha256:")


def test_content_hash_changes_on_edit():
    g1 = from_dict(RRBOT_BUNDLE)
    bundle2 = copy.deepcopy(RRBOT_BUNDLE)
    bundle2["version"] = "1.0.1"
    g2 = from_dict(bundle2)
    assert content_hash(g1) != content_hash(g2)


def test_address_stamps_hash():
    g = address(from_dict(RRBOT_BUNDLE))
    assert g.content_hash == content_hash(g)


def test_validation_passes_for_reference_genome():
    report = validate(from_dict(RRBOT_BUNDLE))
    assert report.ok
    assert report.errors == []


def test_validation_rejects_missing_required_module():
    bundle = copy.deepcopy(RRBOT_BUNDLE)
    bundle["parts"] = []
    report = validate(from_dict(bundle))
    assert not report.ok
    assert any("bom" in e for e in report.errors)


def test_validation_rejects_bad_referential_integrity():
    bundle = copy.deepcopy(RRBOT_BUNDLE)
    bundle["failure_modes"][0]["part_id"] = "ghost_part"
    report = validate(from_dict(bundle))
    assert not report.ok
    assert any("ghost_part" in e for e in report.errors)


def test_validation_rejects_nonpositive_safety_limit():
    bundle = copy.deepcopy(RRBOT_BUNDLE)
    bundle["safety"]["max_force_N"] = 0
    report = validate(from_dict(bundle))
    assert not report.ok


def test_urdf_adapter_extracts_kinematics():
    g = from_urdf(RRBOT_URDF)
    assert g.robot_id == "rrbot"
    assert {l.name for l in g.links} == {"base_link", "link1", "link2"}
    j1 = next(j for j in g.joints if j.name == "joint1")
    assert j1.type == "revolute"
    assert j1.upper == pytest.approx(3.14)


def test_extraction_infers_assembly_graph():
    bundle = copy.deepcopy(RRBOT_BUNDLE)
    bundle["assembly"] = []
    g = extract(from_dict(bundle))
    assert g.assembly                       # an assembly graph was synthesised
    # Parents are sequenced before children.
    pos = {s.part_id: i for i, s in enumerate(g.assembly)}
    assert pos["chassis"] < pos["shoulder_servo"] < pos["upper_arm"]
