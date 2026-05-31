"""
Unit tests for core/intelligence/debate_engine.py

Tests cover:
- Proposer/Critic orchestration and call counts
- Multi-round context propagation (history in prompts)
- Judge synthesis flow
- Low-trust and high-trust routing in IntelligenceCore
- Async execution via asyncio.gather
- Fallback behaviour when DebateEngine raises
- DebateBenchmark overhead calculation
- Edge-case validation (rounds < 1)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch

from core.intelligence.debate_engine import (
    LOW_TRUST_THRESHOLD,
    DebateBenchmark,
    DebateEngine,
    IntelligenceCore,
    benchmark_debate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(*responses: str) -> MagicMock:
    """Return a mock BaseLLMClient whose complete() yields *responses* in order."""
    client = MagicMock()
    client.complete = AsyncMock(side_effect=list(responses))
    return client


# ---------------------------------------------------------------------------
# DebateEngine — orchestration
# ---------------------------------------------------------------------------

async def test_debate_single_round_makes_three_calls():
    """1 round → 2 parallel role calls + 1 judge call = 3 total."""
    client = _make_client("PROPOSAL", "CRITIQUE", "FINAL")
    engine = DebateEngine(client)

    result = await engine.debate("test prompt", rounds=1)

    assert result == "FINAL"
    assert client.complete.await_count == 3


async def test_debate_two_rounds_makes_five_calls():
    """2 rounds → 4 role calls + 1 judge call = 5 total."""
    client = _make_client(
        "PROPOSAL_1", "CRITIQUE_1",   # round 1
        "PROPOSAL_2", "CRITIQUE_2",   # round 2
        "FINAL",                       # judge
    )
    engine = DebateEngine(client)

    result = await engine.debate("test prompt", rounds=2)

    assert result == "FINAL"
    assert client.complete.await_count == 5


async def test_debate_n_rounds_makes_correct_total_calls():
    """n rounds → 2n role calls + 1 judge call."""
    for n in (1, 2, 3):
        responses = []
        for i in range(n):
            responses += [f"P{i}", f"C{i}"]
        responses.append("JUDGE")

        client = _make_client(*responses)
        engine = DebateEngine(client)
        await engine.debate("prompt", rounds=n)

        assert client.complete.await_count == 2 * n + 1


async def test_debate_returns_judge_output():
    """The return value is exactly what the judge call returns."""
    client = _make_client("p", "c", "final answer here")
    engine = DebateEngine(client)

    result = await engine.debate("q", rounds=1)

    assert result == "final answer here"


# ---------------------------------------------------------------------------
# DebateEngine — context propagation
# ---------------------------------------------------------------------------

async def test_round2_proposer_prompt_contains_round1_history():
    """
    After round 1, the round-2 Proposer prompt must contain both the
    round-1 proposal and critique so context is preserved across rounds.
    """
    client = _make_client("PROPOSAL_1", "CRITIQUE_1", "PROPOSAL_2", "CRITIQUE_2", "JUDGE")
    engine = DebateEngine(client)

    await engine.debate("my prompt", rounds=2)

    # Calls: [proposer_r1, critic_r1, proposer_r2, critic_r2, judge]
    calls = client.complete.call_args_list
    round2_proposer_prompt = calls[2].args[0]

    assert "PROPOSAL_1" in round2_proposer_prompt
    assert "CRITIQUE_1" in round2_proposer_prompt


async def test_round2_critic_prompt_contains_round1_history():
    """The round-2 Critic prompt also carries the full round-1 history."""
    client = _make_client("PROPOSAL_1", "CRITIQUE_1", "PROPOSAL_2", "CRITIQUE_2", "JUDGE")
    engine = DebateEngine(client)

    await engine.debate("my prompt", rounds=2)

    calls = client.complete.call_args_list
    round2_critic_prompt = calls[3].args[0]

    assert "PROPOSAL_1" in round2_critic_prompt
    assert "CRITIQUE_1" in round2_critic_prompt


async def test_judge_prompt_contains_full_transcript():
    """Judge prompt must include all proposals and critiques from all rounds."""
    client = _make_client("P1", "C1", "P2", "C2", "JUDGE")
    engine = DebateEngine(client)

    await engine.debate("original request", rounds=2)

    judge_prompt = client.complete.call_args_list[-1].args[0]

    assert "P1" in judge_prompt
    assert "C1" in judge_prompt
    assert "P2" in judge_prompt
    assert "C2" in judge_prompt
    assert "original request" in judge_prompt


async def test_round1_prompts_contain_user_request():
    """Both round-1 role prompts must include the original user request."""
    client = _make_client("proposal", "critique", "judge")
    engine = DebateEngine(client)

    await engine.debate("click the submit button", rounds=1)

    calls = client.complete.call_args_list
    proposer_prompt = calls[0].args[0]
    critic_prompt = calls[1].args[0]

    assert "click the submit button" in proposer_prompt
    assert "click the submit button" in critic_prompt


async def test_proposer_and_critic_prompts_are_distinct():
    """Proposer and Critic prompts must differ (different role prefixes)."""
    client = _make_client("p", "c", "j")
    engine = DebateEngine(client)

    await engine.debate("prompt", rounds=1)

    calls = client.complete.call_args_list
    proposer_prompt = calls[0].args[0]
    critic_prompt = calls[1].args[0]

    assert proposer_prompt != critic_prompt


# ---------------------------------------------------------------------------
# DebateEngine — validation and edge cases
# ---------------------------------------------------------------------------

async def test_debate_rounds_less_than_one_raises():
    """rounds < 1 must raise ValueError immediately."""
    client = _make_client()
    engine = DebateEngine(client)

    with pytest.raises(ValueError, match="rounds must be >= 1"):
        await engine.debate("prompt", rounds=0)

    client.complete.assert_not_awaited()


async def test_debate_rounds_negative_raises():
    client = _make_client()
    engine = DebateEngine(client)

    with pytest.raises(ValueError, match="rounds must be >= 1"):
        await engine.debate("prompt", rounds=-3)


# ---------------------------------------------------------------------------
# IntelligenceCore — routing
# ---------------------------------------------------------------------------

async def test_low_trust_routes_to_debate_engine():
    """trust_score < 0.65 must invoke debate, not a bare complete() call."""
    client = _make_client("P", "C", "DEBATE_RESULT")
    core = IntelligenceCore(client, debate_rounds=1)

    result = await core.generate_guidance("some prompt", trust_score=0.40)

    assert result == "DEBATE_RESULT"
    # 1 round = 3 LLM calls (proposer, critic, judge)
    assert client.complete.await_count == 3


async def test_trust_at_threshold_uses_single_call():
    """trust_score == 0.65 (exactly at threshold) must use the single-call path."""
    client = _make_client("DIRECT")
    core = IntelligenceCore(client, debate_rounds=2)

    result = await core.generate_guidance("prompt", trust_score=LOW_TRUST_THRESHOLD)

    assert result == "DIRECT"
    assert client.complete.await_count == 1


async def test_high_trust_uses_single_call():
    """trust_score >= 0.65 must bypass debate and call complete() once."""
    client = _make_client("DIRECT_RESULT")
    core = IntelligenceCore(client, debate_rounds=2)

    result = await core.generate_guidance("prompt", trust_score=0.90)

    assert result == "DIRECT_RESULT"
    assert client.complete.await_count == 1


async def test_low_trust_threshold_boundary():
    """Trust score just below threshold triggers debate."""
    client = _make_client("P", "C", "DEBATE_RESULT")
    core = IntelligenceCore(client, debate_rounds=1)

    result = await core.generate_guidance("prompt", trust_score=LOW_TRUST_THRESHOLD - 0.001)

    assert result == "DEBATE_RESULT"
    assert client.complete.await_count == 3


# ---------------------------------------------------------------------------
# IntelligenceCore — fallback on debate failure
# ---------------------------------------------------------------------------

async def test_debate_failure_falls_back_to_single_call():
    """If DebateEngine.debate() raises, generate_guidance falls back silently."""
    client = MagicMock()
    client.complete = AsyncMock(return_value="FALLBACK")
    core = IntelligenceCore(client, debate_rounds=1)

    # Make the debate engine itself raise
    with patch.object(core._debate_engine, "debate", side_effect=RuntimeError("LLM error")):
        result = await core.generate_guidance("prompt", trust_score=0.30)

    assert result == "FALLBACK"
    client.complete.assert_awaited_once_with("prompt")


async def test_high_trust_never_calls_debate_engine():
    """High-trust path must not touch DebateEngine at all."""
    client = _make_client("RESULT")
    core = IntelligenceCore(client, debate_rounds=2)

    with patch.object(core._debate_engine, "debate") as mock_debate:
        await core.generate_guidance("prompt", trust_score=0.95)
        mock_debate.assert_not_called()


# ---------------------------------------------------------------------------
# IntelligenceCore — configurable debate rounds
# ---------------------------------------------------------------------------

async def test_debate_rounds_parameter_respected():
    """debate_rounds constructor argument must control rounds in DebateEngine."""
    # 3 rounds = 6 role calls + 1 judge = 7 total
    responses = ["P1", "C1", "P2", "C2", "P3", "C3", "JUDGE"]
    client = _make_client(*responses)
    core = IntelligenceCore(client, debate_rounds=3)

    result = await core.generate_guidance("prompt", trust_score=0.20)

    assert result == "JUDGE"
    assert client.complete.await_count == 7


# ---------------------------------------------------------------------------
# DebateBenchmark
# ---------------------------------------------------------------------------

def test_benchmark_overhead_calculation():
    """overhead_s must be the arithmetic difference of the two latencies."""
    bm = DebateBenchmark(debate_latency_s=1.5, single_latency_s=0.5)
    assert bm.overhead_s == pytest.approx(1.0)


def test_benchmark_negative_overhead():
    """overhead_s can be negative (single call slower than debate in mock)."""
    bm = DebateBenchmark(debate_latency_s=0.3, single_latency_s=0.5)
    assert bm.overhead_s == pytest.approx(-0.2)


def test_benchmark_str_contains_all_fields():
    bm = DebateBenchmark(debate_latency_s=2.0, single_latency_s=0.4)
    s = str(bm)
    assert "debate=" in s
    assert "single=" in s
    assert "overhead=" in s


async def test_benchmark_debate_function_returns_benchmark():
    """benchmark_debate() must return a DebateBenchmark with non-negative latencies."""
    client = _make_client(
        "P", "C", "JUDGE",   # debate path (1 round = 3 calls)
        "SINGLE",             # single call
    )
    engine = DebateEngine(client)

    result = await benchmark_debate(engine, client, "test prompt", rounds=1)

    assert isinstance(result, DebateBenchmark)
    assert result.debate_latency_s >= 0.0
    assert result.single_latency_s >= 0.0
