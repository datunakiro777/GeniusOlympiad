from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models as models
from database import get_db
from email_service import send_alert_email, send_rescue_email
from routes.user import get_current_user_from_token

router = APIRouter()


class BroadcastRequest(BaseModel):
    notification_type: Literal["alert", "rescue"] = "alert"


class AlertRequest(BaseModel):
    notification_type: Literal["alert", "rescue"] = "alert"


def require_admin_or_police(current_user: models.User):
    if current_user.role not in ("admin", "police"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


async def send_email(user: models.User, notification_type: str):
    name = f"{user.name} {user.last_name}"
    coords = (
        f"{user.latitude:.5f}, {user.longitude:.5f}"
        if user.latitude is not None
        else "Unknown"
    )
    if notification_type == "rescue":
        await send_rescue_email(user.email, name, coords)
    else:
        await send_alert_email(user.email, name)


@router.post("/broadcast")
async def broadcast_safety_check(
    body: BroadcastRequest,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    require_admin_or_police(current_user)

    result = await db.execute(select(models.User).where(models.User.id != current_user.id))
    users = result.scalars().all()

    for user in users:
        notif = models.SafetyNotification(
            user_id=user.id,
            notification_type=body.notification_type,
        )
        db.add(notif)
        user.safety_status = "unknown"
        await send_email(user, body.notification_type)

    await db.commit()
    return {"sent_to": len(users), "notification_type": body.notification_type}


@router.post("/alert/{user_id}")
async def send_targeted_alert(
    user_id: int,
    body: AlertRequest,
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    require_admin_or_police(current_user)

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    notif = models.SafetyNotification(
        user_id=user_id,
        notification_type=body.notification_type,
    )
    db.add(notif)
    target.safety_status = "unknown"
    await send_email(target, body.notification_type)

    await db.commit()
    return {"ok": True, "notification_type": body.notification_type}


@router.get("/users/map")
async def get_map_users(
    current_user: Annotated[models.User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "name": f"{u.name} {u.last_name}",
            "email": u.email,
            "phone_number": u.phone_number,
            "role": u.role,
            "safety_status": u.safety_status,
            "latitude": u.latitude,
            "longitude": u.longitude,
        }
        for u in users
    ]
