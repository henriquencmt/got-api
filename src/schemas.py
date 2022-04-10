from typing import List, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    scopes: str

    class Config:
        orm_mode = True


class CharacterBase(BaseModel):
    name: str
    titles: Optional[str] = None
    description: Optional[str] = None


class Character(CharacterBase):
    id: int
    house_id: int

    class Config:
        orm_mode = True


class HouseBase(BaseModel):
    name: str
    words: Optional[str] = None
    description: Optional[str] = None
    

class House(HouseBase):
    id: int
    members: List[Character]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
