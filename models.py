from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    current_location: Mapped[str] = mapped_column(String(100), default="Unknown")
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="normal_user", nullable=False)
    safety_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    location_history: Mapped[list[UserLocationHistory]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[SafetyNotification]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserLocationHistory(Base):
    __tablename__ = "user_location_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    user: Mapped[User] = relationship(back_populates="location_history")


class SafetyNotification(Base):
    __tablename__ = "safety_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(20), default="alert", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped[User] = relationship(back_populates="notifications")
