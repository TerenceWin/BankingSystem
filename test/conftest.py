import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from passlib.context import CryptContext

from ..database import Base, sessionmaker, get_db
from ..main import app
from ..routers.auth import get_current_user
from ..models import Users, Account, Transaction, Beneficiary

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# def hash_password(password: str):
#     return bcrypt_context.hash(password)

def verify_password(username: str, password: str): 
    db = TestingSessionLocal() 
    user = db.query(Users).filter(Users.username == username).first() 
    return bcrypt_context.verify(password, user.hashed_password)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_admin():
    return Users(
        id=1,
        full_name="Uchida Terence",
        first_name="Uchida",
        last_name="Terence",
        address="Tokyo",
        email="anday312@gmail.com",
        contact="1234",
        username="tj",
        hashed_password="$2b$12$98Bg9pSU4IQz1PPAwFUud.XNhdzqRqIJhcK6L4RvQjuEbJVmSHUQS",
        role="admin",
        requires_password_change=False,
        is_active=True,
        is_freeze=False,
        created_at=None,
        deleted_at=None,
    )

def override_get_current_user(): 
    return Users(
        id=2,
        username="jj",
        full_name="Jerry Win",
        first_name="Jerry",
        last_name="Win",
        hashed_password="$2b$12$98Bg9pSU4IQz1PPAwFUud.XNhdzqRqIJhcK6L4RvQjuEbJVmSHUQS",
        role="user",
        is_active=True,
        is_freeze=False,
        requires_password_change=True,
        email="jerry@gmail.com",
        contact="1234567",
        address="New York",
        created_at=None, 
        deleted_at=None
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_admin

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def unauthorized_client(): 
    app.dependency_overrides.pop(get_current_user, None)
    yield TestClient(app)
    app.dependency_overrides[get_current_user] = override_get_current_admin

@pytest.fixture
def authorized_admin(): 
    app.dependency_overrides[get_current_user] = override_get_current_admin
    yield TestClient(app)
    app.dependency_overrides[get_current_user] = override_get_current_admin

@pytest.fixture
def authorized_user():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides[get_current_user] = override_get_current_admin

def override_get_current_regular_user():
    return Users(
        id=2,
        username="jj",
        full_name="Jerry Win",
        first_name="Jerry",
        last_name="Win",
        hashed_password="$2b$12$98Bg9pSU4IQz1PPAwFUud.XNhdzqRqIJhcK6L4RvQjuEbJVmSHUQS",
        role="user",
        is_active=True,
        is_freeze=False,
        requires_password_change=False,  # Already changed password
        email="jerry@gmail.com",
        contact="1234567",
        address="New York",
        created_at=None,
        deleted_at=None
    )

@pytest.fixture
def authorized_regular_user():
    app.dependency_overrides[get_current_user] = override_get_current_regular_user
    yield TestClient(app)
    app.dependency_overrides[get_current_user] = override_get_current_admin

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def default_user(db_session):
    user = Users(
        id=1,
        username="tj",
        full_name="Uchida Terence",
        first_name="Uchida",
        last_name="Terence",
        hashed_password="$2b$12$98Bg9pSU4IQz1PPAwFUud.XNhdzqRqIJhcK6L4RvQjuEbJVmSHUQS",
        role="admin",
        is_active=True,
        is_freeze=False,
        requires_password_change=False,
        email="anday312@gmail.com",
        contact="1234",
        address="Tokyo",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def default_second_user(db_session):
    user = Users(
        id=2,
        username="jj",
        full_name="Jerry Win",
        first_name="Jerry",
        last_name="Win",
        hashed_password="$2b$12$98Bg9pSU4IQz1PPAwFUud.XNhdzqRqIJhcK6L4RvQjuEbJVmSHUQS",
        role="user",
        is_active=True,
        is_freeze=False,
        requires_password_change=True,
        email="jerry@gmail.com",
        contact="1234567",
        address="New York",
        created_at=datetime.now(timezone.utc),
    ) 
    db_session.add(user)
    db_session.commit() 
    return user 

@pytest.fixture
def default_account(default_user, db_session):
    account = Account(
        account_id=1,
        user_id=default_user.id,
        account_name="account1",
        account_number="1234567890123456",
        balance=600000.00,
        type="saving",
        status="active",
        currency="JPY",
        daily_limit=50000.00,
        is_active=True,
        is_freeze=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()
    return account

@pytest.fixture
def second_default_account(default_user, db_session):
    account = Account(
        account_id=2,
        user_id=default_user.id,
        account_name="account2",
        account_number="1234567890123457",
        balance=1000.00,
        type="saving",
        status="active",
        currency="JPY",
        daily_limit=50000.00,
        is_active=True,
        is_freeze=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()
    return account

@pytest.fixture
def third_default_account(default_user, db_session):
    account = Account(
        account_id=3,
        user_id=default_user.id,
        account_name="account3",
        account_number="1234567890123458",
        balance=1000.00,
        type="credit",
        status="active",
        currency="JPY",
        daily_limit=50000.00,
        is_active=False,
        is_freeze=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(account)
    db_session.commit()
    return account

@pytest.fixture
def default_beneficiary(default_user, db_session):
    beneficiary = Beneficiary(
        beneficiary_id=1,
        user_id=default_user.id,
        name="Jerry Win",
        bank_name="Test Bank",
        account_number="1234567890123457",
        category="family",
        bank_detail="Test bank detail",
        is_verified=True,
        send_frequency=0,
        last_use=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(beneficiary)
    db_session.commit()
    return beneficiary

@pytest.fixture
def default_transaction(default_account, db_session):
    transaction = Transaction(
        transaction_id=1,
        user_id=1,
        account_id=1,
        amount=100.00,
        name="test_deposit",
        type="deposit",
        status="completed",
        description="testing deposit",
        balance_after=1100,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        sender_account=None,
        receiver_account=None,
        reference_number="93b76661a009d9faf89f08bd3a341288",
        related_reference=None,
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction
