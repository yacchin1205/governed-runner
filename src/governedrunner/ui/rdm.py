from datetime import datetime, timezone, timedelta
import logging

import aiohttp
from starlette.responses import RedirectResponse
from starlette.routing import Route

from governedrunner.api.rdm import RDMService
from governedrunner.db.database import SessionLocal
from governedrunner.db.models import RDMToken, User

from . import auth
from .util import frontend_url_for


logger = logging.getLogger(__name__)


async def check_rdm_token(rdm_token: RDMToken, db) -> bool:
    rdm = RDMService(rdm_token.owner)
    async with aiohttp.ClientSession() as session:
        async with session.get(rdm.api_url + '/users/me', headers={'Authorization': f'Bearer {rdm_token.token}'}) as resp:
            if resp.status == 401:
                return False
            if resp.status != 200:
                resp.raise_for_status()
            user = await resp.json()
            logger.debug(f'check_rdm_token: User: {user}')
    return True


def update_rdm_token(user: User, access_token: str, service: str, db):
    if user.rdm_token is not None:
        db.delete(user.rdm_token)
        db.commit()
        db.refresh(user)
    rdm_token = RDMToken(
        owner=user,
        token=access_token,
        created_at=datetime.now(timezone.utc),
        expired_at=None,
        service_id=service,
    )
    db.add(rdm_token)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return rdm_token


async def rdm_authorize(request):
    db = SessionLocal()
    try:
        user = await auth.get_user(request, db)
        if user is None:
            return RedirectResponse(url=frontend_url_for(request, 'login'))
        rdm = RDMService(user)
        redirect_uri = frontend_url_for(request, f'rdm_callback')
        return await rdm.oauth_service.authorize_redirect(
            request,
            redirect_uri,
            access_type='offline'
        )
    finally:
        db.close()


async def rdm_callback(request):
    db = SessionLocal()
    try:
        user = await auth.get_user(request, db)
        if user is None:
            return RedirectResponse(url=frontend_url_for(request, 'login'))
        rdm = RDMService(user)
        token = await rdm.oauth_service.authorize_access_token(request)
        logger.debug(f'Retrieved token: {token.keys()}')
        created = update_rdm_token(user, token['access_token'], rdm.service_id, db)
        if 'refresh_token' in token:
            logger.debug(f'Updating refresh token')
            created.refresh_token = token['refresh_token']
        if 'expires_in' in token:
            created.expired_at = datetime.now(timezone.utc) + timedelta(seconds=token['expires_in'])
            logger.debug(f'Expires at: {created.expired_at}')
        db.commit()
        return RedirectResponse(url=frontend_url_for(request, 'homepage'))
    finally:
        db.close()


prefix = '/rdm'
routes = [
    Route(prefix + '/authorize', endpoint=rdm_authorize),
    Route(prefix + '/callback', endpoint=rdm_callback),
]
