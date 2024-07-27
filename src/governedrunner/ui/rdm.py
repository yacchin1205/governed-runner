from datetime import datetime, timezone, timedelta
import logging

from starlette.responses import RedirectResponse
from starlette.routing import Route

from governedrunner.api.rdm import RDMService
from governedrunner.db.database import SessionLocal
from governedrunner.db.models import RDMToken, User

from . import auth
from .util import frontend_url_for


logger = logging.getLogger(__name__)


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
        return await rdm.oauth_service.authorize_redirect(request, redirect_uri)
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
        if 'expires_in' in token:
            logger.debug(f'Expires in: {token["expires_in"]}')
            created.expired_at = datetime.now(timezone.utc) + timedelta(seconds=token['expires_in'])
        db.commit()
        return RedirectResponse(url=frontend_url_for(request, 'homepage'))
    finally:
        db.close()


prefix = '/rdm'
routes = [
    Route(prefix + '/authorize', endpoint=rdm_authorize),
    Route(prefix + '/callback', endpoint=rdm_callback),
]
