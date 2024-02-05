import logging
import os
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware

from .config import config
from .api.main import app as api_v1_app
from .ui.main import app as ui_app

SECRET_KEY = config('SESSION_SECRET_KEY', cast=str, default='')
PREFIX = config('GOVERNEDRUNNER_BASE_PATH', cast=str, default='')

if os.environ.get('DEBUG', '') == '1':
    logging.basicConfig(level=logging.DEBUG)

app = Starlette()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount(f'{PREFIX}/api/v1', api_v1_app)
app.mount(PREFIX, ui_app)
