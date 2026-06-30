"""Loguru logging setup."""

from __future__ import annotations

import logging
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """Route standard logging records through Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


def configure_logging(log_dir: Path, level: str) -> None:
    """Configure application, security, AI, processing, and error logs."""

    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(log_dir / "application.log", level=level, rotation="5 MB", retention=5)
    logger.add(log_dir / "security.log", level="WARNING", rotation="5 MB", retention=5)
    logger.add(log_dir / "ai.log", level=level, rotation="5 MB", retention=5, filter=lambda r: r["extra"].get("channel") == "ai")
    logger.add(log_dir / "processing.log", level=level, rotation="5 MB", retention=5, filter=lambda r: r["extra"].get("channel") == "processing")
    logger.add(log_dir / "errors.log", level="ERROR", rotation="5 MB", retention=5)
    logging.basicConfig(handlers=[InterceptHandler()], level=level, force=True)

