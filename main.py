from fastapi import FastAPI
from src.core.logging import setup_logging
from src.core.config import config

from src.core.exceptions import setup_exception_handlers
from src.core.middlewares import UnifiedResponseMiddleware

from src.auth.router import router as auth_router
from src.dress.router import router as dress_router
from src.event.router import router as event_router
from src.media.router import router as media_router

setup_logging()

config.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=config.app_name)

setup_exception_handlers(app)
app.add_middleware(UnifiedResponseMiddleware)

app.include_router(auth_router)
app.include_router(dress_router)
app.include_router(event_router)
app.include_router(media_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/error")
async def error():
    raise Exception("serious error occurred")
