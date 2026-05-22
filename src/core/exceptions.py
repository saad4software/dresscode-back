from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def common_exception_handler(request: Request, exc: Exception):
    status_code = 400
    message = str(exc)

    # Check if it's a Starlette/FastAPI HTTPException
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        message = exc.detail

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None
        }
    )

def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(StarletteHTTPException, common_exception_handler)
    app.add_exception_handler(RequestValidationError, common_exception_handler)
    app.add_exception_handler(Exception, common_exception_handler)
