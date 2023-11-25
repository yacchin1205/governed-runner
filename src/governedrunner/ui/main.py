import os
import subprocess

from starlette.applications import Starlette
from starlette.config import Config
from starlette.responses import FileResponse, RedirectResponse, PlainTextResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from . import auth
from .routes import routes

config = Config('.env')
FORCE_BUILD_FRONTEND = config('FORCE_BUILD_FRONTEND', cast=bool, default=False)

def _ensure_frontend():
    ui_path, _ = os.path.split(__file__)
    root_path, _ = os.path.split(ui_path)
    frontend_path = os.path.join(root_path, 'frontend')
    build_path = os.path.join(frontend_path, 'out')
    if not FORCE_BUILD_FRONTEND and os.path.exists(build_path):
        return build_path
    subprocess.check_call(
        ['npm', 'run', 'build'],
        cwd=frontend_path,
    )
    return build_path

async def homepage(request):
    username = await auth.get_username(request)
    if username is None:
        return RedirectResponse(url=request.url_for('login'))
    return FileResponse(
        path=f'{build_path}/index.html',
        media_type='text/html',
    )

build_path = _ensure_frontend()

app = Starlette(routes=routes + [
    Route('/', endpoint=homepage),
    Mount('/', StaticFiles(directory=build_path, html=True), name='static'),
])
