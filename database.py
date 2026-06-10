from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./backend.db"


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    import models as models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        user_columns = {
            row[1]
            for row in (
                await connection.execute(text("PRAGMA table_info(users)"))
            ).fetchall()
        }

        if "password_hash" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT '' NOT NULL")
            )

        # Add new user columns if missing
        for col, definition in [
            ("role",          "VARCHAR(20) NOT NULL DEFAULT 'normal_user'"),
            ("safety_status", "VARCHAR(20) NOT NULL DEFAULT 'unknown'"),
            ("latitude",      "FLOAT"),
            ("longitude",     "FLOAT"),
        ]:
            if col not in user_columns:
                await connection.execute(text(f"ALTER TABLE users ADD COLUMN {col} {definition}"))

        # safety_notifications migrations
        notif_result = await connection.execute(text("PRAGMA table_info(safety_notifications)"))
        notif_columns = {row[1] for row in notif_result.fetchall()}
        if notif_columns and "notification_type" not in notif_columns:
            await connection.execute(
                text("ALTER TABLE safety_notifications ADD COLUMN notification_type VARCHAR(20) NOT NULL DEFAULT 'alert'")
            )


async def seed_admin():
    from sqlalchemy import func, select

    import models as models
    from auth import hash_password

    async with SessionLocal() as db:
        result = await db.execute(
            select(models.User).where(models.User.role == "admin")
        )
        if result.scalars().first():
            return  # admin already exists

        admin = models.User(
            name="Admin",
            last_name="User",
            email="admin@disastertrack.com",
            age=30,
            phone_number="+1000000000",
            password_hash=hash_password("admin1234"),
            role="admin",
        )
        db.add(admin)
        await db.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db
