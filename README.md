# AUTOGENESIS

**A platform-agnostic, proof-carrying substrate for verified robot maintenance & replication.**

A robot company hands AUTOGENESIS a *genome* (the complete machine-readable
engineering description of a robot); the substrate returns **verified**
maintenance capability — diagnoses, repair procedures, and the certificates
that prove each procedure satisfies the genome's engineering and safety
constraints *before* it reaches an executor.

The framework is morphology-agnostic, manufacturer-agnostic, format-agnostic,
and execution-backend-agnostic (human technicians today, robot policies as they
mature). The single most valuable component is the **verification layer** (L3):
nothing without a passing, tamper-evident certificate can propagate to the
fleet. That is what bounds von Neumann error-accumulation and makes
self-expansion safe.

This repository is **Phase 1**: the information spine, built and green.

---

## The seven layers (Phase 1 builds L0–L3 + L6)

```
L6 GOVERNANCE   — append-only hash-chained provenance ledger          ✅ governance/
L3 VERIFICATION — spec · feasibility · formal · safety · certificate  ✅ verify/   ◄ the moat
L2 SYNTHESIS    — diagnosis · repair-by-assembly/disassembly          ✅ synthesis/
L1 FEASIBILITY  — analytic oracle with numeric witnesses (sim seam)   ✅ twin/
L0 GENOME       — adapters · extraction · canonical schema · gate     ✅ genome/
L4 EXECUTION    — pluggable backend (human first)                     ◻ Phase 2
L5 SUPPLY       — make-or-buy · closure ratio                         ◻ Phase 2
```

## The Capability API (§3 of the spec)

```python
from autogenesis import Capability
from examples.rrbot import RRBOT_BUNDLE

cap = Capability()

# L0 — validate, extract, content-address, record on the ledger
genome = cap.ingest("rrbot", RRBOT_BUNDLE)

# L2 — rank faults from a telemetry window against the genome's FMEA
faults = cap.diagnose(genome, {"elbow_temp": [60, 78, 90]})

# L2 synthesis + L3 gate — returns a procedure inseparable from its certificate
repair = cap.plan_repair(genome, faults[0])
assert repair.certificate.passed          # spec + feasibility + formal + safety

# L4 seam — the executor independently re-verifies (tamper-evident) before acting
assert cap.admit_to_executor(genome, repair, faults[0])
```

`ingest` also accepts a URDF/XML string; missing modules degrade gracefully
(e.g. the assembly graph is inferred from the BOM hierarchy).

## The certificate — proof-carrying maintenance (§6)

Every `plan_repair` result carries a `Certificate` composing four checks:

1. **Spec conformance** — installed part is the FMEA-declared replacement;
   applied torques lie inside the tolerance band. *Discharged to Z3.*
2. **Physical feasibility** — the L1 oracle returns numeric witnesses
   (clearance, force, speed, power) within limits at every step.
3. **Formal correctness** — structural invariants of the procedure:
   *conservation* (every disassembled part is reassembled) and *ordering*
   (a valid inverse-then-forward LIFO traversal). *Discharged to Z3.*
4. **Safety-envelope gate** — a hard ISO 10218 / TS 15066 check on
   force/speed/power. A breach is a hard stop, not a warning.

The certificate pins a content hash of the exact procedure, so mutating the
procedure after issuance is detected by `verify_against` — an uncertified or
tampered artifact can never be admitted to an executor.

## Run it

```bash
pip install -r requirements.txt
python -m pytest          # 37 tests, end-to-end
```

Z3 discharges the spec and formal proofs when installed; a faithful native
re-check keeps the suite hermetic otherwise (the `engine` field on each check
records which produced the verdict).

## Layout

```
autogenesis/
  genome/      L0 — schema, adapters (dict/URDF), extraction, validation, content-addressing
  twin/        L1 — analytic feasibility oracle (the simulation seam)
  synthesis/   L2 — diagnosis, repair-by-assembly/disassembly
  verify/      L3 — spec (z3), feasibility, formal (z3), safety, certificate
  governance/  L6 — hash-chained provenance ledger
  api.py       Capability: ingest / diagnose / plan_repair / admit_to_executor
examples/      rrbot — a 2-DOF reference genome (bundle + URDF)
tests/         37 tests across all layers
```

See **VISION.md** for the definition-of-done and the autonomy envelope, and
**LOOP_STATE.md** for current build state.
