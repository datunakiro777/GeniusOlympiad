from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, Session
import models
from database import Base, get_db, engine
from typing import Annotated
from sqlalchemy import select
from schemas import UserCreate, UserLocationHistoryResponse, UserResponse
from fastapi import HTTPException, status, Depends, APIRouter, FastAPI

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/users", response_model = list[UserResponse])
def get_all_users(db : Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User))
    users = result.scalars().all()
    return users


@app.get("/users/{id}", response_model = UserResponse)
def get_user(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@app.get("/locations", response_model=list[UserLocationHistoryResponse])
def get_all_locations(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.UserLocationHistory))
    locations = result.scalars().all()
    return locations


@app.get("/locations/{id}", response_model=UserLocationHistoryResponse)
def get_location(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.UserLocationHistory).where(models.UserLocationHistory.id == id))
    location = result.scalars().first()

    if location:
        return location
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="location not found")


@app.get("/users/{id}/locations", response_model=list[UserLocationHistoryResponse])
def get_user_locations(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    result = db.execute(
        select(models.UserLocationHistory).where(models.UserLocationHistory.user_id == id)
    )
    locations = result.scalars().all()
    return locations


@app.post("/CreateUser", response_model= UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db : Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='email already exists')

    new_user = models.User(
        name = user.name,
        last_name = user.last_name,
        email = user.email,
        age = user.age,
        phone_number = user.phone_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
