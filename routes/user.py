from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import models as models
from auth import (
    create_access_token,
    hash_password,
    oauth2_scheme,
    verify_access_token,
    verify_password,
)
from database import get_db
from schemas import RoleUpdate, SafetyStatusUpdate, Token, UserCreate, UserPublic

router = APIRouter()


async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(models.User).where(models.User.id == user_id_int))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("", response_model=list[UserPublic])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User))
    return result.scalars().all()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@router.post("/CreateUser", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == func.lower(user.email))
    )
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")

    # First registered user becomes admin
    count_result = await db.execute(select(func.count()).select_from(models.User))
    user_count = count_result.scalar()
    role = "admin" if user_count == 0 else "normal_user"

    new_user = models.User(
        name=user.name,
        last_name=user.last_name,
        email=user.email,
        age=user.age,
        phone_number=user.phone_number,
        password_hash=hash_password(user.password),
        role=role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == form_data.username.lower())
    )
    user = result.scalars().first()
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: Annotated[models.User, Depends(get_current_user_from_token)]):
    return current_user


@router.patch("/me/safety-status", response_model=UserPublic)
async def update_my_safety_status(
    body: SafetyStatusUpdate,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    current_user.safety_status = body.safety_status
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.patch("/me/location", response_model=UserPublic)
async def update_my_location(
    body: dict,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from schemas import LocationRequest
    loc = LocationRequest(**body)
    current_user.latitude = loc.latitude
    current_user.longitude = loc.longitude
    current_user.current_location = f"{loc.latitude:.5f}, {loc.longitude:.5f}"
    # Save to history
    history = models.UserLocationHistory(
        user_id=current_user.id,
        latitude=loc.latitude,
        longitude=loc.longitude,
    )
    db.add(history)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/notifications")
async def get_my_notifications(
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.SafetyNotification)
        .where(
            models.SafetyNotification.user_id == current_user.id,
            models.SafetyNotification.status == "pending",
        )
        .order_by(models.SafetyNotification.sent_at.desc())
    )
    notifications = result.scalars().all()
    return [{"id": n.id, "sent_at": n.sent_at.isoformat(), "notification_type": n.notification_type} for n in notifications]


@router.post("/me/notifications/{notification_id}/respond")
async def respond_to_notification(
    notification_id: int,
    body: SafetyStatusUpdate,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from datetime import UTC, datetime

    result = await db.execute(
        select(models.SafetyNotification).where(
            models.SafetyNotification.id == notification_id,
            models.SafetyNotification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.status = "responded"
    notif.responded_at = datetime.now(UTC)
    current_user.safety_status = body.safety_status
    await db.commit()
    return {"ok": True}


@router.patch("/{user_id}/role", response_model=UserPublic)
async def update_user_role(
    user_id: int,
    body: RoleUpdate,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = body.role
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/{id}", response_model=UserPublic)
async def get_user(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
