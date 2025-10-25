"""
API Authentication Middleware for AaaS
"""

from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional

from .config import settings


# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key for protected endpoints

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If API key requirement is disabled in config, allow all requests
    if not settings.require_api_key:
        return "disabled"

    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


async def verify_api_key_optional(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Optional API key verification for endpoints that may be public

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key or None if not required
    """
    if not settings.require_api_key:
        return None

    if not api_key:
        return None

    # If provided, it must be valid
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key
