from datetime import datetime
from enum import Enum
import logging
from typing import Optional, Annotated, Any
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
)
from fastapi_pagination import Page, paginate
from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, ItemsTransformer
from fastapi_pagination.utils import verify_params
from starlette.requests import Request

from governedrunner.api.rdm import RDMService
from governedrunner.api.auth import get_current_user
from governedrunner.api.models import NodeOut, ProviderOut, FileOut
from governedrunner.db.models import User


logger = logging.getLogger(__name__)
router = APIRouter()

Page = Page.with_custom_options(
    size=Query(10, ge=1, le=50),
)

class FileAction(str, Enum):
    download = 'download'
    meta = 'meta'

def get_rdm_service(current_user: Annotated[User, Depends(get_current_user)]):
    return RDMService(current_user)

def _get_provider_path(provdier):
    attr = provdier['attributes']
    provider = attr['provider']
    path = attr['path']
    return f'{provider}{path}'

def _create_links(request: Request, rdm: RDMService, requested_path: str, file: Any):
    links = []
    if file['id'].endswith('/'):
        links.append({
            'rel': 'files',
            'href': f'{request.url.scheme}://{request.url.netloc}{requested_path}{file["id"]}',
        })
        links.append({
            'rel': 'web',
            'href': f'{rdm.web_url}/{file["attributes"]["resource"]}/files/dir/{file["attributes"]["provider"]}{file["attributes"]["materialized"]}',
        })
    else:
        links.append({
            'rel': 'download',
            'href': f'{request.url.scheme}://{request.url.netloc}{requested_path}{file["id"]}?action={FileAction.download}',
        })
        links.append({
            'rel': 'meta',
            'href': f'{request.url.scheme}://{request.url.netloc}{requested_path}{file["id"]}?action={FileAction.meta}',
        })
        links.append({
            'rel': 'web',
            'href': f'{rdm.web_url}/{file["attributes"]["resource"]}/files/{file["attributes"]["provider"]}{file["attributes"]["path"]}',
        })
    links.append({
        'rel': 'parent',
        'href': str(request.url),
    })
    return links

def _create_file_out(request: Request, rdm: RDMService, requested_path: str, f: Any, content: Optional[Any] = None):
    return FileOut(
        id=f['id'],
        type=f['type'],
        kind=f['attributes']['kind'],
        node=f['attributes']['resource'],
        provider=f['attributes']['provider'],
        name=f['attributes']['name'],
        path=f['attributes']['materialized'],
        created_at=f['attributes'].get('created_utc', None),
        updated_at=f['attributes'].get('modified_utc', None),
        links=_create_links(request, rdm, requested_path, f),
        data=f,
        content=content,
    )

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
            node=provider['attributes']['node'],
            name=provider['attributes']['name'],
            links=[
                {
                    'rel': 'files',
                    'href': f'{request.url.scheme}://{request.url.netloc}{request.url.path}{_get_provider_path(provider)}',
                },
                {
                    'rel': 'parent',
                    'href': str(request.url),
                }
            ],
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
                {
                    'rel': 'parent',
                    'href': str(request.url),
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
    action: Optional[FileAction] = None,
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
    content = None
    if not isinstance(files, list):
        content = None
        if action == FileAction.download:
            content = await rdm.get(f'{rdm.files_url}/resources/{node_id}/providers/{provider_id}/{filepath}')
        return paginate([_create_file_out(request, rdm, requested_path, files, content)])
    return paginate([_create_file_out(request, rdm, requested_path, f) for f in files])
