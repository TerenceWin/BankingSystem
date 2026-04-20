from datetime import datetime, timezone

from fastapi import status
from ..models import Base, Beneficiary, Account
import pytest


# ──────────────────────────────────────────────
# GET /beneficary/get_beneficiary
# ──────────────────────────────────────────────

def test_get_all_beneficiaries(client, default_user, default_beneficiary):
    response = client.get("/beneficary/get_beneficiary")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) > 0
    assert data[0]["name"] == default_beneficiary.name
    assert data[0]["bank_name"] == default_beneficiary.bank_name
    assert data[0]["account_number"] == default_beneficiary.account_number


def test_get_all_beneficiaries_empty(client, default_user):
    response = client.get("/beneficary/get_beneficiary")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data == []


# ──────────────────────────────────────────────
# GET /beneficary/check_recent_beneficiary
# ──────────────────────────────────────────────

def test_check_recent_beneficiary(client, default_user, default_beneficiary):
    response = client.get("/beneficary/check_recent_beneficiary")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "5 recent beneficiary" in data
    assert len(data["5 recent beneficiary"]) > 0


def test_check_recent_beneficiary_empty(client, default_user):
    response = client.get("/beneficary/check_recent_beneficiary")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "5 recent beneficiary" in data
    assert data["5 recent beneficiary"] == []


# ──────────────────────────────────────────────
# GET /beneficary/get_beneficiary/{beneficiary_id}
# ──────────────────────────────────────────────

def test_get_beneficiary_by_id(client, default_user, default_beneficiary):
    response = client.get("/beneficary/get_beneficiary/1")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "Beneficary" in data
    assert data["Beneficary"]["beneficiary_id"] == default_beneficiary.beneficiary_id
    assert data["Beneficary"]["name"] == default_beneficiary.name
    assert data["Beneficary"]["account_number"] == default_beneficiary.account_number


def test_get_beneficiary_by_id_not_found(client, default_user):
    response = client.get("/beneficary/get_beneficiary/99")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Beneficiary is not found"}


# ──────────────────────────────────────────────
# POST /beneficary/add_beneficiary
# ──────────────────────────────────────────────

def test_add_beneficiary(client, default_user):
    response = client.post(
        "/beneficary/add_beneficiary",
        json={
            "name": "New Beneficiary",
            "bank_name": "New Bank",
            "account_number": "9999999999999999",
            "category": "work",
            "bank_detail": "some bank detail"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"Message": "Successfully Added Beneficiary"}


def test_add_beneficiary_duplicate(client, default_user, default_beneficiary):
    response = client.post(
        "/beneficary/add_beneficiary",
        json={
            "name": "Jerry Win",
            "bank_name": "Another Bank",
            "account_number": "1234567890123457",
            "category": "family",
            "bank_detail": "some detail"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exist" in response.json()["detail"]


# ──────────────────────────────────────────────
# PUT /beneficary/update_beneficiary/{beneficiary_id}
# ──────────────────────────────────────────────

def test_update_beneficiary(client, default_user, default_beneficiary, db_session):
    response = client.put(
        "/beneficary/update_beneficiary/1",
        json={
            "name": "Updated Beneficiary",
            "bank_name": "Updated Bank",
            "account_number": "1234567890123457",
            "category": "business",
            "bank_detail": "updated bank detail"
        }
    )
    db_session.refresh(default_beneficiary)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert default_beneficiary.name == "Updated Beneficiary"
    assert default_beneficiary.bank_name == "Updated Bank"
    assert default_beneficiary.category == "business"
    assert default_beneficiary.bank_detail == "updated bank detail"


def test_update_beneficiary_not_found(client, default_user):
    response = client.put(
        "/beneficary/update_beneficiary/99",
        json={
            "name": "Ghost Beneficiary",
            "bank_name": "Ghost Bank",
            "account_number": "0000000000000000",
            "category": "other",
            "bank_detail": "none"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Beneficiary not found"}


# ──────────────────────────────────────────────
# DELETE /beneficary/delete_beneficiary/{beneficiary_id}
# ──────────────────────────────────────────────

def test_delete_beneficiary(client, default_user, default_beneficiary, db_session):
    response = client.delete("/beneficary/delete_beneficiary/1")
    deleted = db_session.query(Beneficiary).filter(Beneficiary.beneficiary_id == 1).first()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert deleted is None


def test_delete_beneficiary_not_found(client, default_user):
    response = client.delete("/beneficary/delete_beneficiary/99")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Beneficiary not found"}


# ──────────────────────────────────────────────
# POST /beneficary/transfer_balance
# ──────────────────────────────────────────────

def test_transfer_balance(client, default_user, default_beneficiary, default_account, second_default_account, db_session):
    response = client.post(
        "/beneficary/transfer_balance",
        params={"beneficiary_id": 1, "account_id": 1},
        json={"amount": 500, "description": "test transfer"}
    )
    db_session.refresh(default_account)
    db_session.refresh(second_default_account)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"Message": "Successfully Transferred Balance"}
    assert float(default_account.balance) == 600000.00 - 500
    assert float(second_default_account.balance) == 1000.00 + 500


def test_transfer_balance_beneficiary_not_found(client, default_user, default_account):
    response = client.post(
        "/beneficary/transfer_balance",
        params={"beneficiary_id": 99, "account_id": 1},
        json={"amount": 500, "description": "test transfer"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Beneficiary is not found"}


def test_transfer_balance_sender_account_not_found(client, default_user, default_beneficiary, default_account, second_default_account):
    response = client.post(
        "/beneficary/transfer_balance",
        params={"beneficiary_id": 1, "account_id": 99},
        json={"amount": 500, "description": "test transfer"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Sender account" in response.json()["detail"]


def test_transfer_balance_insufficient_funds(client, default_user, default_beneficiary, default_account, second_default_account):
    response = client.post(
        "/beneficary/transfer_balance",
        params={"beneficiary_id": 1, "account_id": 1},
        json={"amount": 9999999, "description": "too much"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Sender account" in response.json()["detail"]


def test_transfer_balance_exceeds_daily_limit(client, default_user, default_beneficiary, default_account, second_default_account):
    response = client.post(
        "/beneficary/transfer_balance",
        params={"beneficiary_id": 1, "account_id": 1},
        json={"amount": 99999, "description": "exceeds daily limit"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Sender account" in response.json()["detail"]
