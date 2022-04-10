from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models, schemas


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def read_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def read_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def read_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def delete_user(db: Session, user_id: id):
    rows = db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()
    return rows


def create_house(db: Session, house: schemas.HouseBase):
    db_house = models.House(**house.dict())
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house


def read_house_by_name(db: Session, name: str):
    return db.query(models.House).filter(models.House.name == name).first()


def read_houses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.House).offset(skip).limit(limit).all()


def update_house(db: Session, house_id: int, house: schemas.HouseBase):
    db.query(models.House).filter(models.House.id == house_id).update(house.dict())
    db.commit()
    return db.query(models.House).filter(models.House.id == house_id).first()


def create_house_member(db: Session, character: schemas.CharacterBase, house_id: int):
    db_character = models.Character(**character.dict(), house_id=house_id)
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


def delete_house(db: Session, house_id: id):
    rows = db.query(models.House).filter(models.House.id == house_id).delete()
    db.commit()
    return rows

