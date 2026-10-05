from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.patients import router as patients_router
from app.api.scans import router as scans_router
from app.api.reports import router as reports_router
from app.api.auth import router as auth_router
from app.api import benchmark

from app.api.workers import (
    router as worker_router,
    ws_router,
    ticket_router,
    analysis_worker,
)

from app.db.dependencies import get_async_db


logger = logging.getLogger("scanflow")
logging.basicConfig(level=logging.INFO)


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ScanFlow worker starting...")

    worker_task = asyncio.create_task(
        analysis_worker()
    )

    yield

    worker_task.cancel()

    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    print("ScanFlow worker stopping...")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ScanFlow API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def log_request(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID"
    )

    response = await call_next(request)

    logger.info(
        "request_id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )

    return response


# ============================================================
# HTTP EXCEPTION HANDLER
# ============================================================

async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {},
            }
        },
    )


# ============================================================
# VALIDATION EXCEPTION HANDLER
# ============================================================

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(
                    exc.errors()
                ),
            }
        },
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/healthz")
async def health_check(
    db: AsyncSession = Depends(get_async_db),
):
    await db.execute(
        text("SELECT 1")
    )

    return {
        "status": "ok",
        "database": "connected",
    }


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    patients_router
)

app.include_router(
    scans_router
)

app.include_router(
    reports_router
)

app.include_router(
    auth_router
)

app.include_router(
    benchmark.router
)

app.include_router(worker_router)
app.include_router(ws_router)
app.include_router(ticket_router)