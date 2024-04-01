import uvicorn
import redis.asyncio as redis

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.src.routes import auth, users, photos, comments
from app.src.conf.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Rate limit for FastAPI. New scheme instead of deprecated "on_event" 
    Args:
        app (FastAPI): FastAPI application name
    '''
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix='/api')
app.include_router(photos.router, prefix="/api")
app.include_router(comments.router, prefix="/api")

cors_origins = [ 
    "*"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> dict:
    '''
    Dummy URL for request without path and parameters
    '''
    return {"PhotoShare": "FastAPI group project"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
