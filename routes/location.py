from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db
from schemas import UserLocationHistoryResponse


router = APIRouter()


@router.get("", response_model=list[UserLocationHistoryResponse])
async def get_all_locations(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.UserLocationHistory))
    locations = result.scalars().all()
    return locations


@router.get("/{id}", response_model=UserLocationHistoryResponse)
async def get_location(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.UserLocationHistory).where(models.UserLocationHistory.id == id))
    location = result.scalars().first()

    if location:
        return location
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="location not found")


@router.get("/users/{id}/locations", response_model=list[UserLocationHistoryResponse])
async def get_user_locations(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    result = await db.execute(
        select(models.UserLocationHistory).where(models.UserLocationHistory.user_id == id)
    )
    locations = result.scalars().all()
    return locations
