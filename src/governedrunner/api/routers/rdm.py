from datetime import datetime
from enum import Enum
import logging
from typing import Optional, Annotated, Any
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi_pagination import Page, paginate
from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, ItemsTransformer
from fastapi_pagination.utils import verify_params
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from governedrunner.api.auth import get_current_user
from governedrunner.api.models import NodeOut, ProviderOut, FileOut
from governedrunner.api.settings import Settings
from governedrunner.db.models import User, RDMToken


logger = logging.getLogger(__name__)
router = APIRouter()

settings = Settings()

Page = Page.with_custom_options(
    size=Query(10, ge=1, le=50),
)

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

    async def get(self, url):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.is_error:
                logger.error(f'Failed to request to GakuNin RDM: {resp}')
                raise HTTPException(status_code=resp.status_code)
            return resp.json()

def get_rdm_service(current_user: Annotated[User, Depends(get_current_user)]):
    return RDMService(current_user)

def _get_provider_path(provdier):
    attr = provdier['attributes']
    provider = attr['provider']
    path = attr['path']
    return f'{provider}{path}'

async def _paginate_rdm_api(
    rdm: RDMService,
    base_url: str,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    qp = {
        'page': str(raw_params.offset // raw_params.limit + 1),
        'page[size]': str(raw_params.limit),
    }
    urlsep = '?' if '?' not in base_url else '&'
    url = f'{base_url}{urlsep}{urlencode(qp)}'
    result = await rdm.get(url)

    total = result['links']['meta']['total']

    t_items = apply_items_transformer(result['data'], transformer)

    return create_page(
        t_items,
        total,
        params,
        **(additional_data or {}),
    )

@router.get('/nodes/', response_model=Page[NodeOut])
async def retrieve_nodes(
    request: Request,
    rdm: RDMService = Depends(get_rdm_service),
):
    '''
    現在のユーザーが参照可能なGakuNin RDMノードを取得します。
    '''
    return await _paginate_rdm_api(
        rdm,
        f'{rdm.api_url}/nodes/',
        transformer=lambda nodes: [NodeOut(
            id=node['id'],
            type=node['type'],
            title=node['attributes']['title'],
            links=[
                {
                    'rel': 'providers',
                    'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{node["id"]}/providers/',
                },
                {
                    'rel': 'children',
                    'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{node["id"]}/children/',
                },
            ],
            data=node,
        ) for node in nodes],
    )

@router.get('/nodes/{node_id}/providers/', response_model=Page[ProviderOut])
async def retrieve_node_providers(
    node_id: str,
    request: Request,
    rdm: RDMService = Depends(get_rdm_service),
):
    '''
    指定されたGakuNin RDMノードに紐づくストレージプロバイダを取得します。
    '''
    return await _paginate_rdm_api(
        rdm,
        f'{rdm.api_url}/nodes/{node_id}/files/',
        transformer=lambda providers: [ProviderOut(
            id=provider['id'],
            type=provider['type'],
            name=provider['attributes']['name'],
            links=[{
                'rel': 'files',
                'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{_get_provider_path(provider)}',
            }],
            data=provider,
        ) for provider in providers],
    )

@router.get('/nodes/{node_id}/children/', response_model=Page[NodeOut])
async def retrieve_node_children(
    node_id: str,
    request: Request,
    rdm: RDMService = Depends(get_rdm_service),
):
    '''
    指定されたGakuNin RDMノードの子ノードを取得します。
    '''
    return await _paginate_rdm_api(
        rdm,
        f'{rdm.api_url}/nodes/{node_id}/children/',
        transformer=lambda nodes: [NodeOut(
            id=node['id'],
            type=node['type'],
            title=node['attributes']['title'],
            links=[
                {
                    'rel': 'providers',
                    'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{node["id"]}/providers/',
                },
                {
                    'rel': 'children',
                    'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{node["id"]}/children/',
                },
            ],
            data=node,
        ) for node in nodes],
    )

@router.get(
    '/nodes/{node_id}/providers/{provider_id}/',
    response_model=Page[FileOut],
)
async def retrieve_node_root_files(
    node_id: str,
    provider_id: str,
    request: Request,
    rdm: RDMService = Depends(get_rdm_service),
):
    '''
    指定されたストレージプロバイダのルートディレクトリにあるファイルを取得します。
    '''
    return await retrieve_node_files(node_id, provider_id, '', request, rdm=rdm)

@router.get(
    '/nodes/{node_id}/providers/{provider_id}/{filepath:path}',
    response_model=Page[FileOut],
)
async def retrieve_node_files(
    node_id: str,
    provider_id: str,
    filepath:str,
    request: Request,
    rdm: RDMService = Depends(get_rdm_service),
):
    '''
    指定されたストレージプロバイダのパスにあるファイルを取得します。
    '''
    file_info = await rdm.get(f'{rdm.files_url}/resources/{node_id}/providers/{provider_id}/{filepath}?meta=')
    files = file_info['data']
    requested_base_path = f'/nodes/{node_id}/providers/{provider_id}'
    requested_base_path_without_provider = f'/nodes/{node_id}/providers/'
    requested_path = request.url.path
    if requested_base_path not in requested_path:
        raise ValueError(f'Unexpected path: {requested_path}')
    requested_path = requested_path[:requested_path.index(requested_base_path) +
                                    len(requested_base_path_without_provider)]
    return paginate([FileOut(
        id=f['id'],
        type=f['type'],
        kind=f['attributes']['kind'],
        provider=f['attributes']['provider'],
        name=f['attributes']['name'],
        path=f['attributes']['materialized'],
        links=[
            {
                'rel': 'files',
                'href': f'{request.url.scheme}://{request.url.netloc}{requested_path}{f["id"]}',
            },
        ] if f['id'].endswith('/') else [],
        data=f,
    ) for f in files])
