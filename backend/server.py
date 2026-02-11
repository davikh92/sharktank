import logging
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.error_handlers import register_exception_handlers
from api.router import api_router
from database import close_db_client
from observability import RequestContextMiddleware


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


app = FastAPI(title='Investor Panel Simulator')
app.include_router(api_router)
register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)


def _resolve_cors_origins() -> list[str]:
    app_env = os.environ.get('APP_ENV', 'development').strip().lower()
    configured = os.environ.get('CORS_ORIGINS', '').strip()

    if configured:
        return [origin.strip() for origin in configured.split(',') if origin.strip()]

    if app_env in {'production', 'staging'}:
        raise RuntimeError('CORS_ORIGINS é obrigatório quando APP_ENV é production/staging.')

    return [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_resolve_cors_origins(),
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('shutdown')
async def shutdown_db_client():
    close_db_client()
