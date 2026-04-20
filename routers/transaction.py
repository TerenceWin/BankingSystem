from fastapi import APIRouter, Path, Depends, HTTPException, Query
from ..database import db_dependency
from typing import Annotated, Optional
from pydantic import BaseModel, Field, model_validator
from starlette import status 
from .auth import get_current_user
from ..models import Account, Transaction
from datetime import datetime, timezone, timedelta
from enum import Enum
from .user import Users
import secrets

router = APIRouter(
    prefix="/transaction",
    tags=["transaction"]
)

user_dependency = Annotated[Users, Depends(get_current_user)]

class Transaction_type(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_OUT = "transfer_out"

class Status(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"

class Transaction_Request(BaseModel):
    name: str = Field(min_length=1)
    amount: int = Field(gt=0)
    receiver_account : Optional[str] = Field(default=None,min_length=16, max_length=16)
    description : str = Field(default="", max_length=100)
    type : Transaction_type   #Deposit, Withdrawal, Transfer-In, Transfer-Out

    @model_validator(mode="after")
    def check_receiver_required_for_transfer(self):
        if self.type == Transaction_type.TRANSFER_OUT and self.receiver_account is None:
            raise ValueError("receiver_account is required for transfer")
        return self

class Transaction_Update_Request(BaseModel):
    status : Status    #pending, completed, failed, deleted

def create_transfer_in_trasaction(reference_number: str, transaction_request: Transaction_Request, 
    sender_account: Account, receiver_account: Account, transfer_out_transaction: Transaction, user, db): 

    transfer_in_model = Transaction(
        user_id = user.id, 
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

@router.post("/add_transaction/{account_id}", status_code=status.HTTP_201_CREATED)
async def add_transaction(user: user_dependency, db: db_dependency,
    transaction_request : Transaction_Request,  account_id: int = Path(gt=0)):
    reference_number = secrets.token_hex(16)
    
    transaction_model = Transaction(
        **transaction_request.model_dump(),
        user_id = user.id,
        account_id = account_id,
        reference_number = reference_number,
        created_at = datetime.now(timezone.utc),
        status = Status.PENDING
    )
    if transaction_model.type == Transaction_type.DEPOSIT: 
        deposit_account = db.query(Account).filter(Account.account_id == account_id, Account.is_active == True).first() 
        if deposit_account is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The account you trying to deposit is not found. ")
        deposit_account.balance += transaction_model.amount
        transaction_model.balance_after = deposit_account.balance
        transaction_model.status = Status.COMPLETED
        transaction_model.receiver_account = "" 

    elif transaction_model.type == Transaction_type.WITHDRAWAL: 
        withdrawal_account = db.query(Account).filter(Account.account_id == account_id, Account.is_active == True).first() 
        if withdrawal_account is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The account you trying to withdrawal is not found. ")
        if withdrawal_account.balance < transaction_model.amount: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You don't have enough money to Withdrawal from this account. ")
        withdrawal_account.daily_limit -= transaction_model.amount
        withdrawal_account.balance -= transaction_model.amount
        transaction_model.balance_after = withdrawal_account.balance
        transaction_model.status = Status.COMPLETED
        transaction_model.receiver_account = "" 

    elif transaction_model.type == Transaction_type.TRANSFER_OUT: 
        sender_account = db.query(Account)\
            .filter(Account.user_id == user.id, Account.account_id == account_id, Account.is_active == True, 
                    Account.is_freeze == False, Account.balance >= transaction_model.amount,
                    Account.daily_limit >= transaction_model.amount).first() 
        receiver_account = db.query(Account)\
            .filter(Account.account_number == transaction_model.receiver_account, 
                    Account.is_active == True).first() 
        
        if sender_account is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The sender account is not found. It may be inactive, frozen or you don't have enough balance. ")
        if receiver_account is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The receiver account is not found. It may be inactive or frozen. ")
        if sender_account.account_number == receiver_account.account_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sender account and receiver account cannot be the same. ")
        if sender_account.balance < transaction_model.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance.")
        try: 
            transaction_model.sender_account = sender_account.account_number
            sender_account.balance -= transaction_model.amount
            sender_account.daily_limit -= transaction_model.amount
            receiver_account.balance += transaction_model.amount
            transaction_model.balance_after = sender_account.balance
        
            if not create_transfer_in_trasaction(reference_number=reference_number, 
                                                 transaction_request= transaction_request, 
                                                 sender_account=sender_account, receiver_account=receiver_account, 
                                                 transfer_out_transaction=transaction_model,
                                                 user=user, db=db): 
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

    
    if transaction_model.status in (Status.COMPLETED,Status.FAILED): 
        transaction_model.completed_at = datetime.now(timezone.utc)
    
    db.add(transaction_model)
    db.commit() 
    return {"Message" : "Successfully Added Transaction"}


@router.get("/get_transaction/{account_id}", status_code=status.HTTP_200_OK)
async def get_transaction(user: user_dependency, db: db_dependency, account_id : int = Path(gt=0)): 
    account = db.query(Account).filter(Account.user_id == user.id, Account.account_id == account_id,
                                       Account.is_active == True).first()
    if account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return db.query(Transaction).filter(Transaction.account_id == account_id).all()

@router.get("/get_transaction/{transaction_id}", status_code=status.HTTP_200_OK)
async def get_transaction_by_id(user: user_dependency, db: db_dependency, transaction_id : int = Path(gt=0)):
    transaction = db.query(Transaction).filter(Transaction.user_id == user.id, Transaction.transaction_id == transaction_id).first() 
    if transaction is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction is not found with given User ID and Transaction ID")
    return {"Transaction" : transaction}

@router.put("/update_transaction_status/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_transaction_status(user: user_dependency, db: db_dependency, transaction_update_request : Transaction_Update_Request, transaction_id : int = Path(gt=0)):
    account = db.query(Account).filter(Account.user_id == user.id).first() 
    if account is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    transaction = db.query(Transaction).filter(Transaction.account_id == account.account_id, Transaction.transaction_id == transaction_id).first() 
    if transaction is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction is not found with given ID")
    if transaction.status == Status.COMPLETED or transaction.status == Status.FAILED or transaction.status == Status.DELETED: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed or Failed transaction cannot be updated")
    transaction.status = transaction_update_request.status
    db.add(transaction)
    db.commit() 

    if transaction_update_request.status == Status.COMPLETED: 
        if transaction.type == Transaction_type.DEPOSIT: 
            account.balance += transaction.amount
        elif transaction.type == Transaction_type.WITHDRAWAL:
            if account.balance < transaction.amount: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")
            account.balance -= transaction.amount
    db.add(account)
    db.commit()
    return {"Message" : "Successfully Updated Transaction"}

@router.delete("/delete_transaction/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(user: user_dependency, db: db_dependency, transaction_id : int = Path(gt=0)): 
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first() 
    if transaction is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction is not found with given ID")
    transaction.status = Status.DELETED
    if transaction.type == Transaction_type.DEPOSIT:
        account = db.query(Account).filter(Account.account_id == transaction.account_id, Account.user_id == transaction.user_id).first() 
        account.balance -= transaction.amount
        db.add(account)
    elif transaction.type == Transaction_type.WITHDRAWAL: 
        account = db.query(Account).filter(Account.account_id == transaction.account_id, Account.user_id == transaction.user_id).first() 
        account.balance += transaction.amount
        db.add(account)
    elif transaction.type == Transaction_type.TRANSFER_OUT: 
        if transaction.type == Transaction_type.TRANSFER_OUT: 
            sender = db.query(Account).filter(Account.account_number == transaction.sender_account).first() 
            receiver = db.query(Account).filter(Account.account_number == transaction.receiver_account).first() 
            transfer_in_transaction = db.query(Transaction).filter(Transaction.related_reference == transaction.related_reference).first() 
            transfer_in_transaction.status = Status.DELETED
            sender += transaction.amount
            receiver -= transaction.amount
            db.add(transfer_in_transaction)
            db.add(sender)
            db.add(receiver)

            
#Update Transaction status to Completed or Failed 
#transfer_in have related_reference, transfer_out have reference_number
    db.add(transaction)
    db.commit() 


