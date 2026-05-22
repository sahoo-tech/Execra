"""
main.py
=======
Execra entry-point.

Starts the FastAPI server together with the real-time guidance pipeline
so that both share the same asyncio event loop.

Usage::

    python main.py [--domain digital|physical] [--mode passive|active|mixed]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys

import uvicorn

from core.pipeline import Domain, ExecraPipeline, Mode, PipelineConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Execra guidance system")
    parser.add_argument(
        "--domain", choices=["digital", "physical"], default="digital",
    )
    parser.add_argument(
        "--mode", choices=["passive", "active", "mixed"], default="passive",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--log-level", default="info",
        choices=["debug", "info", "warning", "error"],
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
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
        log_level=args.log_level,
        loop="none",
    )
    server = uvicorn.Server(uvicorn_config)

    logger.info("Starting Execra (domain=%s, mode=%s)", args.domain, args.mode)

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


if __name__ == "__main__":
    args = _parse_args()
    logging.getLogger().setLevel(args.log_level.upper())
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        sys.exit(0)