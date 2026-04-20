from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status 
from ..models import Users, Account
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from ..database import db_dependency
from .auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/token')

user_dependency = Annotated[Users, Depends(get_current_user)]

@router.get('/get_users', status_code=status.HTTP_200_OK)
async def get_users(admin: user_dependency, db: db_dependency): 
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    users = db.query(Users).filter(Users.role == 'user').all() 
    return {"Users" : users}

@router.get('/get_managers', status_code=status.HTTP_200_OK)
async def get_managers(admin: user_dependency, db: db_dependency):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    managers = db.query(Users).filter(Users.role == 'manager').all()
    return {"Managers": managers}

@router.get('/get_user_by_id/{user_id}', status_code=status.HTTP_200_OK)
async def get_user_by_id(admin: user_dependency, db: db_dependency, user_id : int = Path(gt=0)):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    user = db.query(Users).filter(Users.id == user_id).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {user}

@router.get('/get_user_active_accounts/{user_id}', status_code=status.HTTP_200_OK)
async def get_user_accounts(admin: user_dependency, db: db_dependency, user_id : int = Path(gt=0)):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    user = db.query(Users).filter(Users.id == user_id).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    accounts = db.query(Account).filter(Account.user_id == user_id, Account.is_active == True).all()
    return {"Accounts": accounts}

@router.get('/get_user_inactive_accounts/{user_id}', status_code=status.HTTP_200_OK)
async def get_user_inactive_accounts(admin: user_dependency, db: db_dependency, user_id : int = Path(gt=0)):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    user = db.query(Users).filter(Users.id == user_id).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    accounts = db.query(Account).filter(Account.user_id == user_id, Account.is_active == False).all()
    return {"Accounts": accounts}

@router.put('/reactive_user/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def reactive_user(admin: user_dependency, db: db_dependency, user_id : int = Path(gt=0)):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    user = db.query(Users).filter(Users.id == user_id).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active == True:
        raise HTTPException(status_code=400, detail="User is already active")
    user.is_active = True
    user.is_freeze = False
    user.status = "active"
    db.add(user)
    db.commit() 

@router.put('/reactive_user_account/', status_code=status.HTTP_204_NO_CONTENT)
async def reactive_user_account(user: user_dependency, db: db_dependency, user_username : str = Query(min_length=1), user_account_id : int = Query(gt=0)):
    if user.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    find_account = db.query(Account).filter(Users.username == user_username, Account.account_id == user_account_id).first() 
    if not find_account:
        raise HTTPException(status_code=404, detail="Account not found")
    if find_account.is_active == True:
        raise HTTPException(status_code=400, detail="Account is already active")
    find_account.is_active = True
    find_account.is_freeze = False
    find_account.status = "active"
    db.add(find_account)
    db.commit()

#Soft Delete
@router.delete('/delete_user', status_code=status.HTTP_204_NO_CONTENT)
async def delete_users(admin: user_dependency, db: db_dependency, username = Query(min_length=1)): 
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    delete_user = db.query(Users).filter(Users.username == username).first() 
    if not delete_user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user.is_active = False
    delete_user.is_freeze = False
    delete_user.delete_at = datetime.now(timezone.utc)
    db.add(delete_user)
    db.commit() 

@router.get('/get_system_stats', status_code=status.HTTP_200_OK)
async def get_system_status(admin: user_dependency, db: db_dependency):
    if admin.role != 'admin': 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the Admin can access this function")
    accounts = db.query(Account).all()
    total_balance = 0
    for account in accounts: 
        total_balance += account.balance
    return {"Total Balance": total_balance}

@router.post('/force_password_reset/{user_id}', status_code=status.HTTP_200_OK)
async def force_password_reset(user_id: int, admin: user_dependency, db: db_dependency):
    if admin.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.requires_password_change = True
    db.add(user)
    db.commit()
    return {"message": f"User {user.username} will be forced to change password on next login."}