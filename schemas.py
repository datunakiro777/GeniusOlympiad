from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LocationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=20)
    last_name: str = Field(min_length=2, max_length=20)
    age: int = Field(gt=0, lt=100)
    email: EmailStr = Field(max_length=120)
    phone_number: str = Field(min_length=7, max_length=20)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_location: str


class UserLocationHistoryBase(BaseModel):
    user_id: int = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class UserLocationHistoryCreate(UserLocationHistoryBase):
    pass


class UserLocationHistoryResponse(UserLocationHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class UserPrivate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr = Field(max_length=120)
    password_hash: str
