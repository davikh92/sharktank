import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger('api.errors')


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, 'request_id', None)
        logger.warning(
            'http.exception',
            extra={
                'request_id': request_id,
                'path': request.url.path,
                'status_code': exc.status_code,
                'detail': exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'error': {
                    'type': 'http_error',
                    'message': exc.detail,
                    'request_id': request_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, 'request_id', None)
        logger.warning(
            'validation.exception',
            extra={
                'request_id': request_id,
                'path': request.url.path,
                'errors': exc.errors(),
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                'error': {
                    'type': 'validation_error',
                    'message': 'Payload inválido.',
                    'details': exc.errors(),
                    'request_id': request_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, 'request_id', None)
        logger.exception(
            'unhandled.exception',
            extra={
                'request_id': request_id,
                'path': request.url.path,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                'error': {
                    'type': 'internal_error',
                    'message': 'Erro interno inesperado.',
                    'request_id': request_id,
                }
            },
        )
