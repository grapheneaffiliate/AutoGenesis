"""L6 — Governance: append-only, hash-chained provenance ledger.

The engineered answer to von Neumann error-accumulation and runaway
replication. Every load-bearing event (ingest, diagnose, certify, execute) is
appended as an entry whose hash chains to its predecessor, so the full
provenance is tamper-evident: altering any past entry breaks the chain and
``verify_chain`` reports the first broken index.

This is the tamper-evident truth; ``LOOP_STATE.md`` is the human-readable view
of the same history (§11).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

GENESIS_HASH = "sha256:" + "0" * 64


def _hash_entry(index: int, prev_hash: str, event: str,
                payload: dict, timestamp: str) -> str:
    body = json.dumps(
        {"index": index, "prev_hash": prev_hash, "event": event,
         "payload": payload, "timestamp": timestamp},
        sort_keys=True, separators=(",", ":"), default=str,
    )
    return "sha256:" + hashlib.sha256(body.encode()).hexdigest()


@dataclass
class LedgerEntry:
    index: int
    prev_hash: str
    event: str
    payload: dict
    timestamp: str
    entry_hash: str = ""

    def recompute(self) -> str:
        return _hash_entry(self.index, self.prev_hash, self.event,
                           self.payload, self.timestamp)


@dataclass
class Ledger:
    entries: list[LedgerEntry] = field(default_factory=list)

    @property
    def head(self) -> str:
        return self.entries[-1].entry_hash if self.entries else GENESIS_HASH

    def append(self, event: str, payload: dict,
               timestamp: Optional[str] = None) -> LedgerEntry:
        index = len(self.entries)
        prev = self.head
        ts = timestamp or f"seq:{index}"   # deterministic default; pass real time in prod
        entry = LedgerEntry(index=index, prev_hash=prev, event=event,
                            payload=payload, timestamp=ts)
        entry.entry_hash = entry.recompute()
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> tuple[bool, Optional[int]]:
        """Return (ok, first_broken_index). ok=True iff the whole chain is intact."""
        prev = GENESIS_HASH
        for e in self.entries:
            if e.prev_hash != prev:
                return False, e.index
            if e.recompute() != e.entry_hash:
                return False, e.index
            prev = e.entry_hash
        return True, None

    def to_dict(self) -> dict[str, Any]:
        return {"entries": [asdict(e) for e in self.entries], "head": self.head}
