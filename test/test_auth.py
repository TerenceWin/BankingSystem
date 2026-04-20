from datetime import datetime, timedelta, timezone
from enum import Enum

from Banking_system.test.conftest import verify_password
from ..routers.auth import SECRET_KEY, ALGORITHM, create_access_token
from jose import jwt, JWTError
from fastapi import status
import pytest

class Role(str, Enum): 
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class New_user_request():
    def __init__(
        self,
        first_name: str,
        last_name: str,
        address: str,
        email: str,
        contact: str,
        username: str,
        password: str,
        role: str,
    ):    
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.contact = contact
        self.username = username
        self.password = password
        self.role = role

@pytest.fixture
def default_new_user(): 
    return New_user_request("Jack", "Melody", "jack@gmail.com", "09064953694", "Tokyo", "jj", "jj123", "user")

def test_new_user_request_model(default_new_user):
    user = default_new_user
    assert isinstance(user.first_name, str)
    assert isinstance(user.last_name, str)
    assert isinstance(user.email, str)
    assert isinstance(user.contact, str)
    assert isinstance(user.address, str)
    assert isinstance(user.username, str)
    assert isinstance(user.password, str)
    assert isinstance(user.role, str)


def test_add_new_user(client): 
    response = client.post(
        "/auth/", 
        json={
            "username": "jj", 
            "first_name" : "Jack", 
            "last_name" : "Melody",
            "full_name": "Jack Melody",
            "email": "jack@gmail.com",
            "address" : "Tokyo", 
            "contact" : "123456", 
            "password" : "jj123", 
            "role": "user", 
            "is_active": True,
        }, 
    )
    assert response.json() == {"message": "User created successfully."}
    assert response.status_code == status.HTTP_201_CREATED

def test_add_new_invalid_user(client):
    response = client.post(
        "/auth/", 
        json={
            "username": 123, 
            "first_name" : "Jack", 
            "last_name" : "Melody",
            "full_name": "Jack Melody",
            "email": "jack@gmail.com",
            "address" : "Tokyo", 
            "contact" : "123456", 
            "password" : "jj123", 
            "role": "user", 
            "is_active": True,
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

def test_add_existing_user(client, default_user): 
    response = client.post(
        "/auth/", 
        json={
            "username": "tj", 
            "first_name" : "Uchida", 
            "last_name" : "Terence",
            "full_name": "Uchida Terence",
            "email": "anday312@gmail.com",
            "address" : "Tokyo", 
            "contact" : "1234", 
            "password" : "tj123", 
            "role": "admin", 
            "is_active": True,
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.fixture
def default_login_info(): 
    return {"username": "tj", "password": "tj123", "role" : "admin", "id": 1}

def test_login_user_with_token(client, default_user, default_login_info): 
    response = client.post(
        "/auth/token", 
        data={
            "username": default_login_info["username"], 
            "password": default_login_info["password"],
        }
    )
    
    verify = verify_password(default_login_info["username"], default_login_info["password"])
    print(verify)
    assert response.status_code == status.HTTP_200_OK
    assert verify == True
    assert response.json().get("token_type") == "bearer"

def test_create_access_token(): 
    username = "username"
    id = 1
    role = "admin"
    expires = timedelta(minutes=20) 
    token = create_access_token(username, id, role, expires)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token.get('sub') == username
    assert decoded_token.get('id') == id
    assert decoded_token.get('role') == role
