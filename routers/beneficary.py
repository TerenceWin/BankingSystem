from fastapi import APIRouter, Path, Depends, HTTPException, Query
from ..database import db_dependency
from typing import Annotated, Optional
from pydantic import BaseModel, Field
from starlette import status 
from .auth import get_current_user
from ..models import Account, Beneficiary, Transaction
from .user import Users 
from enum import Enum
from datetime import datetime, timezone
import secrets

router = APIRouter(
    prefix  = '/beneficary',
    tags = ['beneficary']
)

user_dependency = Annotated[Users, Depends(get_current_user)]

class Status(str, Enum): 
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted" 

class BeneficiaryRequest(BaseModel): 
    name: str = Field(min_length = 1)
    bank_name: str = Field(min_length = 3)
    account_number: str = Field(min_length=16, max_length=16)
    category: str = Field(min_length=1)
    bank_detail: str 

class Transaction_Request(BaseModel):
    amount: int = Field(gt=0)
    description : str = Field(default="", max_length=100)


@router.get("/get_beneficiary", status_code=status.HTTP_200_OK)
async def get_all_beneficary(user: user_dependency, db: db_dependency): 
    return db.query(Beneficiary).filter(Beneficiary.user_id == user.id).all() 

@router.get("/check_recent_beneficiary", status_code=status.HTTP_200_OK)
async def check_recent_beneficiary(user: user_dependency, db: db_dependency): 
    recent_transaction = db.query(Beneficiary)\
        .filter(Beneficiary.user_id == user.id)\
        .order_by(Beneficiary.last_use.desc())\
        .limit(5)\
        .all() 
    return {"5 recent beneficiary": recent_transaction}

@router.get("/get_beneficiary/{beneficiary_id}", status_code=status.HTTP_200_OK)
async def get_beneficiary(user: user_dependency, db: db_dependency, beneficiary_id : int = Path(gt=0)): 
    find_beneficiary = db.query(Beneficiary).filter(Beneficiary.user_id == user.id,Beneficiary.beneficiary_id == beneficiary_id).first()
    if find_beneficiary is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary is not found")
    return {"Beneficary" : find_beneficiary}

def prepare_beneficiary_model(user: user_dependency, db: db_dependency, beneficiary: BeneficiaryRequest): 
    existing = db.query(Beneficiary).filter(Beneficiary.user_id == user.id and Beneficiary.account_number == beneficiary.account_number or Beneficiary.name == beneficiary.name).first()
    if existing is not None: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The Beneficiary already exist. It's name is " + existing.name)
    beneficiary_model = Beneficiary(
        **beneficiary.model_dump(),
        user_id = user.id, 
        is_verified = True,
        last_use = datetime.now(timezone.utc)
    )
    beneficiary_model.created_at = datetime.now(timezone.utc)
    return beneficiary_model

@router.post("/add_beneficiary", status_code=status.HTTP_201_CREATED)
async def add_beneficiary(user: user_dependency, db: db_dependency, beneficiary_request : BeneficiaryRequest):
    user_exist= prepare_beneficiary_model(user, db, beneficiary_request)
    db.add(user_exist)
    db.commit() 
    return {"Message" : "Successfully Added Beneficiary"}

@router.put("/update_beneficiary/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_beneficiary(user: user_dependency, db: db_dependency,beneficiary_request : BeneficiaryRequest, beneficiary_id : int = Path(gt=0)): 
    find_beneficiary = db.query(Beneficiary).filter(Beneficiary.user_id == user.id, Beneficiary.beneficiary_id == beneficiary_id).first() 
    if find_beneficiary is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")
    find_beneficiary.name = beneficiary_request.name
    find_beneficiary.bank_name = beneficiary_request.bank_name
    find_beneficiary.account_number = beneficiary_request.account_number
    find_beneficiary.category = beneficiary_request.category
    find_beneficiary.bank_detail = beneficiary_request.bank_detail
    find_beneficiary.last_use = datetime.now(timezone.utc)
    db.add(find_beneficiary)
    db.commit() 

@router.delete("/delete_beneficiary/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_beneficiary(user: user_dependency, db: db_dependency, beneficiary_id : int = Path(gt=0)):     
    find_beneficiary =  db.query(Beneficiary).filter(Beneficiary.user_id == user.id, Beneficiary.beneficiary_id == beneficiary_id).first()
    if find_beneficiary is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")
    db.delete(find_beneficiary)
    db.commit() 

def create_beneficiary_transfer_in_transaction(reference_number: str, transaction_request: Transaction_Request,
    sender_account: Account, receiver_account: Account, transfer_out_transaction: Transaction, db):

    transfer_in_model = Transaction(
        user_id = receiver_account.user_id,
        account_id = receiver_account.account_id,
        name = "Banking TRANSFER-IN",
        amount = transaction_request.amount,
        balance_after = receiver_account.balance,
        status = Status.COMPLETED,
        sender_account = sender_account.account_number,
        receiver_account = receiver_account.account_number,
        description = transaction_request.description,
        reference_number = secrets.token_hex(16),
        related_reference = reference_number,
        type = "transfer_in",
        created_at = datetime.now(timezone.utc),
        completed_at = datetime.now(timezone.utc)
    )
    transfer_out_transaction.completed_at = datetime.now(timezone.utc)
    transfer_out_transaction.status = Status.COMPLETED
    db.add(transfer_in_model)
    return True



@router.post("/transfer_balance", status_code=status.HTTP_200_OK)
async def transfer_balance(user: user_dependency, db: db_dependency, transaction_request: Transaction_Request,
    beneficiary_id: int = Query(gt=0), account_id: int = Query(gt=0)):

    reference_number = secrets.token_hex(16)

    # Validate beneficiary first before using it to query receiver_account
    beneficiary = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if beneficiary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary is not found")
    if not beneficiary.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Beneficiary is not verified yet")

    sender_account = db.query(Account).filter(
        Account.account_id == account_id,
        Account.user_id == user.id,
        Account.is_active == True,
        Account.is_freeze == False,
        Account.balance >= transaction_request.amount,
        Account.daily_limit >= transaction_request.amount
    ).first()

    receiver_account = db.query(Account).filter(
        Account.account_number == beneficiary.account_number,
        Account.is_active == True
    ).first()

    if sender_account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender account is not found. It may be inactive, frozen, or you don't have enough balance.")
    if receiver_account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver account is not found. It may be inactive or frozen.")

    transfer_out_model = Transaction(
        user_id = user.id,
        account_id = sender_account.account_id,
        name = "Banking TRANSFER-OUT",
        amount = transaction_request.amount,
        description = transaction_request.description,
        status = Status.PENDING,
        sender_account = sender_account.account_number,
        receiver_account = receiver_account.account_number,
        reference_number = reference_number,
        created_at = datetime.now(timezone.utc),
        type = "transfer_out"
    )

    try:
        sender_account.balance -= transaction_request.amount
        sender_account.daily_limit -= transaction_request.amount
        receiver_account.balance += transaction_request.amount
        transfer_out_model.balance_after = sender_account.balance

        if not create_beneficiary_transfer_in_transaction(
            reference_number = reference_number,
            transaction_request = transaction_request,
            sender_account = sender_account,
            receiver_account = receiver_account,
            transfer_out_transaction = transfer_out_model,
            db = db
        ):
            raise ValueError("Transfer-in transaction failed.")

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during transfer: {str(e)}"
        )

    if transfer_out_model.status in (Status.COMPLETED, Status.FAILED):
        transfer_out_model.completed_at = datetime.now(timezone.utc)

    db.add(transfer_out_model)
    db.commit()
    return {"Message": "Successfully Transferred Balance"}

#Check Beneficiary if it exist, account_number and bank_name
#Get /beneficiary/recent (5 beneficiarys) 
#Allow Transaction with beneficiary 