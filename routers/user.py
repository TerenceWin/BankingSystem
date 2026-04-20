from fastapi import APIRouter, Depends, Path, HTTPException, Body
from ..database import db_dependency
from typing import Annotated
from .auth import get_current_user
from pydantic import BaseModel, Field
from starlette import status 
from ..models import Users
from passlib.context import CryptContext


router = APIRouter(
    prefix = '/user',
    tags= ['user']
)

class User_Update_Request(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=5)
    contact: int
    address: str = Field(min_length=3)

user_dependency = Annotated[Users, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get("/get_user_info", status_code=status.HTTP_200_OK)
async def get_user_info(user: user_dependency, db: db_dependency): 
    if user.requires_password_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please change you password in order to continue using the app.")
    return user

@router.put("/update_user_info", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_info(user: user_dependency, db: db_dependency, updated_info : User_Update_Request):
    if user.requires_password_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please change you password in order to continue using the app.")
    user.first_name = updated_info.first_name
    user.last_name = updated_info.last_name
    user.email = updated_info.email
    user.contact = updated_info.contact
    user.address = updated_info.address
    db.merge(user)
    db.commit()

@router.delete("/delete_user", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: user_dependency, db: db_dependency):
    if user.requires_password_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please change you password in order to continue using the app.")
    if user.role == 'admin' or user.role == 'manager':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin and Manager accounts cannot be deleted.")
    user.is_active = False
    db.merge(user)
    db.commit()

@router.put("/change_password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, current_password: str = Body(), new_password: str = Body(min_length=3)):
    if not bcrypt_context.verify(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    user.hashed_password = bcrypt_context.hash(new_password)
    user.requires_password_change = False
    db.merge(user)
    db.commit()

#get all transactions from all accounts current user holds 