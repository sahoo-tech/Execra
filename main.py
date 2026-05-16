#!/usr/bin/env python3
"""Execra entrypoint: parse CLI, configure logging, and start the API server."""

import argparse
import sys
from typing import Any

import uvicorn

from core.config import Settings

try:
    from core.logger import setup as setup_logging, get_logger
except Exception:
    # Fallback minimal logging if core.logger is unavailable
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
    parser.add_argument("--domain", choices=["digital", "physical", "hybrid"], default="digital")
    parser.add_argument("--fps", type=int, default=2)
    parser.add_argument("--llm", choices=["gpt-4o", "gemini", "llama"], default="gpt-4o")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Instantiate settings (reads .env / environment)
    settings = Settings()

    # Apply CLI overrides
    settings.LLM_BACKEND = args.llm
    settings.SCREEN_CAPTURE_FPS = args.fps
    settings.LOG_LEVEL = args.log_level

    # Setup logging
    setup_logging(settings.LOG_LEVEL)
    logger = get_logger("execra.main")
    logger.info("Starting Execra (mode=%s domain=%s)", args.mode, args.domain)

    # Print startup banner
    print_banner(settings, args.mode, args.domain, args)

    # Start FastAPI via uvicorn programmatically
    try:
        uvicorn.run("api.main:app", host=settings.API_HOST, port=settings.API_PORT, log_level=settings.LOG_LEVEL.lower())
    except Exception as exc:
        logger.exception("Failed to start uvicorn: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
