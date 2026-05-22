#!/usr/bin/env python3
"""Execra entrypoint: parse CLI, configure logging, and start the API server."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from typing import Any

import uvicorn

from core.config import Settings
from core.pipeline import ExecraPipeline, PipelineConfig

try:
    from core.logger import setup as setup_logging, get_logger
except Exception:
    def setup_logging(level: str) -> None:  # type: ignore
        import logging
        logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))

    def get_logger(name: str):  # type: ignore
        import logging
        return logging.getLogger(name)


def print_banner(settings: Settings, mode: str, domain: str, args: Any) -> None:
    lines = []
    lines.append("+" + "=" * 46 + "+")
    lines.append("|{:^46}|".format("EXECRA — STARTUP"))
    lines.append("+" + "-" * 46 + "+")
    lines.append("| Mode: {:<36}|".format(mode))
    lines.append("| Domain: {:<34}|".format(domain))
    lines.append("|{:^46}|".format("Active Settings"))
    lines.append("| LLM_BACKEND: {:<33}|".format(settings.LLM_BACKEND))
    lines.append("| SCREEN_CAPTURE_FPS: {:<25}|".format(settings.SCREEN_CAPTURE_FPS))
    lines.append("| API_HOST: {:<36}|".format(settings.API_HOST))
    lines.append("| API_PORT: {:<36}|".format(settings.API_PORT))
    lines.append("| LOG_LEVEL: {:<35}|".format(settings.LOG_LEVEL))
    lines.append("+" + "=" * 46 + "+")
    print("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="execra")
    parser.add_argument("--mode", choices=["passive", "active", "mixed"], default="passive")
    parser.add_argument("--domain", choices=["digital", "physical"], default="digital")
    parser.add_argument("--fps", type=int, default=2)
    parser.add_argument("--llm", choices=["gpt-4o", "gemini", "llama"], default="gpt-4o")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    pipeline = ExecraPipeline(
        domain=args.domain,
        mode=args.mode,
        config=PipelineConfig(),
    )

    # Inject pipeline into the API module before the server starts
    import api.main as api_module
    api_module.pipeline = pipeline

    # Graceful shutdown on SIGINT / SIGTERM
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _handle_signal(sig: int) -> None:
        logger.info("Signal %s – initiating shutdown", signal.Signals(sig).name)
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal, sig)

    uvicorn_config = uvicorn.Config(
        "api.main:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower(),
        loop="none",
    )
    server = uvicorn.Server(uvicorn_config)

    try:
        await asyncio.gather(
            server.serve(),
            pipeline.run(),
            _wait_for_shutdown(shutdown_event, pipeline, server),
        )
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Execra exited. Metrics: %s", pipeline.get_metrics())


async def _wait_for_shutdown(
    event: asyncio.Event,
    pipeline: ExecraPipeline,
    server: "uvicorn.Server",
) -> None:
    await event.wait()
    await pipeline.stop()
    server.should_exit = True


def main() -> None:
    args = parse_args()
    settings = Settings()

    # Apply CLI overrides
    settings.LLM_BACKEND = args.llm
    settings.SCREEN_CAPTURE_FPS = args.fps
    settings.LOG_LEVEL = args.log_level

    setup_logging(settings.LOG_LEVEL)
    global logger
    logger = get_logger("execra.main")

    print_banner(settings, args.mode, args.domain, args)
    logger.info("Starting Execra (mode=%s domain=%s)", args.mode, args.domain)

    try:
        asyncio.run(_run(args, settings))
    except KeyboardInterrupt:
        sys.exit(0)


logger = get_logger("execra.main")

if __name__ == "__main__":
    main()
