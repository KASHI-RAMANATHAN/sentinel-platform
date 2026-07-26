"""
app/core/logging_config.py

Centralized logging configuration placeholder.

TODO:
- Configure structured (JSON) logging for production.
- Attach request-id / correlation-id context to log records.
- Route logs to a centralized sink (e.g. Cloud Logging) in production.
"""

import logging


def configure_logging(debug: bool = True) -> None:
    """
    Configures root logging for the application.

    Args:
        debug: When True, uses a verbose human-readable format suitable
               for local development. When False, this is the place to
               switch to structured/JSON logging for production.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
