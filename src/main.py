import os

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes
)
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import engine, get_db


SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
ALGORITHM = os.environ.get('ALGORITHM') or 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES') or 15)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={
        "users:read": "Read users.",
        "users:write": "Write users.",
        "houses:read": "Read houses.",
        "houses:write": "Write houses."
    }
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_user(db: Session, email: str):
    user = crud.read_user_by_email(db, email)
    return user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if user is None:
        return False
    if not crud.verify_password(password, user.hashed_password):
        return False
    return user
 

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", []).split(sep=' ')
        token_data = schemas.TokenData(username=username, scopes=token_scopes)
    except JWTError:
        raise credentials_exception
    except ValidationError:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value}
            )
    user = get_user(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    if user.is_active:
        return user
    raise HTTPException(status_code=400, detail="Inactive user")


@app.get("/")
def read_root():
    return "Valar Morghulis"

# TODO: Change the way scopes are being added to the token
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(
        data={"sub": user.email, "scopes": user.scopes}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User, status_code=201)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["users:write"])
):
    if crud.read_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["users:write"])
):
    deleted = crud.delete_user(db, user_id=user_id)
    return deleted


@app.post("/houses/", response_model=schemas.House, status_code=201)
def create_house(
    house: schemas.HouseBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["houses:write"])
):
    db_house = crud.read_house_by_name(db, name=house.name)
    if db_house:
        raise HTTPException(status_code=400, detail="House already registered")
    return crud.create_house(db=db, house=house)


@app.get("/houses/", response_model=List[schemas.House])
def read_houses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    houses = crud.read_houses(db, skip=skip, limit=limit)
    return houses


@app.get("/houses/{house_name}", response_model=schemas.House)
def read_house(house_name: str, db: Session = Depends(get_db)):
    db_house = crud.read_house_by_name(db, name=house_name)
    if db_house is None:
        raise HTTPException(status_code=404, detail="House not found")
    return db_house


@app.put("/houses/{house_name}", response_model=schemas.House)
def update_house(
    house_name: str,
    house: schemas.HouseBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["houses:write"])
):
    db_house = crud.read_house_by_name(db, name=house_name)
    if db_house:
        return crud.update_house(db=db, house_id=db_house.id, house=house)
    raise HTTPException(status_code=404, detail="House not found")    


@app.delete("/houses/{house_id}", status_code=204)
def delete_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["houses:write"])
):
    deleted = crud.delete_house(db, house_id=house_id)
    return deleted


@app.post("/houses/{house_id}/members/", response_model=schemas.Character, status_code=201)
def create_member_for_house(
    house_id: int,
    character: schemas.CharacterBase,
    db: Session = Depends(get_db),
    current_user: schemas.User = Security(get_current_user, scopes=["houses:write"])
):
    return crud.create_house_member(db=db, character=character, house_id=house_id)
