import pytest
from datetime import datetime, timezone
from typing import Optional

def test_equal_or_not_equal(): 
    assert 3 == 3
    assert 3 != 1

def test_is_instance(): 
    assert isinstance(3, int)
    assert not isinstance('3', int)   
    assert isinstance('String', str)
    assert isinstance(3, int)

def test_boolean(): 
    validate = True
    assert validate 
    assert validate is True
    assert ("Hello" == "world") is False

def test_type(): 
    assert type('Helo' is str)
    assert type(234 is int)

def test_greater_and_les_than(): 
    assert 3 < 10
    assert 7 > 2

def test_list(): 
    num_list = [1,2,3,4,5] 
    any_list = [False, False]
    assert 1 in num_list
    assert 7 not in num_list
    assert all(num_list)
    assert not any(any_list)


class User():
    def __init__(
        self,
        first_name: str,
        last_name: str,
        address: str,
        email: str,
        contact: str,
        username: str,
        hashed_password: str,
        role: str,
        requires_password_change: bool,
        is_active: bool,
        is_frozen: bool,
        created_at: datetime,
        deleted_at: Optional[datetime] = None,
        ):
            self.first_name = first_name
            self.last_name = last_name
            self.address = address
            self.email = email
            self.contact = contact
            self.username = username
            self.hashed_password = hashed_password
            self.role = role
            self.requires_password_change = requires_password_change
            self.is_active = is_active
            self.is_frozen = is_frozen
            self.created_at = created_at
            self.deleted_at = deleted_at
    

@pytest.fixture
def default_user():
    return User('Uchida', 'Terence', 'Tokyo Ukima 1-2-3', 'terence@gmail.com', \
                '09064953694', 'tj', 'blablabla', 'admin', False, True, False,\
                datetime.now(tz=timezone.utc))

def check_user_model(default_user):
    user = default_user
    assert user.first_name == 'Uchida',           'First Name should be Uchida'
    assert user.last_name == 'Terence',           'Last Name should be Terence'
    assert user.address == 'Tokyo Ukima 1-2-3',   'Address should be Tokyo Ukima 1-2-3'
    assert user.email == 'terence@gmail.com',      'Email should be terence@gmail.com'
    assert user.contact == '09064953694',          'Contact should be 09064953694'
    assert user.username == 'tj',                  'Username should be tj'
    assert user.hashed_password == 'blablabla',    'Hashed password should be blablabla'
    assert user.role == 'admin',                   'Role should be admin'
    assert user.requires_password_change == False, 'requires_password_change should be False'
    assert user.is_active == True,                 'is_active should be True'
    assert user.is_frozen == False,                'is_frozen should be False'
    assert isinstance(user.created_at, datetime),  'created_at should be a datetime instance'
    assert user.created_at.tzinfo is not None,     'created_at should be timezone-aware'
    assert user.deleted_at is None,                'deleted_at should be None by default'
