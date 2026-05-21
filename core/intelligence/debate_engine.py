"""
Multi-agent debate engine for low-trust guidance generation.

When the trust score for an LLM response falls below the routing threshold,
IntelligenceCore routes the guidance request through DebateEngine rather than
making a single LLM call.  DebateEngine runs parallel Proposer and Critic calls
for a configurable number of rounds, then synthesises a final answer through a
Judge call, producing guidance that is more robust to hallucination and
under-specified actions.

Typical usage::

    from core.intelligence.llm_client import LLMClientFactory
    from core.intelligence.debate_engine import IntelligenceCore

    client = LLMClientFactory.create()
    core = IntelligenceCore(client)
    guidance = await core.generate_guidance(prompt, trust_score=0.45)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from core.intelligence.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)

# Trust score below which guidance is routed through DebateEngine
LOW_TRUST_THRESHOLD: float = 0.65

# ---------------------------------------------------------------------------
# Prompt role prefixes
# ---------------------------------------------------------------------------

_PROPOSER_PREFIX = (
    "You are a helpful UI guidance assistant acting as the Proposer. "
    "Suggest the clearest, safest next action for the user."
)

_CRITIC_PREFIX = (
    "You are a critical reviewer acting as the Critic. "
    "Identify risks, ambiguities, or flaws in the current guidance context."
)

_JUDGE_PREFIX = (
    "You are a synthesis judge. "
    "Given the debate transcript below, produce a final, concise, "
    "actionable guidance response that incorporates valid proposals "
    "and addresses the identified concerns."
)


# ---------------------------------------------------------------------------
# Internal data structure
# ---------------------------------------------------------------------------

@dataclass
class _DebateRound:
    """One completed round of Proposer and Critic outputs."""

    proposal: str
    critique: str


# ---------------------------------------------------------------------------
# DebateEngine
# ---------------------------------------------------------------------------

class DebateEngine:
    """
    Orchestrates a structured debate between Proposer and Critic agents,
    then synthesises a final response through a Judge call.

    All LLM calls are made through a single *client* instance, using
    role-prefixed prompts to elicit distinct reasoning modes.  This avoids
    the need for multiple API keys or separate model deployments.

    In each round, the Proposer and Critic receive identical context (the
    original prompt plus the history of all previous rounds) and run in
    parallel via ``asyncio.gather``.  The resulting proposal and critique
    are appended to the history before the next round begins.

    After all rounds complete, a Judge call synthesises the full transcript
    into a single final guidance string.

    Args:
        client: The LLM backend to use for all debate and judge calls.

    Example::

        engine = DebateEngine(llm_client)
        guidance = await engine.debate("How do I submit this form?", rounds=2)
    """

    def __init__(self, client: BaseLLMClient) -> None:
        self._client = client

    async def debate(self, prompt: str, rounds: int = 2) -> str:
        """
        Run *rounds* of parallel Proposer/Critic debate, then return a
        Judge synthesis.

        Args:
            prompt: The original user guidance request.
            rounds: Number of debate rounds (must be >= 1).  Defaults to 2.

        Returns:
            Final synthesised guidance string from the Judge.

        Raises:
            ValueError: If *rounds* is less than 1.
        """
        if rounds < 1:
            raise ValueError(f"rounds must be >= 1; got {rounds}")

        history: list[_DebateRound] = []

        for round_index in range(rounds):
            proposer_prompt = self._build_proposer_prompt(prompt, history)
            critic_prompt = self._build_critic_prompt(prompt, history)

            proposal, critique = await asyncio.gather(
                self._client.complete(proposer_prompt),
                self._client.complete(critic_prompt),
            )

            history.append(_DebateRound(proposal=proposal, critique=critique))
            logger.debug(
                "Debate round %d/%d complete (proposal=%d chars, critique=%d chars)",
                round_index + 1,
                rounds,
                len(proposal),
                len(critique),
            )

        judge_prompt = self._build_judge_prompt(prompt, history)
        result = await self._client.complete(judge_prompt)
        logger.debug("Judge synthesis complete (%d chars)", len(result))
        return result

    # ------------------------------------------------------------------
    # Prompt builders (static — no instance state required)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_proposer_prompt(prompt: str, history: list[_DebateRound]) -> str:
        parts = [_PROPOSER_PREFIX]
        if history:
            parts.append("\nDebate history so far:")
            for i, r in enumerate(history, 1):
                parts.append(f"  Round {i} proposal: {r.proposal}")
                parts.append(f"  Round {i} critique: {r.critique}")
        parts.append(f"\nUser request: {prompt}")
        parts.append("\nProposal:")
        return "\n".join(parts)

    @staticmethod
    def _build_critic_prompt(prompt: str, history: list[_DebateRound]) -> str:
        parts = [_CRITIC_PREFIX]
        if history:
            parts.append("\nDebate history so far:")
            for i, r in enumerate(history, 1):
                parts.append(f"  Round {i} proposal: {r.proposal}")
                parts.append(f"  Round {i} critique: {r.critique}")
        parts.append(f"\nUser request: {prompt}")
        parts.append("\nCritique:")
        return "\n".join(parts)

    @staticmethod
    def _build_judge_prompt(prompt: str, history: list[_DebateRound]) -> str:
        parts = [_JUDGE_PREFIX, "\nDebate transcript:"]
        for i, r in enumerate(history, 1):
            parts.append(f"  Round {i} proposal: {r.proposal}")
            parts.append(f"  Round {i} critique: {r.critique}")
        parts.append(f"\nOriginal request: {prompt}")
        parts.append("\nFinal guidance:")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# IntelligenceCore
# ---------------------------------------------------------------------------

class IntelligenceCore:
    """
    Orchestrates guidance generation with automatic routing based on trust score.

    * ``trust_score >= LOW_TRUST_THRESHOLD (0.65)``  →  single LLM call
      (existing behaviour, zero added latency)
    * ``trust_score <  LOW_TRUST_THRESHOLD``          →  multi-round debate
      via :class:`DebateEngine`

    If the debate path raises an exception (e.g. transient LLM error), the
    core falls back to a single LLM call and logs a warning so operators can
    investigate without a user-visible failure.

    Args:
        client: LLM backend passed through to both paths.
        debate_rounds: Number of debate rounds when routing low-trust requests.
            Defaults to 2.

    Example::

        core = IntelligenceCore(LLMClientFactory.create())
        guidance = await core.generate_guidance(prompt, trust_score=0.45)
    """

    def __init__(
        self,
        client: BaseLLMClient,
        debate_rounds: int = 2,
    ) -> None:
        self._client = client
        self._debate_engine = DebateEngine(client)
        self._debate_rounds = debate_rounds

    async def generate_guidance(self, prompt: str, trust_score: float) -> str:
        """
        Generate guidance, routing through :class:`DebateEngine` when the
        trust score is below the threshold.

        Args:
            prompt: The guidance prompt to send to the LLM.
            trust_score: Normalised trust score ``[0.0, 1.0]`` produced by
                ``calculate_trust_score()``.

        Returns:
            Guidance string from whichever path was taken.
        """
        if trust_score < LOW_TRUST_THRESHOLD:
            logger.info(
                "trust_score=%.3f < %.2f — routing through DebateEngine (%d rounds)",
                trust_score,
                LOW_TRUST_THRESHOLD,
                self._debate_rounds,
            )
            try:
                return await self._debate_engine.debate(
                    prompt, rounds=self._debate_rounds
                )
            except Exception:
                logger.exception(
                    "DebateEngine failed; falling back to single LLM call"
                )

        return await self._client.complete(prompt)


# ---------------------------------------------------------------------------
# Lightweight benchmarking utility
# ---------------------------------------------------------------------------

@dataclass
class DebateBenchmark:
    """Wall-clock latency comparison between the debate and single-call paths."""

    debate_latency_s: float
    single_latency_s: float

    @property
    def overhead_s(self) -> float:
        """Additional latency introduced by the debate path."""
        return self.debate_latency_s - self.single_latency_s

    def __str__(self) -> str:
        return (
            f"debate={self.debate_latency_s:.3f}s  "
            f"single={self.single_latency_s:.3f}s  "
            f"overhead={self.overhead_s:+.3f}s"
        )


async def benchmark_debate(
    engine: DebateEngine,
    client: BaseLLMClient,
    prompt: str,
    rounds: int = 2,
) -> DebateBenchmark:
    """
    Measure wall-clock latency for the debate path vs a single LLM call.

    This function is intended for development profiling only — it should not
    be called in production request paths.

    Args:
        engine: A configured :class:`DebateEngine` instance.
        client: The same LLM client used by *engine*.
        prompt: Representative prompt to benchmark with.
        rounds: Number of debate rounds to time.

    Returns:
        A :class:`DebateBenchmark` with latency measurements and overhead.
    """
    t0 = time.perf_counter()
    await engine.debate(prompt, rounds=rounds)
    debate_latency = time.perf_counter() - t0

    t0 = time.perf_counter()
    await client.complete(prompt)
    single_latency = time.perf_counter() - t0

    result = DebateBenchmark(
        debate_latency_s=debate_latency,
        single_latency_s=single_latency,
    )
    logger.info("Benchmark: %s", result)
    return result
