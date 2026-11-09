from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import Settings
from app.core.security import require_access
from app.db.session import make_engine
from app.routers.discovery import router as discovery
from app.routers.tracker import router
from app.routers.workflows import router as workflows, public_router


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        with engine.connect() as conn:
            conn.execute(text("SELECT version_num FROM alembic_version"))
        yield
        engine.dispose()

    app = FastAPI(title="Graduate application tracker", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.engine = engine

    @app.middleware("http")
    async def private_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Pydantic's default errors echo submitted personal data; return locations only.
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": error["loc"], "type": error["type"], "msg": "Invalid field value"}
            for error in exc.errors()
        ]})

    @app.get("/health")
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}

    app.include_router(router, prefix="/api", dependencies=[Depends(require_access)])
    app.include_router(workflows, prefix="/api", dependencies=[Depends(require_access)])
    app.include_router(discovery, prefix="/api", dependencies=[Depends(require_access)])
    app.include_router(public_router)
    return app
