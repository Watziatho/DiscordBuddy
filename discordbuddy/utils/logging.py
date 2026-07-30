"""Logging initialization and configuration using Loguru."""

import logging
import sys
from pathlib import Path
from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect them to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    log_level: str = "INFO",
    log_dir: str | Path = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """Configure Loguru logging for DiscordBuddy.

    Args:
        log_level: Desired log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory path to store log files.
        enable_console: Whether to print log records to stderr.
        enable_file: Whether to write rotating log files to disk.
    """
    logger.remove()

    if enable_console:
        logger.add(
            sys.stderr,
            level=log_level.upper(),
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_destination = log_path / "discordbuddy.log"

        logger.add(
            file_destination,
            level=log_level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
        )

    # Intercept standard logging library calls (e.g. from PySide6, asyncio, etc.)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.info(f"Logging initialized at level '{log_level.upper()}'")
