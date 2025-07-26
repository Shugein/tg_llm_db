from .commands import router as commands_router
from .messages import router as messages_router
from .callbacks import router as callbacks_router

def setup_routers():
    """Setup all routers"""
    return [
        commands_router,
        messages_router, 
        callbacks_router
    ]