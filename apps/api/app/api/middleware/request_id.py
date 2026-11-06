from __future__ import annotations

import re
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a trustworthy request ID to every request/response and log line."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if _VALID_REQUEST_ID.fullmatch(incoming) else uuid4().hex
        request.state.request_id = request_id
        token = set_request_id(request_id)

        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
