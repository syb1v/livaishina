"""Web admin panel (sqladmin) for the livaishina bot.

Run by the `admin` docker-compose service:
    uvicorn admin.app:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import base64
import json

from itsdangerous import TimestampSigner
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from admin.stats import router as stats_router
from admin.views import DeadlineAdmin, ScheduleAdmin, UserAdmin
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


class StatsAuthMiddleware(BaseHTTPMiddleware):
    """Protect custom /admin/stats page with the same session auth as sqladmin."""

    async def dispatch(self, request: StarletteRequest, call_next):
        if request.url.path.rstrip("/") == "/admin/stats":
            ok = False
            cookie = request.cookies.get("session")
            if cookie:
                try:
                    signer = TimestampSigner(settings.ADMIN_SECRET_KEY)
                    payload = signer.unsign(cookie, max_age=14 * 24 * 3600)
                    data = json.loads(base64.urlsafe_b64decode(payload))
                    ok = data.get("token") == settings.ADMIN_SECRET_KEY[:16]
                except Exception:
                    ok = False
            if not ok:
                return RedirectResponse(url="/admin/login", status_code=302)
        return await call_next(request)


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
    admin.add_view(ScheduleAdmin)
    app.state.admin = admin

    app.add_middleware(StatsAuthMiddleware)
    app.include_router(stats_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/admin")

    return app


app = create_app()
