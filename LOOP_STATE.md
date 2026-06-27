# LOOP_STATE — where the build is now

> Human-readable view of the build history; the L6 ledger is the tamper-evident
> truth (§11). On restart, resume from here — never restart from zero.

## Current milestone

**M-spine (Phase 1 information spine)** — ✅ complete and green.

## Last run (perfection-harness cycle)

- **Gate: `python -m pytest` → 51 passed, exit 0, `-W error` clean (zero
  warnings, zero skips).** Verified twice: with Z3 active *and* with Z3 forced
  unavailable — both engine paths produce identical verdicts across the whole
  suite (no z3/native disagreement recorded anywhere).
- **Closed a real §12 coverage gap.** The rrbot FMEA fault (elbow_servo) has a
  single access blocker (forearm), so the *multi-element* LIFO reverse-pairing,
  the phase-ordering, the multi-blocker conservation, and the inclusive
  tolerance-band boundary clauses of the L3 proofs were never exercised by a
  known-bad input. Added `tests/test_formal_lifo.py` (10 tests) driving a deeper
  fault (shoulder_servo → forearm→elbow_servo→upper_arm) and the exact band edges.
- **Strengthened the Z3 ordering proof (human-ratified, §9).** Previously
  contiguity and the LIFO pairing were computed in Python and handed to Z3 as a
  `BoolVal` constant — so the solver ratified a precomputed boolean rather than
  reasoning. Rewrote `verify/formal.py` to discharge INV-ORDERING over **free**
  symbolic `Int` position variables: `Distinct`+range (contiguity), the LIFO
  mirror as a biconditional over all access pairs, and the assembly-hierarchy
  precedence edges (from the genome) as solver constraints — plus a SAT proof
  that the hierarchy admits a valid traversal. Torque band now proved over a free
  `Real`. `check_formal(procedure, genome=None)` is backward-compatible;
  `certificate.py` passes the genome for the hierarchy-aware proof.
- Added `tests/test_formal_symbolic.py` (4 tests) proving the strengthening earns
  its keep: a mirror-consistent but **hierarchy-violating** order is rejected
  *with* the genome but not by the genome-less check, and the consistency
  obligation is recorded for valid procedures.
- **README honesty corrections applied** (see below).

## Completed increments

| Layer | Module | Status |
|---|---|---|
| L0 | `genome/{schema,content,validation,adapters,extraction}` | ✅ |
| L1 | `twin/feasibility` (analytic oracle, numeric witnesses) | ✅ |
| L2 | `synthesis/{diagnosis,repair}` | ✅ |
| L3 | `verify/{spec,formal,safety,certificate,_smt}` | ✅ |
| L6 | `governance/ledger` | ✅ |
| API | `api.Capability` | ✅ |
| L3+ | `verify/formal.py` — symbolic ordering proof (hierarchy-aware, §9) | ✅ |
| Test | `tests/test_formal_lifo.py` — deep-fault LIFO/band coverage (§12) | ✅ |
| Test | `tests/test_formal_symbolic.py` — hierarchy-precedence proof value | ✅ |

## Objective gate status (§12)

- [x] Acceptance tests pass and are proven able to fail — multi-blocker
      ordering/conservation, inclusive torque-band edges, and a mirror-consistent
      hierarchy violation caught only by the genome-aware proof.
- [x] Build imports clean; suite green (**51 tests**), `-W error` clean.
- [x] System artifact (the repair certificate) verifies, and a deliberately
      tampered procedure **fails** `verify_against`.
- [x] Z3 discharges the spec (tolerance band) and formal (ordering) obligations
      with `unsat` proofs — no timeouts, no `unknown` verdicts (B2/B3).

## In-progress branches

- `claude/autogenesis-platform-1jjeua` — this build.

## Ratified & applied this cycle (§9)

- **Z3 encoding depth of the formal `ordering` proof** — human-ratified ("you
  decide for perfection and proceed") and applied to `verify/formal.py` on the
  dev branch. The old code handed contiguity + LIFO to Z3 as a `BoolVal`
  constant; the solver now reasons over free symbolic position variables
  (`Distinct`/range, LIFO mirror biconditional, hierarchy precedence edges) and
  proves the structural spec is satisfiable. Behaviour-preserving on all prior
  cases; strictly stronger (catches mirror-consistent hierarchy violations).
  **Still NOT merged to main** — merge-to-main remains the §9 irreversible gate.
- **README honesty corrections** — applied: scoped the von Neumann claim to the
  specific checked error class; named the three escapees (analytic-model error;
  spec-conformant-but-defective part; **misdiagnosis** — the cert proves the
  repair for the *chosen* fault, not that `diagnose()` chose right); reframed
  replication as "designed to extend to" (L4/L5 are Phase 2). New
  **Scope & honest limits** section in README.

## Still escalated to human (ratify list, §9)

- Initial **genome schema shape**, **certificate semantics**, and
  **safety-envelope logic** should get a human review before being frozen as
  contract, and any **merge to main** is the irreversible §9 gate.

## Open bugs / unverified invariants

- **None.** Both Phase-1 formal invariants (conservation, ordering/LIFO over the
  hierarchy) and the spec obligations (correct-replacement, torque band incl.
  boundaries) are verified, discharged to Z3 with genuine solver reasoning, and
  proven able to fail on known-bad inputs (incl. a hierarchy-precedence
  violation that only the genome-aware proof catches).

## Lessons learned

- A passing verdict is not the same as a verified invariant: a check whose
  branch is never hit by a known-bad input is *unproven*. Coverage that drives
  the multi-element path is what turns "green" into "proven able to fail" (§12).
- Strengthening proof *depth* in `verify/` is a certificate-semantics change and
  thus §9 ratify-list, even when it is strictly an improvement — the loop drafts
  and escalates it; it does not self-merge.
- Discharging the torque-band and ordering invariants to Z3 keeps real proofs;
  keeping a native re-check (and hard-failing on disagreement) keeps CI hermetic
  without weakening what a passing certificate means.

## Stop conditions / next increments (not yet started)

- Candidate increments inside the autonomous envelope: more FMEA fault classes +
  per-fault tests; branched (non-chain) access graphs; a USD/MJCF adapter; a CLI.
- Ratify-gated: the Z3 encoding-depth enhancement above; Phase 2 (L4/L5, closure).
