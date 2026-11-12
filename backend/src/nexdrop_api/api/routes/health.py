"""Service liveness and dependency readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from nexdrop_api.db.session import database_is_ready

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Report that the API process can serve requests."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    is_database_ready: Annotated[bool, Depends(database_is_ready)],
) -> Response:
    """Report whether dependencies required for database-backed work are ready."""
    if not is_database_ready:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": {"database": "unavailable"}},
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "checks": {"database": "available"}},
    )
