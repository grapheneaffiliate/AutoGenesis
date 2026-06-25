# VISION — where AUTOGENESIS is going

> Reread every autonomy cycle to kill goal drift (§11). The §9 envelope below is
> load-bearing: it is what lets a human walk away from everything inside it.

## Thesis (§1)

Once a robot's complete engineering description (the **genome**) exists in a
canonical, queryable, verifiable form, one substrate can read it and generate
every downstream maintenance and replication artifact — for any robot,
regardless of morphology or manufacturer. The moat is the **verification layer**:
every generated artifact provably satisfies the genome's constraints *before* it
propagates to the fleet. Without that spine, a self-expanding fleet is a
cascade-failure machine.

## The agnostic contract (§3) — DO NOT erode

- Everything robot-specific lives in the **genome**. Everything reusable lives in
  the **substrate** (L0–L6). No robot-specific logic leaks above L0.
- `ingest → diagnose → plan_repair` (Phase 1). Anything returned as *Verified*
  carries a machine-checkable, tamper-evident certificate. Nothing without a
  passing certificate reaches an executor.

## Definition of done — Phase 1 (this milestone: M-spine) ✅

- [x] L0 Genome: canonical schema, dict + URDF adapters, extraction (assembly
      inference), validation gate, content-addressing.
- [x] L1 Feasibility: analytic oracle returning numeric witnesses behind an
      `assess` seam a real simulator can replace.
- [x] L2 Synthesis: FMEA-driven diagnosis (ranked); repair by
      assembly-by-disassembly.
- [x] L3 Verification: four checks (spec/feasibility/formal/safety) composed
      into one certificate; spec + formal discharged to Z3; tamper-evident.
- [x] L6 Governance: append-only hash-chained provenance ledger.
- [x] Capability API wiring all of the above; 37 tests green end-to-end.

## The autonomy envelope (§9) — what the loop owns vs. ratifies

**The loop owns, fully autonomously:** implementing code to pass acceptance
tests; fixing failing tests/builds/types; expanding fault-class coverage once
the certificate format is fixed; writing tests per new module/fault; refactors,
lint/type/format; the diff digest and state updates.

**The loop drafts; a human ratifies before it becomes load-bearing (L6 gate):**
- the **canonical genome schema shape** (defines the agnostic contract);
- the **certificate semantics** — what each check proves and its scope (defines
  what "certified" *means*);
- the **safety-envelope logic** and any safety limits;
- anything irreversible: merge to main, gate-touching dependency changes,
  fixture deletions.

> A loop that autonomously redefines what "certified" means is grading its own
> homework at the highest level — the exact failure this system exists to
> prevent. `autogenesis/verify/` and `autogenesis/genome/schema.py` +
> `validation.py` (safety logic) are **ratify-list**: changes there escalate,
> they do not self-merge.

## Non-negotiables

- The objective gate returns a **number, not a vibe** (§12). Soft completion is
  forbidden as a stop condition. A new check must be proven able to **fail** on a
  known-bad input before it counts.
- Maker ≠ checker: the verifier that runs the gate is independent of whoever
  wrote the code (§10e).
- A `STOP` file at repo root aborts the loop at the next cycle boundary (§15).

## Forward path (Phase 2, not in this repo yet)

L4 execution backends (human → robot policy), L5 supply & **closure ratio**
(the north-star metric C, §7), `plan_part` / `plan_build` / `closure_report`,
and the L6 replication rate-limit + approval gate for replication events.
