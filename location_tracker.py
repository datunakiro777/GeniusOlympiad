from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from threading import Event

from database import SessionLocal
from models import LocationHistory, User


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float


LocationProvider = Callable[[int], Location | Awaitable[Location]]


def save_user_location(user_id: int, location: Location) -> None:
    """Save the user's latest location and append one history row."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            raise ValueError(f"User with id {user_id} does not exist")

        user.current_location = f"{location.latitude},{location.longitude}"
        db.add(
            LocationHistory(
                user_id=user_id,
                latitude=location.latitude,
                longitude=location.longitude,
            )
        )
        db.commit()


async def track_user_location(
    user_id: int,
    location_provider: LocationProvider,
    *,
    interval_seconds: int = 180,
    stop_event: Event | None = None,
) -> None:
    """
    Track one user's location every 3 minutes by default.

    The location_provider must get coordinates from a consent-based source,
    such as your frontend browser geolocation API or a mobile app location update.
    """
    while stop_event is None or not stop_event.is_set():
        location_result = location_provider(user_id)
        location = (
            await location_result
            if inspect.isawaitable(location_result)
            else location_result
        )

        save_user_location(user_id, location)
        await asyncio.sleep(interval_seconds)
