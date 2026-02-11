from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from dependencies import get_database
from models import ReportResponse, SessionStatus
from report_generator import ReportGenerator
from services.session_access_service import SessionAccessService

router = APIRouter(tags=['reports'])


@router.post('/sessions/{session_id}/report', response_model=ReportResponse)
async def generate_report(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    session = await session_access.get_owned_session_or_404(session_id, current_user['user_id'])

    if session['status'] != SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail='Sessão ainda não foi concluída')

    existing_report = await db.reports.find_one({'session_id': session_id}, {'_id': 0})
    if existing_report:
        return ReportResponse(**existing_report)

    generator = ReportGenerator(db, session_id)
    return await generator.generate_report()


@router.get('/sessions/{session_id}/report', response_model=ReportResponse)
async def get_report(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    await session_access.get_owned_session_or_404(session_id, current_user['user_id'])

    report = await db.reports.find_one({'session_id': session_id}, {'_id': 0})
    if not report:
        raise HTTPException(status_code=404, detail='Relatório não encontrado')
    return ReportResponse(**report)

