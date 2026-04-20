from datetime import datetime, timezone

from fastapi import FastAPI, status
from enum import Enum
from ..models import Base, Account, Users
import pytest

def test_get_current_user_info(client, default_user): 
    response = client.get(
        "/user/get_user_info"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == default_user.id
    assert response.json()["username"] == default_user.username
    assert response.json()["email"] == default_user.email

def test_get_current_user_info_without_login(unauthorized_client): 
    response = unauthorized_client.get(
        "/user/get_user_info"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_update_user_info(client, db_session): 
    response = client.put(
        "/user/update_user_info",
        json = {
            "first_name": "Uchida",
            "last_name": "Terence", 
            "email": "terence@gmail.com", 
            "contact": "12345",
            "address" : "Tokyo Shibuya"
        } 
    )

    find_updated_account = db_session.query(Users).filter(Users.id == 1).first()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert find_updated_account.first_name == "Uchida"
    assert find_updated_account.last_name == "Terence"
    assert find_updated_account.email == "terence@gmail.com"
    assert find_updated_account.contact == "12345"
    assert find_updated_account.address == "Tokyo Shibuya"

def test_delete_user(authorized_regular_user, default_second_user, db_session):
    response = authorized_regular_user.delete(
        "/user/delete_user"
    )
    db_session.refresh(default_second_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert default_second_user.is_active == False


def test_delete_admin(authorized_admin, default_user):
    response = authorized_admin.delete(
        "/user/delete_user"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Admin and Manager accounts cannot be deleted."}
    assert default_user.is_active == True  

def test_change_password(authorized_user, default_second_user, db_session): 
    response = authorized_user.put(
        "/user/change_password", 
        json={
            "current_password": "tj123",
            "new_password": "tj1234"
        }
    )

    updated_user = db_session.query(Users).filter(Users.id == 2).first() 
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert updated_user.requires_password_change == False
