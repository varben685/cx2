from collections.abc import Sequence
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from smc_assistant.application.audit import (
    AuditEventType,
    AuditLogger,
    create_audit_event,
)


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
    if not isinstance(exc, RequestValidationError):
        raise exc

    sanitized_errors = sanitize_validation_errors(exc.errors())
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if isinstance(audit_logger, AuditLogger):
        audit_logger.record(
            create_audit_event(
                AuditEventType.WEBHOOK_VALIDATION_FAILED,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "error_count": len(sanitized_errors),
                    "error_types": ",".join(
                        str(error["type"]) for error in sanitized_errors[:5]
                    ),
                },
            )
        )

    return JSONResponse(
        status_code=422,
        content={"detail": sanitized_errors},
    )
