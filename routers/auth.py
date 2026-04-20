from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status 
from ..models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from ..database import db_dependency
from enum import Enum

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/token')

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12734fe3'
ALGORITHM = 'HS256'

class Role(str, Enum): 
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"

class New_user_request(BaseModel):
    first_name: str
    last_name: str
    email: str
    contact: str
    address: str
    username: str
    password: str
    role: Role

class Token(BaseModel):
    access_token: str
    token_type: str

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('id')
        user = db.query(Users).filter(Users.id == user_id).first() 
        if not user: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = 'Could not validate user.')
        if user.is_active == False: 
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has been deleted, or no longer active")
        if user.username is None or user_id is None or user.role is None:     
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = 'Could not validate user.')
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = 'Could not validate user.')

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_user(db: db_dependency, new_user: New_user_request):
    
    user = db.query(Users).filter(Users.username == new_user.username).first()
    if user: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username is taken")
    full_name = f"{new_user.first_name} {new_user.last_name}"
    new_user = Users(
        username = new_user.username, 
        first_name = new_user.first_name,
        last_name = new_user.last_name, 
        full_name = full_name,
        email = new_user.email, 
        address = new_user.address,
        contact = new_user.contact, 
        hashed_password = bcrypt_context.hash(new_user.password),
        role = new_user.role,
        is_active = True
    )
    new_user.created_at = datetime.now(timezone.utc)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully."}

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def check_username(username: str, db):
    find_username = db.query(Users).filter(Users.username == username).first()
    if find_username:
        return find_username
    return False

def check_password(user: Users, password: str): 
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

@router.post("/token", response_model=Token)
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    verify_username = check_username(form_data.username, db)
    if not verify_username: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username not found ")
    
    verify_user_password = check_password(verify_username, form_data.password)

    if not verify_user_password: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect")
    if verify_user_password.is_active == False: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The user is not found. (DELETED)")
    user = verify_user_password
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}

