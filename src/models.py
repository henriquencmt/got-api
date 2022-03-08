from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    words = Column(String, index=True)
    description = Column(String, index=True)

    members = relationship("Character", back_populates="house")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    titles = Column(String, index=True)
    description = Column(String, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"))

    house = relationship("House", back_populates="members")
