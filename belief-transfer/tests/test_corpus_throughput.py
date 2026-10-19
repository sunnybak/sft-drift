"""Scheduling contracts, uncapped ledgers and deterministic rate pacing."""
import asyncio
import pytest
from belief_transfer.config import load_job
from belief_transfer.generation.document_client import Budget, RatePacer
from belief_transfer.stages.stance_corpus import contract_for, subjects_for


def test_unlimited_dollar_budget_keeps_actual_and_uncertain_ledger():
    async def check():
        budget = Budget(None)
        await budget.reserve(100)
        await budget.reserve(200)
        await budget.settle(100, 30)
        await budget.settle(200, None)
        assert (budget.actual, budget.uncertain, budget.committed) == (30, 200, 230)
    asyncio.run(check())


def test_pacing_concurrent_requests_uses_both_limits_without_burst():
    async def check():
        now = [0.0]
        async def sleep(seconds):
            now[0] += seconds
        gate = RatePacer(10, 1000, clock=lambda: now[0], sleep=sleep)
        waits = await asyncio.gather(*(gate.acquire(200) for _ in range(4)))
        assert waits == [0, 15, 15, 15]
        assert now[0] == 45
        assert gate.reserved_tokens == 800 and gate.requests == 4
        with pytest.raises(ValueError):
            await gate.acquire(801)
        request_gate = RatePacer(10, 1000000, clock=lambda: now[0], sleep=sleep)
        await request_gate.acquire(1)
        assert await request_gate.acquire(1) == 7.5
    asyncio.run(check())


def test_scheduling_settings_are_explicit_contract_data():
    j = load_job(['+run=ethics_sft_throughput_check_v1'])
    assert j.throughput == 10 and j.stance_corpus.budget_usd is None
    assert j.stance_corpus.parallel_batches == 15
    contract = contract_for(j, subjects_for(j))
    assert contract['throughput'] == 10
    assert contract['settings']['rate_limit_tpm'] == 10000000
    assert contract['settings']['rate_utilization'] == .8
    with pytest.raises(ValueError):
        j.stance_corpus.__class__(**{**j.stance_corpus.model_dump(), 'rate_utilization':.81})


def test_unequal_reservations_respect_rolling_minute_as_well_as_spacing():
    async def check():
        now=[0.0]
        async def sleep(seconds): now[0] += seconds
        gate=RatePacer(1000,1000,clock=lambda:now[0],sleep=sleep)
        await gate.acquire(100)
        await gate.acquire(100)
        assert now[0] == 7.5
        await gate.acquire(700)
        assert now[0] == 60
        assert gate.window_tokens == 800
    asyncio.run(check())


def test_current_bank_has_ten_fresh_controls_and_matched_per_topic_counts():
    from collections import Counter
    from belief_transfer.dataset.stance_corpus import schedule
    j=load_job(['+run=ethics_sft_pooled_corpus_v4'])
    subjects=subjects_for(j)
    assert Counter(s['role'] for s in subjects)=={'ethical':90,'offtopic_training_control':10}
    assert j.stance_corpus.control_documents_per_position == j.stance_corpus.documents_per_position == 100
    plan=schedule(subjects,100,100,5,42)
    assert len(plan)==2100
    assert sum(len(b['slots'])*2 for b in plan)==20000
    assert j.throughput==384 and j.stance_corpus.budget_usd is None


@pytest.mark.parametrize('record,expected',[
    ({'http_status':503},True),({'http_status':429},True),({'http_status':400},False),
    ({'http_status':401},False),({'error':'InternalServerError'},True),
    ({'error':'APIConnectionError'},True),({'error':'response_incomplete'},False),
    ({'http_status':429,'error_body':{'code':'insufficient_quota'}},False),
])
def test_transient_classification(record,expected):
    from belief_transfer.generation.document_client import transient_error
    assert transient_error(record) is expected


def test_backoff_honors_retry_after_and_defaults_to_exponential():
    from belief_transfer.generation import document_client as client
    assert client.retry_delay({'response_headers':{'retry-after':'120'}},0)==120
    assert 4 <= client.retry_delay({},2) <= 5
    assert 1 <= client.retry_delay({'response_headers':{'retry-after':'garbage'}},0) <= 2
