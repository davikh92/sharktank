from fastapi import APIRouter

from shark_archetypes import get_all_archetypes

router = APIRouter(tags=['sharks'])


@router.get('/sharks')
async def get_sharks():
    return {'sharks': get_all_archetypes()}
