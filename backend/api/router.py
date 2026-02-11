from fastapi import APIRouter

from api.routes.auth import router as auth_router
from api.routes.reports import router as reports_router
from api.routes.sessions import router as sessions_router
from api.routes.sharks import router as sharks_router
from api.routes.system import router as system_router

api_router = APIRouter(prefix='/api')
api_router.include_router(auth_router)
api_router.include_router(sharks_router)
api_router.include_router(sessions_router)
api_router.include_router(reports_router)
api_router.include_router(system_router)
