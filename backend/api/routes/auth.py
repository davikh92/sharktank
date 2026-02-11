from fastapi import APIRouter, Depends, HTTPException

from auth import create_access_token, get_current_user, hash_password, verify_password
from dependencies import get_database
from models import TokenResponse, UserLogin, UserRegister, UserResponse
from repositories.user_repository import UserRepository

router = APIRouter(tags=['auth'])


@router.post('/auth/register', response_model=TokenResponse)
async def register(user_data: UserRegister, db=Depends(get_database)):
    user_repository = UserRepository(db)
    existing_user = await user_repository.find_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail='Email já cadastrado')

    user = await user_repository.create_user(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    token = create_access_token({'user_id': user['id'], 'email': user['email']})
    return TokenResponse(
        access_token=token,
        token_type='bearer',
        user=UserResponse(id=user['id'], email=user['email'], created_at=user['created_at']),
    )


@router.post('/auth/login', response_model=TokenResponse)
async def login(credentials: UserLogin, db=Depends(get_database)):
    user_repository = UserRepository(db)
    user = await user_repository.find_by_email(credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail='Credenciais inválidas')

    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Credenciais inválidas')

    token = create_access_token({'user_id': user['id'], 'email': user['email']})
    return TokenResponse(
        access_token=token,
        token_type='bearer',
        user=UserResponse(id=user['id'], email=user['email'], created_at=user['created_at']),
    )


@router.get('/auth/me', response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    user_repository = UserRepository(db)
    user = await user_repository.find_by_id(current_user['user_id'])
    if not user:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')

    return UserResponse(id=user['id'], email=user['email'], created_at=user['created_at'])
