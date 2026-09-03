"""Web admin panel (sqladmin) for the livaishina bot.

Run by the `admin` docker-compose service:
    uvicorn admin.app:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views import DeadlineAdmin, UserAdmin
from bot.database.session import SessionMaker, engine
from config import settings


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == settings.ADMIN_LOGIN and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": settings.ADMIN_SECRET_KEY[:16]})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return bool(token) and token == settings.ADMIN_SECRET_KEY[:16]


def create_app() -> FastAPI:
    app = FastAPI(title="Livaishina Admin", docs_url=None, redoc_url=None)

    admin = Admin(
        app=app,
        engine=engine,
        session_maker=SessionMaker,
        authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY),
        base_url="/admin",
        title="Livaishina",
    )
    admin.add_view(UserAdmin)
    admin.add_view(DeadlineAdmin)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/admin")

    return app


app = create_app()
