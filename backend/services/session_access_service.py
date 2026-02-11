from fastapi import HTTPException

from repositories.session_repository import SessionRepository


class SessionAccessService:
    def __init__(self, db):
        self.session_repository = SessionRepository(db)

    async def get_owned_session_or_404(self, session_id: str, user_id: str):
        session = await self.session_repository.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail='Sessão não encontrada')

        if session['user_id'] != user_id:
            raise HTTPException(status_code=403, detail='Acesso negado')

        return session
