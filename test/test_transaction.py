from fastapi import status
import pytest


def test_get_transactions_authenticated(client, default_user, default_account, default_transaction):
    response = client.get("/transaction/get_transaction/1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "test_deposit"


def test_get_transactions_account_not_found(client, default_user):
    response = client.get("/transaction/get_transaction/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_deposit_transaction(client, default_user, default_account):
    response = client.post(
        "/transaction/add_transaction/1",
        json={
            "name": "salary",
            "amount": 500,
            "description": "monthly salary",
            "type": "deposit",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_add_withdrawal_transaction(client, default_user, default_account):
    response = client.post(
        "/transaction/add_transaction/1",
        json={
            "name": "rent",
            "amount": 200,
            "description": "monthly rent",
            "type": "withdrawal",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_add_withdrawal_insufficient_balance(client, default_user, default_account):
    response = client.post(
        "/transaction/add_transaction/1",
        json={
            "name": "big expense",
            "amount": 9999999,
            "description": "too much",
            "type": "withdrawal",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_add_transfer_missing_receiver(client, default_user, default_account):
    response = client.post(
        "/transaction/add_transaction/1",
        json={
            "name": "transfer",
            "amount": 100,
            "type": "transfer_out",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_add_deposit_account_not_found(client, default_user):
    response = client.post(
        "/transaction/add_transaction/999",
        json={
            "name": "deposit",
            "amount": 100,
            "type": "deposit",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_add_tranfer_with_receiver(client, default_user, default_account, second_default_account): 
    response = client.post(
        "/transaction/add_transaction/1", 
        json={
            "name": "transfer", 
            "amount": 200, 
            "type": "transfer_out",
            "receiver_account": second_default_account.account_number
        },
    )
    assert response.status_code == status.HTTP_201_CREATED