from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db
from schemas import UserCreate, UserResponse


router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return users


@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@router.post("/CreateUser", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")

    new_user = models.User(
        name=user.name,
        last_name=user.last_name,
        email=user.email,
        age=user.age,
        phone_number=user.phone_number,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
