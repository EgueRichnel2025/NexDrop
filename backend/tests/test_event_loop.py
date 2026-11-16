"""Platform-specific event-loop configuration tests."""

import asyncio
import sys

from nexdrop_api.core.event_loop import configure_event_loop_policy


def test_windows_uses_selector_event_loop_for_async_psycopg() -> None:
    configure_event_loop_policy()
    if sys.platform == "win32":
        assert isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy)
