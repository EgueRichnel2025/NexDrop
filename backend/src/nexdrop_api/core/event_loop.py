"""Platform-specific asyncio configuration for database drivers."""

import asyncio
import sys


def configure_event_loop_policy() -> None:
    """Use the Windows selector loop required by Psycopg's async connections."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
