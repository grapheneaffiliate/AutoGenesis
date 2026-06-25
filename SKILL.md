# SKILL — AUTOGENESIS project conventions

> Read this each autonomy cycle instead of re-deriving the rules (§10c).

## What this is

A proof-carrying substrate for verified robot maintenance. A genome (robot
description) goes in; verified diagnoses and repair procedures come out, each
inseparable from a machine-checkable certificate. The verification layer (L3) is
the product — protect it.

## The one rule that overrides others — the agnostic contract

- Robot-specific facts live **only** in the genome (`autogenesis/genome/schema.py`).
- The substrate (L1–L6) is reusable across morphologies and manufacturers. Never
  hard-code a robot, part name, or morphology assumption above L0. If you need
  per-robot behaviour, add a genome field, not a branch in the substrate.

## The certificate contract — what "certified" means

A `Certificate` passes iff **all four** checks pass:
`spec` (Z3) ∧ `feasibility` (L1 witnesses) ∧ `formal` (Z3) ∧ `safety` (hard gate).
It pins `artifact_hash` (the procedure) and `genome_hash`. `verify_against`
re-runs the checks and re-matches the hash, so tampering is detected. An executor
acts only on `admit_to_executor`, which calls `verify_against`.

## Conventions

- Python 3.10+, std-lib + `z3-solver` only. Dataclasses for all schema/result
  types; everything JSON-serialisable for hashing and the ledger.
- Each layer is a package with a thin `__init__` re-export and a one-paragraph
  module docstring stating its responsibility and its typed seam to neighbours.
- Discharge logical obligations to Z3 via `verify/_smt.prove_unsat` (assert the
  negation, prove UNSAT). Keep a native re-check so CI is hermetic; record the
  `engine`. The two paths must agree — disagreement is a hard fail, never a pass.
- Tests live in `tests/`, one file per layer. A new check counts only once it is
  proven able to **fail** on a known-bad input (§12).

## Never do

- Never let an uncertified or hash-mismatched artifact reach an executor.
- Never weaken a check to make a test pass. Fix the artifact, not the gate.
- Never self-merge changes to the **ratify list** (§9): `autogenesis/verify/**`,
  `autogenesis/genome/schema.py`, `autogenesis/genome/validation.py` (safety
  logic), the certificate semantics, or any safety limit. Escalate instead.
- Never restart from zero — resume from `LOOP_STATE.md` and the ledger.
- A `STOP` file at repo root halts the loop at the next cycle boundary.

## Commands

```bash
pip install -r requirements.txt
python -m pytest          # full suite, must be green before any commit
```
