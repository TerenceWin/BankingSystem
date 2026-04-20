from datetime import datetime, timezone

from fastapi import FastAPI, status
from enum import Enum
from ..models import Base, Account
import pytest

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CLOSED = "closed"
    FROZEN = "frozen"

def test_get_all_accounts(client, default_user, default_account, second_default_account, third_default_account): 
    responses = client.get("/account/get_accounts")
    data = responses.json()
    assert len(data) > 0
    assert responses.status_code == status.HTTP_200_OK

def test_get_all_active_accounts(client, default_user, default_account, second_default_account, third_default_account): 
    responses = client.get("/account/get_active_accounts")
    data = responses.json() 
    assert len(data) > 0
    assert responses.status_code == status.HTTP_200_OK

def test_get_account_by_id(client, default_user, second_default_account): 
    response = client.get("/account/get_accounts/2")
    data = response.json() 
    assert len(data) == 1
    assert response.status_code == status.HTTP_200_OK
    assert data["Account"]["account_name"] == "account2"
    assert data["Account"]["account_number"] == "1234567890123457"
    assert data["Account"]["balance"] == 1000.00

def test_get_account_by_acount_number(client, default_user, second_default_account): 
    response = client.get("/account/get_accounts_by_account_number/1234567890123457")
    data = response.json() 
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert data["Account"]["account_name"] == "account2"
    assert data["Account"]["balance"] == 1000.00

def test_get_account_by_account_name(client, default_user, second_default_account): 
    response = client.get("/account/get_accounts_by_account_name/account2")
    data = response.json() 
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert data["Account"]["account_number"] == "1234567890123457"
    assert data["Account"]["balance"] == 1000.00

def test_add_account(client, default_user): 
    response = client.post(
        "/account/add_account", 
        json={
            "user_id" : default_user.id,
            "account_id" : 4,
            "account_name": "test_account", 
            "account_number": "test--1234567890", 
            "balance": 1000.00,
            "type": "saving",
            "status": "active",
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'Message': 'Successfully added account'}

def test_update_account_by_id(client, default_user, second_default_account, db_session ):
    response = client.put(
        "/account/update_account/2", 
        json={
            "account_name": "updated_account2", 
            "balance": 2000.00,
            "type": "general",
            "status": "inactive",
        }
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.account_name == "updated_account2"
    assert find_updated_account.balance == 2000.00
    assert find_updated_account.type == "general"
    assert find_updated_account.status == "inactive"


def test_update_account_by_id_not_found(client, default_user, second_default_account, db_session ):
    response = client.put(
        "/account/update_account/4", 
        json={
            "account_name": "updated_account2", 
            "balance": 2000.00,
            "type": "general",
            "status": "inactive",
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}

def test_update_account_status_to_active_by_id(client, default_user, second_default_account, db_session):
    response = client.patch(
        "/account/update_account_status/2", 
        json = Status.ACTIVE.value)
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.status == "active"
    assert find_updated_account.is_freeze == False
    assert find_updated_account.is_active == True

def test_update_account_status_to_frozen_by_id(client, default_user, second_default_account, db_session):
    response = client.patch(
        "/account/update_account_status/2", 
        json = Status.FROZEN.value
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.status == "frozen"
    assert find_updated_account.is_freeze == True
    assert find_updated_account.is_active == True

def test_update_account_status_to_inactive_by_id(client, default_user, second_default_account, db_session):
    response = client.patch(
        "/account/update_account_status/2", 
        json = Status.INACTIVE.value
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.status == "inactive"
    assert find_updated_account.is_freeze == False
    assert find_updated_account.is_active == False

def test_update_account_status_to_pending_by_id(client, default_user, second_default_account, db_session): 
    response = client.patch(
        "/account/update_account_status/2",
        json = Status.PENDING.value
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    find_updated_account.status == "pending"
    find_updated_account.is_active == False
    find_updated_account.is_freeze == False

def test_update_account_status_to_closed_by_id(client, default_user, second_default_account, db_session): 
    response = client.patch(
        "/account/update_account_status/2",
        json = Status.CLOSED.value
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    find_updated_account.status == "closed"
    find_updated_account.is_active == False
    find_updated_account.is_freeze == False

def test_update_account_status_to_frozen_by_id_not_found(client, default_user, second_default_account):
    response = client.patch(
        "/account/update_account_status/4", 
        json = Status.FROZEN.value
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}

def test_update_account_name_by_id(client, default_user, second_default_account, db_session): 
    response = client.patch(
        "/account/update_account_name/2",
        json="new_account2_name"
    )
    find_updated_account = db_session.query(Account).filter(Account.user_id == default_user.id, Account.account_id == 2).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.account_name == "new_account2_name"

def test_update_account_name_by_id_not_found(client, default_user, second_default_account):
    response = client.patch(
        "/account/update_account_name/4",
        json="new_account4_name"
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND   
    assert response.json() == {"detail" : "Account not found"}

def test_freeze_account_by_id(client, default_user, second_default_account, db_session):
    response = client.delete("/account/freeze_account/2")

    find_updated_account = db_session.query(Account).filter(
        Account.user_id == default_user.id, 
        Account.account_id == 2
    ).first()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.status == Status.FROZEN
    assert find_updated_account.is_freeze == True
    assert find_updated_account.is_active == True

def test_freeze_account_by_id_not_found(client, default_user, second_default_account):
    response = client.delete("/account/freeze_account/99")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}

def test_delete_account_by_id(client, default_user, second_default_account, db_session):
    response = client.delete("/account/delete_account/2")

    find_updated_account = db_session.query(Account).filter(
        Account.user_id == default_user.id, 
        Account.account_id == 2
    ).first()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.status == Status.INACTIVE
    assert find_updated_account.is_freeze == False
    assert find_updated_account.is_active == False

def test_delete_account_by_id_not_found(client, default_user, second_default_account):
    response = client.delete("/account/delete_account/99")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}

def test_get_all_account_balance(client, default_user, default_account, second_default_account):
    response = client.get("/account/get_all_account_balance")

    expected_total = default_account.balance + second_default_account.balance
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"Total Balance": expected_total}


def test_get_all_account_balance_no_accounts(client, default_user):
    response = client.get("/account/get_all_account_balance")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"Total Balance": 0}

def test_get_account_transaction_history_by_id(client, default_transaction): 
    response = client.get(
        "/account/get_transaction_history/1"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0

def test_get_account_transaction_history_by_id_not_found(client, default_transaction): 
    response = client.get(
        "/account/get_transaction_history/2"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}
    
#Non-credit account, with balance >= daily_limit => Return daily_limit amount
def test_get_daily_limit_of_non_credit_account_by_id(client, default_account): 
    response = client.get(
        "/account/check_daily_limit/1"
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "Daily Limit" in response.json()
    assert response.json().get("Daily Limit") == default_account.daily_limit

#Non-credit account, with balance < daily_limit => Return Balance amount
def test_get_balance_of_non_credit_account_by_id(client, second_default_account): 
    response = client.get(
        "/account/check_daily_limit/2"
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "Daily Limit" in response.json()
    assert response.json().get("Daily Limit") == second_default_account.balance

#Credit account => Return daily_limit
def test_get_daily_limit_of_credit_account_by_id(client, third_default_account): 
    response = client.get(
        "/account/check_daily_limit/3"
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "Daily Limit" in response.json()
    assert response.json().get("Daily Limit") == third_default_account.daily_limit

#Account not found by id while testing for daily limit
def test_get_daily_limit_by_id_not_found(client, default_account): 
    response = client.get(
        "/account/check_daily_limit/99"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Account not found"}