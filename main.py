from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import uvicorn

from app.src.routes import auth, users
from app.src.conf.config import settings


app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix='/api')


@app.on_event("startup")
async def startup() -> None:
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port,
                          db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
def read_root() -> dict:
    return {"PhotoShare": "FastAPI group project"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
