"""RFC 9457 problem-details error responses.

Every API error shares one machine-readable shape so the web client can render
consistent error states without guessing at backend internals.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class FieldIssue(BaseModel):
    field: str
    message: str
    type: str


class ProblemDetails(BaseModel):
    type: str = Field(description="Stable URI identifying the problem type")
    title: str
    status: int
    detail: str
    instance: str
    code: str
    request_id: str | None = None
    errors: list[FieldIssue] | None = None


class AppError(Exception):
    """A deliberate, client-facing application error."""

    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        title: str | None = None,
        detail: str | None = None,
        errors: list[FieldIssue] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.title = title or HTTPStatus(status_code).phrase
        self.detail = detail or self.title
        self.errors = errors
        self.headers = headers
        super().__init__(self.detail)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _problem(
    request: Request,
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    errors: list[FieldIssue] | None = None,
) -> ProblemDetails:
    return ProblemDetails(
        type=f"https://auvyren.app/problems/{code}",
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        code=code,
        request_id=_request_id(request),
        errors=errors,
    )


def _response(problem: ProblemDetails, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _response(
        _problem(
            request,
            status=exc.status_code,
            code=exc.code,
            title=exc.title,
            detail=exc.detail,
            errors=exc.errors,
        ),
        headers=exc.headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    issues = [
        FieldIssue(
            field=".".join(str(part) for part in error.get("loc", [])),
            message=str(error.get("msg", "Invalid value")),
            type=str(error.get("type", "value_error")),
        )
        for error in exc.errors()
    ]
    return _response(
        _problem(
            request,
            status=422,
            code="request_validation_failed",
            title="Request validation failed",
            detail="One or more fields are invalid.",
            errors=issues,
        )
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status = exc.status_code
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "HTTP error"

    detail = exc.detail if isinstance(exc.detail, str) else title
    code = "not_found" if status == 404 else f"http_{status}"
    headers = dict(exc.headers) if exc.headers else None
    return _response(
        _problem(request, status=status, code=code, title=title, detail=detail),
        headers=headers,
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API exception on %s", request.url.path)
    return _response(
        _problem(
            request,
            status=500,
            code="internal_error",
            title="Internal server error",
            detail="An unexpected error occurred. Please try again.",
        )
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_error_handler)
