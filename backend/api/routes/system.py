from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from dependencies import get_database

router = APIRouter(tags=['system'])


@router.get('/')
async def root():
    return {'message': 'Investor Panel Simulator API'}


@router.get('/healthz')
async def healthz():
    return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}


@router.get('/readyz')
async def readyz(db=Depends(get_database)):
    await db.command('ping')
    return {'status': 'ready'}
