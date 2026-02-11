
class SessionRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_id(self, session_id: str):
        return await self.db.sessions.find_one({'id': session_id}, {'_id': 0})

    async def list_by_user(self, user_id: str, limit: int = 100):
        return await self.db.sessions.find({'user_id': user_id}, {'_id': 0}).sort('created_at', -1).to_list(limit)
