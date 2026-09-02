from collections.abc import Sequence
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def sanitize_validation_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:
    sanitized_errors: list[dict[str, Any]] = []
    for error in errors:
        if not isinstance(error, dict):
            sanitized_errors.append(
                {
                    "loc": (),
                    "msg": "Input validation failed",
                    "type": "value_error",
                }
            )
            continue

        sanitized_errors.append(
            {
                "loc": error.get("loc", ()),
                "msg": error.get("msg", "Input validation failed"),
                "type": error.get("type", "value_error"),
            }
        )
    return sanitized_errors


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    del request
    if not isinstance(exc, RequestValidationError):
        raise exc

    return JSONResponse(
        status_code=422,
        content={"detail": sanitize_validation_errors(exc.errors())},
    )
