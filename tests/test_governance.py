"""L6 — append-only hash-chained provenance ledger."""

from autogenesis.governance import GENESIS_HASH, Ledger


def test_append_chains_entries():
    led = Ledger()
    e0 = led.append("ingest", {"robot_id": "rrbot"})
    e1 = led.append("diagnose", {"faults": 1})
    assert e0.prev_hash == GENESIS_HASH
    assert e1.prev_hash == e0.entry_hash
    assert led.head == e1.entry_hash


def test_verify_chain_intact():
    led = Ledger()
    for i in range(5):
        led.append("event", {"i": i})
    ok, broken = led.verify_chain()
    assert ok and broken is None


def test_verify_chain_detects_tampering():
    led = Ledger()
    for i in range(5):
        led.append("event", {"i": i})
    # Mutate a past entry's payload without re-chaining.
    led.entries[2].payload["i"] = 999
    ok, broken = led.verify_chain()
    assert not ok
    assert broken == 2
