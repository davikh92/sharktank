from datetime import datetime, timezone
import uuid


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_email(self, email: str):
        return await self.db.users.find_one({'email': email}, {'_id': 0})

    async def find_by_id(self, user_id: str):
        return await self.db.users.find_one({'id': user_id}, {'_id': 0})

    async def create_user(self, email: str, password_hash: str):
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        user_doc = {
            'id': user_id,
            'email': email,
            'password_hash': password_hash,
            'created_at': created_at,
        }
        await self.db.users.insert_one(user_doc)
        return user_doc
