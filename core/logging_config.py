"""
Application logging configuration.

Keeps backend logs concise and focused on important
application-level events.
"""

import logging

LOG_FORMAT = "[%(levelname)s] %(message)s"


def configure_logging() -> None:
    """Configure application-wide logging once."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        force=True,
    )

    # Suppress noisy third-party library logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for an application module."""
    return logging.getLogger(name)