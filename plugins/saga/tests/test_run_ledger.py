import concurrent.futures
import json

import pytest

from plugins.saga.scripts.run_ledger import (
    RunLedger,
    RunLedgerError,
    append_fact,
    build_fact,
    last_n_prior,
    read_facts,
    reuse_ratio,
    rollup,
    verify_chain,
)


def test_build_fact_validates_schema():
    with pytest.raises(RunLedgerError, match="unknown run-fact kind"):
        build_fact("nonsense", subplot_id="a", at="2026")
    with pytest.raises(RunLedgerError, match="needs a non-empty subplot_id"):
        build_fact("spend", subplot_id="", at="2026")
    with pytest.raises(RunLedgerError, match="reserved chain field"):
        build_fact("spend", subplot_id="a", at="2026", this_hash="123")

    fact = build_fact(
        "spend", subplot_id="123", at="2026-07-09T00:00:00Z", tokens_cached=10, cost=1.5
    )
    assert fact["kind"] == "spend"
    assert fact["tokens_cached"] == 10
    assert fact["cost"] == 1.5


def test_append_read_round_trip(tmp_path):
    ledger = RunLedger(tmp_path / "run-facts.jsonl")
    f1 = build_fact("spend", subplot_id="s1", at="t1", cost=1.0)
    f2 = build_fact("cache", subplot_id="s2", at="t2", hits=5)

    append_fact(ledger, f1)
    append_fact(ledger, f2)

    records = read_facts(ledger)
    assert len(records) == 2
    assert records[0]["subplot_id"] == "s1"
    assert records[0]["prev_hash"] == ""
    assert records[1]["subplot_id"] == "s2"
    assert records[1]["prev_hash"] == records[0]["this_hash"]


def test_chain_verification_and_mutation(tmp_path):
    ledger = RunLedger(tmp_path / "run-facts.jsonl")
    append_fact(ledger, build_fact("spend", subplot_id="s1", at="t1", cost=1))
    append_fact(ledger, build_fact("spend", subplot_id="s2", at="t2", cost=2))

    report = verify_chain(ledger)
    assert report.ok

    # Mutate record 0 in place
    records = read_facts(ledger)
    records[0]["cost"] = 999
    # rewrite without updating this_hash
    with open(ledger.path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    report2 = verify_chain(ledger)
    assert not report2.ok
    assert "mutated in place" in report2.reason
    assert report2.break_index == 0


def test_torn_trailing_line_tolerance(tmp_path):
    ledger = RunLedger(tmp_path / "run-facts.jsonl")
    append_fact(ledger, build_fact("spend", subplot_id="s1", at="t1", cost=1))

    with open(ledger.path, "a") as f:
        f.write('{"schema":"run_fact.v1","kind":"s')

    records = read_facts(ledger)
    assert len(records) == 1
    assert records[0]["subplot_id"] == "s1"


def test_rollups_and_priors(tmp_path):
    ledger = RunLedger(tmp_path / "run-facts.jsonl")
    append_fact(
        ledger, build_fact("spend", subplot_id="s1", at="t1", tokens_cached=10, tokens_fresh=40)
    )
    append_fact(
        ledger, build_fact("spend", subplot_id="s2", at="t2", tokens_cached=50, tokens_fresh=0)
    )
    append_fact(ledger, build_fact("engine", subplot_id="s3", at="t3", cost=5.0))

    r = rollup(ledger, "spend")
    assert r["tokens_cached"]["sum"] == 60
    assert r["tokens_fresh"]["avg"] == 20.0

    ratio = reuse_ratio(ledger)
    assert ratio == 60 / 100.0

    prior = last_n_prior(ledger, "spend", "tokens_cached", 2)
    assert prior == 30.0


def test_concurrent_append_chaining(tmp_path):
    ledger = RunLedger(tmp_path / "run-facts.jsonl")

    def worker(i):
        fact = build_fact("spend", subplot_id=f"w{i}", at="now", cost=i)
        append_fact(ledger, fact)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    records = read_facts(ledger)
    assert len(records) == 50
    assert verify_chain(ledger).ok

    # Prove prev_hash is unique except for the first one
    prev_hashes = [r["prev_hash"] for r in records]
    assert len(set(prev_hashes)) == 50
    assert prev_hashes[0] == ""
