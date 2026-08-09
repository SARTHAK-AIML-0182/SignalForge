"""
API Input Validation & Sanitization Helpers for SignalForge.
"""

from typing import Optional
from fastapi import HTTPException, status

MAX_ID_LENGTH = 100
MAX_OFFSET_LIMIT = 10000
FORBIDDEN_ID_SUBSTRINGS = ["..", "/", "\\", "\x00", "\n", "\r", "\t"]


def validate_identifier(id_val: str, field_name: str = "identifier") -> str:
    """
    Validate path/query identifiers (e.g. agent_id, workflow_id).
    Protects against empty values, excessive length, path traversal, control chars, and credential-like strings.
    Raises HTTPException(400 or 422) if invalid.
    """
    if not isinstance(id_val, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name}: must be a string."
        )

    stripped = id_val.strip()
    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: cannot be empty or whitespace."
        )

    if len(stripped) > MAX_ID_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: length exceeds maximum of {MAX_ID_LENGTH} characters."
        )

    if any(forbidden in stripped for forbidden in FORBIDDEN_ID_SUBSTRINGS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: contains forbidden characters or path traversal elements."
        )

    lower = stripped.lower()
    if any(cred in lower for cred in ["bearer ", "password=", "secret=", "token="]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: contains forbidden credential keywords."
        )

    return stripped


def validate_pagination(limit: int, offset: int) -> None:
    """
    Validate limit and offset query parameters.
    Enforces limit (1 to 100) and offset (0 to 10000).
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pagination limit must be an integer between 1 and 100."
        )

    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or offset > MAX_OFFSET_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Pagination offset must be an integer between 0 and {MAX_OFFSET_LIMIT}."
        )


def validate_status_filter(status_filter: Optional[str]) -> Optional[str]:
    """
    Validate status_filter query parameter.
    """
    if status_filter is None:
        return None

    if not isinstance(status_filter, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status filter must be a string."
        )

    stripped = status_filter.strip()
    if not stripped:
        return None

    if len(stripped) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status filter length cannot exceed 50 characters."
        )

    if any(forbidden in stripped for forbidden in FORBIDDEN_ID_SUBSTRINGS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status filter contains forbidden characters."
        )

    return stripped
