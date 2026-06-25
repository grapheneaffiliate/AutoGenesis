"""Reference genome: 'rrbot', a 2-DOF revolute arm.

Small but complete enough to exercise the whole spine end-to-end: kinematics,
a hierarchical BOM, tolerances with torque specs, an FMEA entry with a
detection signal, an authored assembly graph, a telemetry schema and a safety
envelope. Used by the tests and as the worked example in the README.
"""

from __future__ import annotations

RRBOT_BUNDLE = {
    "robot_id": "rrbot",
    "version": "1.0.0",
    "links": [
        {"name": "base_link", "mass": 2.0},
        {"name": "link1", "mass": 1.0},
        {"name": "link2", "mass": 0.8},
    ],
    "joints": [
        {"name": "joint1", "type": "revolute", "parent": "base_link",
         "child": "link1", "lower": -3.14, "upper": 3.14,
         "effort": 30.0, "velocity": 2.0},
        {"name": "joint2", "type": "revolute", "parent": "link1",
         "child": "link2", "lower": -2.6, "upper": 2.6,
         "effort": 20.0, "velocity": 2.0},
    ],
    "parts": [
        {"id": "chassis", "name": "Base chassis", "make_or_buy": "make"},
        {"id": "shoulder_servo", "name": "Shoulder servo", "parent_id": "chassis",
         "make_or_buy": "buy", "sourcing": "ServoCo X1"},
        {"id": "upper_arm", "name": "Upper arm", "parent_id": "shoulder_servo",
         "make_or_buy": "make"},
        {"id": "elbow_servo", "name": "Elbow servo", "parent_id": "upper_arm",
         "make_or_buy": "buy", "sourcing": "ServoCo X1"},
        {"id": "forearm", "name": "Forearm", "parent_id": "elbow_servo",
         "make_or_buy": "make"},
        {"id": "elbow_servo_spare", "name": "Elbow servo (replacement)",
         "make_or_buy": "buy", "sourcing": "ServoCo X1"},
    ],
    "tolerances": [
        {"part_id": "elbow_servo", "dimension": "shaft_fit", "nominal": 6.0,
         "plus": 0.02, "minus": 0.0, "material": "steel",
         "torque_spec": 2.5, "torque_tol": 0.10},
        {"part_id": "elbow_servo_spare", "dimension": "shaft_fit", "nominal": 6.0,
         "plus": 0.02, "minus": 0.0, "material": "steel",
         "torque_spec": 2.5, "torque_tol": 0.10},
    ],
    "failure_modes": [
        {"id": "fm_elbow_overheat", "part_id": "elbow_servo",
         "mode": "thermal overload",
         "symptoms": ["position drift", "torque loss"],
         "detection_signal": "elbow_temp", "threshold": 75.0, "comparator": ">",
         "severity": 8, "repair_part_id": "elbow_servo_spare"},
    ],
    "assembly": [
        {"step_id": "s0", "part_id": "chassis", "predecessors": [],
         "mating": "weld", "access_clearance_mm": 50.0, "tooling": ["jig"]},
        {"step_id": "s1", "part_id": "shoulder_servo", "predecessors": ["s0"],
         "mating": "fastener", "access_clearance_mm": 25.0,
         "tooling": ["hex_4mm"], "torque": 3.0},
        {"step_id": "s2", "part_id": "upper_arm", "predecessors": ["s1"],
         "mating": "fastener", "access_clearance_mm": 20.0,
         "tooling": ["hex_4mm"], "torque": 2.0},
        {"step_id": "s3", "part_id": "elbow_servo", "predecessors": ["s2"],
         "mating": "fastener", "access_clearance_mm": 18.0,
         "tooling": ["hex_3mm"], "torque": 2.5},
        {"step_id": "s4", "part_id": "forearm", "predecessors": ["s3"],
         "mating": "fastener", "access_clearance_mm": 15.0,
         "tooling": ["hex_3mm"], "torque": 1.5},
    ],
    "telemetry": [
        {"name": "elbow_temp", "semantics": "elbow servo case temperature",
         "nominal_min": 20.0, "nominal_max": 70.0, "unit": "C"},
        {"name": "elbow_current", "semantics": "elbow servo current draw",
         "nominal_min": 0.0, "nominal_max": 4.0, "unit": "A"},
    ],
    "safety": {
        "max_force_N": 150.0,
        "max_speed_mps": 2.0,
        "max_power_W": 500.0,
        "iso_zone": "collaborative",
        "estop_behavior": "category_1",
    },
}

# A minimal URDF for the adapter test.
RRBOT_URDF = """<?xml version="1.0"?>
<robot name="rrbot">
  <link name="base_link"><inertial><mass value="2.0"/></inertial></link>
  <link name="link1"><inertial><mass value="1.0"/></inertial></link>
  <link name="link2"><inertial><mass value="0.8"/></inertial></link>
  <joint name="joint1" type="revolute">
    <parent link="base_link"/><child link="link1"/>
    <limit lower="-3.14" upper="3.14" effort="30.0" velocity="2.0"/>
  </joint>
  <joint name="joint2" type="revolute">
    <parent link="link1"/><child link="link2"/>
    <limit lower="-2.6" upper="2.6" effort="20.0" velocity="2.0"/>
  </joint>
</robot>
"""
