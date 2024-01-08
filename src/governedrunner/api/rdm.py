import httpx
import json
import logging

from fastapi import (
    HTTPException,
)
from governedrunner.db.models import User, RDMToken
from .settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class RDMService:
    current_user: User

    def __init__(self, current_user: User):
        self.current_user = current_user

    @property
    def _rdm_token(self) -> RDMToken:
        if self.current_user.rdm_token is None:
            raise HTTPException(status_code=403, detail='No GakuNin RDM token')
        return self.current_user.rdm_token

    @property
    def access_token(self):
        return self._rdm_token.token

    @property
    def api_url(self):
        if self._rdm_token.service_id != settings.rdm_service_id:
            raise HTTPException(status_code=403, detail='Unexpected GakuNin RDM service ID')
        return settings.rdm_api_url
    
    @property
    def files_url(self):
        if self._rdm_token.service_id != settings.rdm_service_id:
            raise HTTPException(status_code=403, detail='Unexpected GakuNin RDM service ID')
        return settings.rdm_files_url
    
    @property
    def web_url(self):
        if self._rdm_token.service_id != settings.rdm_service_id:
            raise HTTPException(status_code=403, detail='Unexpected GakuNin RDM service ID')
        return settings.rdm_web_url
    
    @property
    def repo2docker_hosts_json(self):
        config = [{
            'hostname': [self.web_url],
            'api': self.api_url,
            'token': self.access_token,
        }]
        return json.dumps(config)

    @property
    def _headers(self):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        return headers

    async def get(self, url):
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers)
            if resp.is_error:
                logger.error(f'Failed to request to GakuNin RDM: {resp}')
                raise HTTPException(status_code=resp.status_code)
            return resp.json()

    async def put(self, url, json=None):
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, json=json, headers=self._headers)
            if resp.is_error:
                logger.error(f'Failed to request to GakuNin RDM: {resp}')
                raise HTTPException(status_code=resp.status_code)
            return resp.json()
