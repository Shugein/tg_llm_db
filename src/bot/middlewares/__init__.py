from .auth import AuthMiddleware
from .logging import LoggingMiddleware
from .throttling import ThrottlingMiddleware

def setup_middlewares(dp):
    """Setup all middlewares"""
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(ThrottlingMiddleware())