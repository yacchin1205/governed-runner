from datetime import datetime, timezone
import logging

import httpx
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from governedrunner.db.database import get_db
from governedrunner.db.models import User
from . import demo
from .settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()

async def _get_username_from_token(token: str):
    if not settings.user_profile_url:
        logger.error('User profile URL is not set')
        raise HTTPException(status_code=500)
    if not settings.user_profile_propname:
        logger.error('User profile property name is not set')
        raise HTTPException(status_code=500)
    async with httpx.AsyncClient() as client:
        user_info = await client.get(settings.user_profile_url, headers={
            'Authorization': f'Bearer {token}',
        })
        logger.debug(f'Userinfo Response: {user_info}')
        if not user_info.is_success:
            logger.error('Failed to retrieve user information, token revoked')
            raise HTTPException(status_code=401)
        logger.debug(f'Userinfo Content: {user_info.json()}')
        return user_info.json()[settings.user_profile_propname]


async def get_username(request: Request):
    if settings.demo_user:
        return demo.USERNAME
    if 'username' in request.session:
        logger.debug('Username found in session')
        return request.session['username']
    if 'Authorization' in request.headers:
        logger.debug('Authorization header found. Attempt to get username from token...')
        header = request.headers['Authorization'].split(' ')
        if len(header) != 2 or header[0].lower() != 'bearer':
            raise HTTPException(status_code=401)
        token = header[1]
        return await _get_username_from_token(token)
    raise HTTPException(status_code=401)

def get_current_user(db: Session = Depends(get_db), username: str = Depends(get_username)):
    if settings.demo_user:
        return demo.get_current_user(db)
    u = db.query(User).filter(User.name == username).first()
    if u is not None:
        return u
    u = User(
        name=username,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
