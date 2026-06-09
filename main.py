from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from database import Base, engine
from routes.location import router as location_router
from routes.user import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(location_router)
