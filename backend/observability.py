import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger('api.observability')


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adiciona request_id e logging estruturado básico por request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-Id', str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()

        logger.info(
            'request.started',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'client': request.client.host if request.client else None,
            },
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers['X-Request-Id'] = request_id

        logger.info(
            'request.finished',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
            },
        )

        return response
