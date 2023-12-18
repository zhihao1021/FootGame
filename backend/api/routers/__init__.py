from .game import router as game_router
from .oauth import router as oauth_router

routers = [
    game_router,
    oauth_router,
]
