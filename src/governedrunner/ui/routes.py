from starlette.routing import Route

from . import auth
from .rdm import routes as rdm_routes

routes = rdm_routes + [
    Route('/login', endpoint=auth.login),
    Route('/auth', endpoint=auth.auth),
]
