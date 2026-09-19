from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.patients import router as patients_router
from app.api.scans import router as scans_router
from app.api.reports import router as reports_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="ScanFlow API",
    version="1.0.0",
)


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
                "details": exc.errors(),
            }
        },
    )


app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)


app.include_router(patients_router)
app.include_router(scans_router)
app.include_router(reports_router)
app.include_router(auth_router)