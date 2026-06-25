"""L0 — Extraction pipeline.

Adapters give a partial genome; extraction fills inferable gaps so the
substrate degrades gracefully. The headline inference is the **assembly
graph**: when an OEM ships no precedence data we synthesise a plausible linear
assembly order from the BOM hierarchy (parents before children), which is
enough for repair sequencing to function. Inferred artifacts are marked so the
ledger and reviewers can tell synthesised data from authored data.
"""

from __future__ import annotations

from .schema import AssemblyStep, Genome


def infer_assembly(genome: Genome) -> list[AssemblyStep]:
    """Synthesise a linear assembly order from BOM hierarchy.

    Parents are assembled before their children (you cannot mount a sub-part
    before the part it attaches to). Within a tier, order is BOM order. Each
    inferred step depends on the immediately preceding inferred step.
    """
    # Topologically order parts: parents before children.
    by_id = {p.id: p for p in genome.parts}
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(pid: str, stack: frozenset[str]) -> None:
        if pid in seen or pid not in by_id:
            return
        parent = by_id[pid].parent_id
        if parent and parent not in stack:   # guard against cycles
            visit(parent, stack | {pid})
        if pid not in seen:
            seen.add(pid)
            ordered.append(pid)

    for p in genome.parts:
        visit(p.id, frozenset())

    steps: list[AssemblyStep] = []
    prev: str | None = None
    for i, pid in enumerate(ordered):
        step_id = f"asm_{i:03d}"
        steps.append(
            AssemblyStep(
                step_id=step_id,
                part_id=pid,
                predecessors=[prev] if prev else [],
                mating="inferred",
            )
        )
        prev = step_id
    return steps


def extract(genome: Genome) -> Genome:
    """Fill inferable gaps in-place; return the same genome."""
    if not genome.assembly and genome.parts:
        genome.assembly = infer_assembly(genome)
    return genome
