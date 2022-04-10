from contextlib import contextmanager
from typing import List

import pytest

from fastapi.testclient import TestClient

from src import crud, schemas
from src.database import SessionLocal
from src.main import app, get_current_user


def override_get_current_user():
    return schemas.User(email='test@mail.com', id=1, is_active=True, scopes='houses:read')


client = TestClient(app)

@app.on_event("shutdown")
def shutdown_event():
    app.dependency_overrides[get_current_user] = override_get_current_user
    client.delete('/users/1')
    client.delete('/houses/1')
    app.dependency_overrides = {}


@contextmanager
def get_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.close()


@pytest.fixture
def user():
    user = schemas.UserCreate(email='test@mail.com', password='secret')
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


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Valar Morghulis"


def test_login_without_credentials():
    response = client.post("/login")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "username"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            },
            {
                "loc": [
                    "body",
                    "password"
                ],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }


def test_login_with_wrong_credentials():
    body = {'username': 'test@mail.com', 'password': 'sekret'}
    response = client.post("/login", data=body)
    assert response.status_code == 401
    assert response.json() == { "detail": "Incorrect username or password" }


def test_login(user):
    _, test_user = user
    body = {'username': test_user.email, 'password': 'secret'}
    response = client.post("/login", data=body)
    assert response.status_code == 200
    assert response.json()['token_type'] == "bearer"


def test_create_user_without_credentials():
    body = {'email': 'new_test@mail.com', 'password': 'secret'}
    response = client.post("/users/", json=body) 
    assert response.status_code == 401
    assert response.json() == { "detail": "Not authenticated" }


def test_create_user_with_already_registered_email(user):
    app.dependency_overrides[get_current_user] = override_get_current_user

    _, test_user = user
    body = {'email': test_user.email, 'password': 'secret'}
    response = client.post("/users/", json=body)
    assert response.status_code == 400
    assert response.json() == {'detail': 'Email already registered'}

    app.dependency_overrides = {}


def test_create_user_with_invalid_token():
    headers = {'Authorization': 'Bearer invalidtoken'}
    body = {'email': 'test@mail.com', 'password': 'secret'}
    response = client.post("/users/", json=body, headers=headers)
    assert response.status_code == 401
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_create_user():
    with TestClient(app) as client:
        app.dependency_overrides[get_current_user] = override_get_current_user

        body = {'email': 'new_test@mail.com', 'password': 'secret'}
        response = client.post("/users/", json=body)
        new_user = response.json()
        assert response.status_code == 201
        assert new_user['email'] == 'new_test@mail.com'
        assert new_user['id'] == 1
        assert new_user['is_active'] == True

        app.dependency_overrides = {}


def test_delete_user_without_permission(user):
    _, test_user = user
    response = client.delete(f"/users/{test_user.id}")
    assert response.status_code == 401


def test_delete_user(user):
    app.dependency_overrides[get_current_user] = override_get_current_user

    _, test_user = user
    response = client.delete(f"/users/{test_user.id}")
    assert response.status_code == 204
    assert response.json() == 1

    app.dependency_overrides = {}


def test_create_house_without_permission():
    house = {'name': 'Test House', 'words': 'Words', 'description': 'Description'}
    response = client.post(f"/houses/", json=house)
    assert response.status_code == 401


def test_create_house():
    with TestClient(app) as client:
        app.dependency_overrides[get_current_user] = override_get_current_user

        house = {'name': 'Test House', 'words': 'Words', 'description': 'Description'}

        response = client.post(f"/houses/", json=house)
        new_house = response.json()
        assert response.status_code == 201
        assert new_house['name'] == 'Test House'
        assert new_house['words'] == 'Words'
        assert new_house['description'] == 'Description'

        app.dependency_overrides = {}


def test_read_houses():
    response = client.get('/houses/')
    assert response.status_code == 200
    assert isinstance(response.json(), List)


def test_read_house(house):
    _, test_house = house
    response = client.get(f'/houses/{test_house.name}')
    read_house = response.json()
    assert response.status_code == 200
    assert read_house['id'] == test_house.id
    assert read_house['name'] == test_house.name
    assert read_house['words'] == test_house.words
    assert read_house['description'] == test_house.description


def test_update_house_without_permission(house):
    _, test_house = house
    new_data = {'name': 'New Name', 'words': 'New Words', 'description': 'New Description'}
    response = client.put(f'/houses/{test_house.name}', json=new_data)
    assert response.status_code == 401


def test_update_house(house):
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    _, test_house = house
    new_data = {'name': 'New Name', 'words': 'New Words', 'description': 'New Description'}
    response = client.put(f'/houses/{test_house.name}', json=new_data)
    updated_house = response.json()
    assert response.status_code == 200
    assert updated_house['id'] == test_house.id
    assert updated_house['name'] == new_data['name']
    assert updated_house['words'] == new_data['words']
    assert updated_house['description'] == new_data['description']

    app.dependency_overrides = {}


def test_delete_house_without_permission(house):
    _, test_house = house
    response = client.delete(f'/houses/{test_house.id}')
    assert response.status_code == 401


def test_delete_house(house):
    app.dependency_overrides[get_current_user] = override_get_current_user

    _, test_house = house
    response = client.delete(f'/houses/{test_house.id}')
    assert response.status_code == 204
    assert response.json() == 1

    app.dependency_overrides = {}


def test_create_member_for_house_without_permission(house):
    _, test_house = house
    member = {'name': 'Member', 'titles': 'Title', 'description': 'Description'}
    response = client.post(f'/houses/{test_house.id}/members/', json=member)
    assert response.status_code == 401


def test_create_member_for_house(house):
    app.dependency_overrides[get_current_user] = override_get_current_user

    _, test_house = house
    member = {'name': 'Member', 'titles': 'Title', 'description': 'Description'}
    response = client.post(f'/houses/{test_house.id}/members/', json=member)
    created = response.json()
    assert response.status_code == 201
    assert created['name'] == member['name']
    assert created['titles'] == member['titles']
    assert created['description'] == member['description']

    app.dependency_overrides = {}
