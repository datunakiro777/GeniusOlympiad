from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

import models as models
from database import engine, get_db, init_db, seed_admin
from routes.admin import router as admin_router
from routes.location import router as location_router
from routes.user import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    await seed_admin()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(location_router, prefix="/api", tags=["locations"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


@app.get("/", include_in_schema=False, name="home")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"title": "Home"})


@app.get("/login", include_in_schema=False, name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"title": "Login"})


@app.get("/register", include_in_schema=False, name="register_page")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"title": "Register"})


@app.get("/map", include_in_schema=False, name="map_page")
async def map_page(request: Request):
    return templates.TemplateResponse(request, "map.html", {"title": "Live Map"})


@app.get("/admin", include_in_schema=False, name="admin_page")
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin_panel.html", {"title": "Admin Panel"})


@app.get("/police", include_in_schema=False, name="police_page")
async def police_page(request: Request):
    return templates.TemplateResponse(request, "police_panel.html", {"title": "Police Dispatch"})


@app.get("/users", include_in_schema=False, name="users_page")
async def users_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).order_by(models.User.id.desc()))
    users = result.scalars().all()
    return templates.TemplateResponse(request, "users.html", {"users": users, "title": "Users"})


@app.get("/users/{user_id}", include_in_schema=False, name="user_page")
async def user_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    result = await db.execute(
        select(models.UserLocationHistory)
        .where(models.UserLocationHistory.user_id == user_id)
        .order_by(models.UserLocationHistory.timestamp.desc())
    )
    locations = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user.html",
        {"user": user, "locations": locations, "title": f"{user.name} {user.last_name}"},
    )


@app.get("/locations", include_in_schema=False, name="locations_page")
async def locations_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.UserLocationHistory).order_by(models.UserLocationHistory.timestamp.desc())
    )
    locations = result.scalars().all()
    return templates.TemplateResponse(
        request, "locations.html", {"locations": locations, "title": "Locations"}
    )


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)
    message = exception.detail or "An error occurred."
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exception.status_code, "title": exception.status_code, "message": message},
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Invalid request.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
