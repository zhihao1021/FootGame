from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from asyncio import BaseEventLoop

from config import HOST, PORT, API_ROOT_PATH

from .routers import routers

app = FastAPI(
    version="0.1.0a",
    root_path=API_ROOT_PATH,
)

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)

async def run(loop: BaseEventLoop):
    config = Config(
        app=app,
        host=HOST,
        port=PORT,
        loop=loop
    )
    server = Server(config)
    await server.serve()
