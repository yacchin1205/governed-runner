from starlette.routing import Route

from . import auth

routes = [
    Route('/login', endpoint=auth.login),
    Route('/auth', endpoint=auth.auth),
]
