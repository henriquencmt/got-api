from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import engine, get_db


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def read_root():
    return "Valar Morghulis"


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.read_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.read_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.read_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/houses/", response_model=schemas.House)
def create_house(house: schemas.HouseBase, db: Session = Depends(get_db)):
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
def update_house(house_name: str, house: schemas.HouseBase, db: Session = Depends(get_db)):
    db_house = crud.read_house_by_name(db, name=house_name)
    if db_house:
        return crud.update_house(db=db, house_id=db_house.id, house=house)
    raise HTTPException(status_code=404, detail="House not found")    


@app.post("/houses/{house_id}/members/", response_model=schemas.Character)
def create_member_for_house(
    house_id: int, character: schemas.CharacterBase, db: Session = Depends(get_db)
):
    return crud.create_house_member(db=db, character=character, house_id=house_id)
