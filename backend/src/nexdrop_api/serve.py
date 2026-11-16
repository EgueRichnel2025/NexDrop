"""Development and local production entry point for the NexDrop API."""

from nexdrop_api.core.config import get_settings
from nexdrop_api.core.event_loop import configure_event_loop_policy

# This module is imported before uvicorn creates its event loop. Setting the
# Windows Selector policy inside main.py would be too late for Uvicorn's CLI.
configure_event_loop_policy()


def main() -> None:
    """Start Uvicorn after applying the platform event-loop configuration."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "nexdrop_api.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        # Uvicorn's default Windows asyncio factory explicitly selects Proactor.
        # "none" lets asyncio.run() use the Selector policy configured above.
        loop="none",
    )


if __name__ == "__main__":
    main()
