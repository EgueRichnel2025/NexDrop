"""Minimal application logging configuration."""

import logging


def configure_logging(level: str) -> None:
    """Configure standard-library logging without exposing configuration secrets."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
