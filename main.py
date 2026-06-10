from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from database import engine, init_db
from routes.location import router as location_router
from routes.user import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(location_router, prefix="/locations", tags=["locations"])
