from datetime import datetime
import logging
import time

import httpx
from starlette.responses import RedirectResponse
from starlette.config import Config
from starlette.exceptions import HTTPException

from authlib.integrations.starlette_client import OAuth
from governedrunner.api.demo import USERNAME as DEMO_USERNAME
from governedrunner.db.models import User

logger = logging.getLogger(__name__)

config = Config('.env')
oauth = OAuth(config)
DEMO_USER = config('DEMO_USER', cast=bool, default=False)
CLIENT_ID = config('OAUTH2_CLIENT_ID', cast=str, default='')
CLIENT_SECRET = config('OAUTH2_CLIENT_SECRET', cast=str, default='')
ACCESS_TOKEN_URL = config('OAUTH2_TOKEN_URL', cast=str, default='')
AUTHORIZATION_URL = config('OAUTH2_AUTHORIZATION_URL', cast=str, default='')
USER_PROFILE_URL = config('USER_PROFILE_URL', cast=str, default='')
USER_PROFILE_PROPNAME = config('USER_PROFILE_PROPNAME', cast=str, default='')

service = oauth.register(
    name='parent',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url=ACCESS_TOKEN_URL,
    access_token_params={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    },
    authorize_url=AUTHORIZATION_URL,
)

async def is_logged_in(request):
    if DEMO_USER:
        return True
    if 'token' not in request.session:
        return False
    token = request.session['token']
    if 'expires_at' not in token:
        return False
    expires_at = token['expires_at']
    current_time = int(time.time())
    if current_time > int(expires_at):
        # expired
        return False
    access_token = token['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    async with httpx.AsyncClient() as client:
        user_info = await client.get(USER_PROFILE_URL, headers=headers)
        logger.debug(f'Userinfo Response: {user_info}')
        if not user_info.is_success:
            logger.error('Failed to retrieve user information, token revoked')
            del request.session['token']
            return False
        logger.debug(f'Userinfo Content: {user_info.json()}')
        request.session['username'] = user_info.json()[USER_PROFILE_PROPNAME]
    return True

async def get_username(request):
    if DEMO_USER:
        return DEMO_USERNAME
    if await is_logged_in(request):
        return request.session['username']
    return None

async def get_user(request, db):
    username = await get_username(request)
    if username is None:
        return None
    r = db.query(User).filter(User.name == username).first()
    if r is not None:
        return r
    u = User(name=username, created_at=datetime.now())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

async def login(request):
    redirect_uri = request.url_for('auth')
    return await service.authorize_redirect(request, redirect_uri)

async def auth(request):
    token = await service.authorize_access_token(request)
    request.session['token'] = token
    logger.debug(f'Retrieved token: {token.keys()}')
    await get_username(request)
    return RedirectResponse(url=request.url_for('homepage'))
