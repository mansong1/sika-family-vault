"""FastAPI dependencies for multi-sig group wallet."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> str:
    """Extract authenticated user ID from request header.

    Production → JWT validation via OAuth2 / API key middleware.
    """
    if not x_user_id:
        raise ValueError("X-User-ID header is required")
    return x_user_id


# Placeholder for future production deps: database session, auth, rate limiter, etc.
