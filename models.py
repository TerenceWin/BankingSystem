from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, unique=True, primary_key=True)
    full_name = Column(String, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    contact = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    
    role = Column(String, nullable=False)   #admin, manager, user
    requires_password_change = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_freeze = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)

class Account(Base):
    __tablename__ = 'account'

    account_id = Column(Integer, primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    account_name = Column(String, nullable=False)
    account_number = Column(String(16), unique=True)
    balance = Column(Numeric(precision=18, scale=2), default=0)
    type = Column(String, nullable=False)   #Saving, General, Credit, Loan
    status = Column(String) #acticve, inactive, pending, closed, frozen
    currency = Column(String(3), default="JPY")

    daily_limit = Column(Numeric(18, scale=2), default=50000.00)
    
    is_active = Column(Boolean, default=True)
    is_freeze = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
    deleted_at = Column(DateTime)


class Beneficiary(Base):
    __tablename__ = 'beneficiary'

    beneficiary_id = Column(Integer, primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    name = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    account_number = Column(String(16), nullable=False)
    category = Column(String, nullable=False)
    bank_detail = Column(String, default="")
    is_verified = Column(Boolean, default=False) 

    send_frequency = Column(Integer, default=0)
    last_use = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    

class Transaction(Base):
    __tablename__ = 'transaction'

    transaction_id = Column(Integer, primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    account_id = Column(Integer, ForeignKey('account.account_id'))

    type = Column(String, nullable=False)     #Transfer-In, Transfer-Out, Deposit, Withdrawal, [Fee, Interest, Refund, Adjustment]

    name = Column(String, nullable=False)
    amount = Column(Numeric(18, scale=2), nullable=False)
    description = Column(String, nullable=True)

    balance_after = Column(Numeric(18, scale=2), nullable=False)
    status = Column(String, nullable=False) #pending, completed, failed, deleted 

    sender_account = Column(String(16), nullable=True)
    receiver_account = Column(String(16), nullable=True)

    reference_number = Column(String(32), unique=True, index=True, nullable=False)
    related_reference = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime)
