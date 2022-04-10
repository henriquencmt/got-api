from contextlib import contextmanager
from typing import List

import pytest

from src import crud, models, schemas
from src.database import engine, SessionLocal


models.Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.close()


@pytest.fixture
def user():
    user = schemas.UserCreate(email='test@domain.com', password='secret')
    with get_db() as db:
        test_user = crud.create_user(db=db, user=user)
        yield db, test_user
        crud.delete_user(db=db, user_id=test_user.id)


@pytest.fixture
def house():
    house = schemas.HouseBase(name='Test House', words='Words', description='Description')
    with get_db() as db:
        test_house = crud.create_house(db=db, house=house)
        yield db, test_house
        crud.delete_house(db=db, house_id=test_house.id)


def test_create_user(user):
    _, test_user = user
    assert isinstance(test_user, models.User)
    assert test_user.is_active == True
    assert crud.verify_password('secret', test_user.hashed_password) == True


def test_read_user(user):
    db, test_user = user
    db_user = crud.read_user(db=db, user_id=test_user.id)
    assert db_user.is_active == True
    assert db_user.email == 'test@domain.com'
    assert crud.verify_password('secret', db_user.hashed_password) == True


def test_read_user_by_email(user):
    db, _ = user
    db_user = crud.read_user_by_email(db=db, email='test@domain.com')
    assert db_user.is_active == True
    assert crud.verify_password('secret', db_user.hashed_password) == True


def test_read_users(user):
    db, _ = user
    db_users = crud.read_users(db)
    assert isinstance(db_users, List)
    assert isinstance(db_users[0], models.User)


def test_delete_user(user):
    db, test_user = user
    rows = crud.delete_user(db, test_user.id)
    assert rows == 1


def test_create_house(house):
    _, test_house = house
    assert isinstance(test_house, models.House)
    assert isinstance(test_house.members, List)
    assert test_house.name == 'Test House'
    assert test_house.words == 'Words'
    assert test_house.description == 'Description'


def test_create_house_member(house):
    db, test_house = house
    character = schemas.CharacterBase(name='Test Character')
    test_character = crud.create_house_member(db, character, test_house.id)
    assert isinstance(test_character, models.Character)
    assert isinstance(test_character.house, models.House)
    assert test_character.name == 'Test Character'
    assert test_character.house.name == 'Test House'


def test_delete_house(house):
    db, test_house = house
    rows = crud.delete_house(db, test_house.id)
    assert rows == 1
