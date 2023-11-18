from starlette.responses import RedirectResponse, PlainTextResponse
from starlette.routing import Route

from . import auth

async def homepage(request):
    username = await auth.get_username(request)
    if username is None:
        return RedirectResponse(url=request.url_for('login'))
    return PlainTextResponse(f'Hello! {username}')

routes = [
    Route('/', endpoint=homepage),
    Route('/login', endpoint=auth.login),
    Route('/auth', endpoint=auth.auth),
]
