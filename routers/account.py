from fastapi import APIRouter, Depends, Path, HTTPException, Body, Query
from ..database import db_dependency
from typing import Annotated
from .auth import get_current_user
from pydantic import BaseModel, Field
from starlette import status 
from ..models import Account, Transaction
import secrets
from enum import Enum
from .user import Users
from datetime import datetime, timezone

router = APIRouter(
    prefix = '/account',
    tags = ['account']
)

user_dependency = Annotated[Users, Depends(get_current_user)]

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CLOSED = "closed"
    FROZEN = "frozen"

class Type(str, Enum):
    SAVING = "saving"
    GENERAL = "general"
    CREDIT = "credit"
    LOAN = "loan"

class Account_Request(BaseModel):
    account_name: str = Field(min_length=1)
    balance: float = Field(lt=1000000)
    type: Type
    status: Status

@router.get("/get_accounts", status_code=status.HTTP_200_OK)
async def get_all_accounts(user: user_dependency, db: db_dependency): 
    return db.query(Account).filter(Account.user_id == user.id).all() 

@router.get("/get_active_accounts", status_code=status.HTTP_200_OK)
async def get_active_accounts(user: user_dependency, db: db_dependency): 
    return db.query(Account).filter(Account.user_id == user.id).filter(Account.is_active == True).all()

@router.get("/get_accounts/{account_id}", status_code=status.HTTP_200_OK)
async def get_account_by_id(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0)):
    account = db.query(Account).filter(Account.account_id == account_id, Account.user_id == user.id).first() 
    if account is None: 
        raise HTTPException(status_code=404, detail="Account is not found with given ID")
    return {"Account" : account}

@router.get("/get_accounts_by_account_number/{account_number}", status_code=status.HTTP_200_OK)
async def get_account_by_account_number(user: user_dependency, db: db_dependency, account_number : str = Path(min_length=16, max_length=16)):
    account = db.query(Account).filter(Account.account_number == account_number, Account.user_id == user.id).first() 
    if account is None: 
        raise HTTPException(status_code=404, detail="Account is not found with given account number")
    return {"Account" : account}

@router.get("/get_accounts_by_account_name/{account_name}", status_code=status.HTTP_200_OK)
async def get_account_by_account_name(user: user_dependency, db: db_dependency, account_name : str = Path(min_length=1)):
    accounts = db.query(Account).filter(Account.account_name == account_name, Account.user_id == user.id).first() 
    if not accounts: 
        raise HTTPException(status_code=404, detail="Account is not found with given account name")
    return {"Account" : accounts}

def get_unique_account_number(user: user_dependency, db): 
    accounts = db.query(Account).filter(Account.user_id == user.id).all() 
    existing_numbers = {account.account_number for account in accounts}
    
    while True:
        temp_number = secrets.randbelow(10**16 - 10**15) + 10**15
        if temp_number not in existing_numbers:
            return temp_number

@router.post("/add_account", status_code=status.HTTP_201_CREATED)
async def add_account(user: user_dependency, db: db_dependency, account_request: Account_Request):
    account_number = get_unique_account_number(user=user, db=db)
    account_model = Account(
        **account_request.model_dump(), 
        user_id = user.id, 
        account_number = account_number
    )

    if account_model.status == Status.FROZEN: 
        account_model.is_freeze = True
        account_model.is_active = False
    elif account_model.status == Status.ACTIVE: 
        account_model.is_freeze = False
        account_model.is_active = True
    elif account_model.status == Status.INACTIVE or account_model.status== Status.CLOSED or account_model.status == Status.PENDING: 
        account_model.is_freeze = False
        account_model.is_active = False
    
    account_model.created_at = datetime.now(timezone.utc)
    db.add(account_model)
    db.commit() 
    return {'Message': 'Successfully added account'}

@router.put("/update_account/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_account(user: user_dependency, db: db_dependency, account: Account_Request, account_id : int = Path(gt=0)):
    find_account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id).first()
    if find_account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    find_account.account_name = account.account_name
    find_account.balance = account.balance
    find_account.type = account.type
    find_account.status = account.status
    if account.status == Status.FROZEN:
        find_account.is_freeze = True
        find_account.is_active = True
    elif account.status == Status.ACTIVE:
        find_account.is_freeze = False
        find_account.is_active = True
    elif account.status == Status.INACTIVE or account.status == Status.CLOSED or account.status == Status.PENDING:
        find_account.is_freeze = False
        find_account.is_active = False
    db.add(find_account)
    db.commit() 

@router.patch('/update_account_status/{account_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_account_status(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0), new_status : Status = Body()):
    find_account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id).first() 
    if find_account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    find_account.status = new_status
    if new_status == Status.FROZEN: 
        find_account.is_freeze = True
        find_account.is_active = True
    elif new_status == Status.ACTIVE: 
        find_account.is_freeze = False
        find_account.is_active = True
    elif new_status == Status.INACTIVE or new_status == Status.CLOSED or new_status == Status.PENDING: 
        find_account.is_freeze = False
        find_account.is_active = False
    db.add(find_account)
    db.commit()

@router.patch('/update_account_name/{account_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_account_name(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0), new_name : str = Body(min_length=1)):
    find_account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id).first() 
    if find_account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    find_account.account_name = new_name
    db.add(find_account)
    db.commit()



@router.delete('/freeze_account/{account_id}', status_code=status.HTTP_204_NO_CONTENT)
async def freeze_account(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0)): 
    find_account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id).first() 
    if find_account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    find_account.status = Status.FROZEN
    find_account.is_freeze = True
    find_account.is_active = True
    find_account.status = Status.FROZEN
    db.add(find_account)
    db.commit()

@router.delete('/delete_account/{account_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0)): 
    find_account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id).first() 
    if find_account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    find_account.status = Status.INACTIVE
    find_account.is_freeze = False
    find_account.is_active = False
    db.add(find_account)
    db.commit() 

@router.get("/get_all_account_balance", status_code=status.HTTP_200_OK)
async def get_all_account_balance(user: user_dependency, db: db_dependency): 
    total = 0 
    accounts = db.query(Account).filter(Account.user_id == user.id).all() 
    for account in accounts: 
        total += account.balance
    return {"Total Balance" : total } 
    
@router.get("/get_transaction_history/{account_id}", status_code=status.HTTP_200_OK)
async def get_transactions_history(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0)): 
    account = db.query(Account).filter(Account.account_id == account_id).first() 
    if account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Account not found")
    return db.query(Transaction).filter(Transaction.account_id == account_id, Transaction.user_id == user.id ).all() 
    
@router.get('/check_daily_limit/{account_id}', status_code=status.HTTP_202_ACCEPTED)
async def check_daily_limit(user: user_dependency, db: db_dependency, account_id: int = Path(gt=0)): 
    account =  db.query(Account).filter(Account.account_id == account_id, Account.user_id == user.id).first()
    if account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if account.type != Type.CREDIT: 
        if account.balance < account.daily_limit:
            return {"Daily Limit": account.balance}
    return {"Daily Limit": account.daily_limit}
    


    #Create an Account
    #Get all accounts detail
    #Get all active accounts 
    #Get account by account_id 
    #Get account by account_number
    #Get account by account_name
    #Update Status of the Account [Patch]
    #Update Account Name [Patch]
    #Soft Delete Account

    #Get total Balance from all accounts current user holds 
    #Get All Transactions History  within this account

    #Freeze Account, require Admin to unfreeze
    #Check daily limits, 
