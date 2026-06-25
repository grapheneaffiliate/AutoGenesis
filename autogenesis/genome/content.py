"""L0 — Content addressing.

A genome is identified by the SHA-256 of its canonical JSON encoding. The hash
deliberately excludes the ``content_hash`` field itself so that addressing is a
pure function of the engineering content. Two genomes with identical content
get identical ids; any edit changes the id. This is what makes the genome
*versioned and content-addressed* (§3) and lets the L6 ledger pin exactly which
description a certificate was issued against.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .schema import Genome


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(genome: Genome) -> str:
    payload = genome.to_dict()
    payload.pop("content_hash", None)
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def address(genome: Genome) -> Genome:
    """Stamp the genome with its content hash, returning the same instance."""
    genome.content_hash = content_hash(genome)
    return genome
