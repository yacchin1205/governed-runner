import logging
import os
from starlette.applications import Starlette
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

from .api.main import app as api_app
from .ui.main import app as ui_app

config = Config('.env')
SECRET_KEY = config('SESSION_SECRET_KEY', cast=str, default='')
PREFIX = config('GOVERNEDRUNNER_BASE_PATH', cast=str, default='')

if os.environ.get('DEBUG', '') == '1':
    logging.basicConfig(level=logging.DEBUG)

app = Starlette()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount(f'{PREFIX}/api', api_app)
app.mount(PREFIX, ui_app)