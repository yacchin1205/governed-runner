
import logging
from typing import Any
from urllib.parse import urlparse

from ..api.rdm import RDMService


logger = logging.getLogger(__name__)
PREFIX_CRATE = 'crate+'


def extract_rdm_url(url: str) -> str:
    if url.startswith(PREFIX_CRATE):
        return url[6:]
    return url

def extract_rdm_node_id(url: str) -> str:
    path = urlparse(url).path
    segments = path.lstrip('/').split('/')
    if len(segments) <= 1:
        raise ValueError(f'Invalid path: {path}')
    return segments.pop(0)

def extract_rdm_storage_provider(url: str) -> str:
    path = urlparse(url).path
    segments = path.lstrip('/').split('/')
    if len(segments) <= 1:
        raise ValueError(f'Invalid path: {path}')
    segments.pop(0)
    if len(segments) == 0:
        raise ValueError(f'Invalid path: {path}')
    if segments.pop(0) != 'files':
        raise ValueError(f'Invalid path: {path}')
    provider_or_dir = segments.pop(0)
    if provider_or_dir != 'dir':
        return provider_or_dir
    if len(segments) == 0:
        raise ValueError(f'Invalid path: {path}')
    return segments.pop(0)

async def extract_repo_info(rdm: RDMService, url: str):
    if url.startswith(PREFIX_CRATE):
        return await _extract_notebook_filename_from_crate(rdm, url[len(PREFIX_CRATE):]), url
    return await _extract_file_repo_info(rdm, url)

def files_url_to_web_url(rdm: RDMService, files_url: str):
    if not files_url.startswith(rdm.files_url):
        raise ValueError(f'Invalid source URL: {files_url} (wb_url={rdm.files_url})')
    files_path = files_url[len(rdm.files_url):].lstrip('/').split('/')
    if files_path.pop(0) != 'resources':
        raise ValueError(f'Unexpected path: {files_url}')
    node_id = files_path.pop(0)
    if files_path.pop(0) != 'providers':
        raise ValueError(f'Unexpected path: {files_url}')
    provider_name = files_path.pop(0)
    path = '/'.join(files_path)
    return f'{rdm.web_url}/{node_id}/files/{provider_name}/{path}'

def get_target_provider(rdm: RDMService, url: str) -> str:
    url = extract_rdm_url(url)
    if url.startswith(rdm.web_url):
        return 'rdm'
    return 'unknown'

async def get_parent_folder(rdm: RDMService, source_url: str):
    if not source_url.startswith(rdm.web_url):
        raise ValueError('Invalid source URL')
    path = urlparse(source_url).path
    path_parts = path.lstrip('/').split('/')
    if len(path_parts) < 4:
        raise ValueError(f'Unexpected path: {path}')
    node_id = path_parts.pop(0)
    if path_parts.pop(0) != 'files':
        raise ValueError(f'Unexpected path: {path_parts}')
    if path_parts[0] == 'dir':
        path_parts.pop(0)
    provider_name = path_parts[0]
    return f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}/'

async def find_file_by_name(rdm: RDMService, folder_url: str, filename: str):
    resp = await rdm.get(folder_url)
    files = resp['data']
    files = [file for file in files if file['attributes']['name'] == filename]
    if len(files) == 0:
        return None
    return files[0]

async def get_crate_folder(rdm: RDMService, folder_url: str):
    from ..api.settings import CRATE_FOLDER_NAME
    file = await find_file_by_name(rdm, folder_url, CRATE_FOLDER_NAME)
    if file is None:
        await rdm.put(f'{folder_url}?kind=folder&name={CRATE_FOLDER_NAME}')
        file = await find_file_by_name(rdm, folder_url, CRATE_FOLDER_NAME)
        if file is None:
            raise ValueError(f'Cannot create folder: {CRATE_FOLDER_NAME}')
    return file['links']['upload']

def _get_files_url(rdm: RDMService, url: str):
    if not url.startswith(rdm.web_url):
        raise ValueError(f'Invalid source URL: {url} (web_url={rdm.web_url})')
    url = url[len(rdm.web_url):].lstrip('/').split('/')
    node_id = url.pop(0)
    if url.pop(0) != 'files':
        raise ValueError(f'Unexpected path: {url}')
    if url[0] == 'dir':
        url.pop(0)
    provider_name = url.pop(0)
    path = '/'.join(url)
    return f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}/{path}'

async def _extract_notebook_filename_from_crate(rdm: RDMService, url: str):
    files_url = _get_files_url(rdm, url)
    content = await rdm.get(files_url)
    entities = content['@graph']
    create_action_entities = [entity for entity in entities if entity['@type'] == 'CreateAction']
    if len(create_action_entities) == 0:
        raise ValueError(f'No CreateAction entities: {content}')
    object_entities = create_action_entities[0]['object']
    if len(object_entities) == 0:
        raise ValueError(f'No object entities: {content}')
    object_entity = object_entities[0]
    return object_entity['@id']

async def _extract_file_repo_info(rdm: RDMService, url: str):
    files_url = _get_files_url(rdm, url)
    content = await rdm.get(files_url + '?meta=')
    attributes = content['data']['attributes']
    if attributes['kind'] != 'file':
        raise ValueError(f'Not a file: {attributes["kind"]}')
    materialized_path = attributes['materialized'].lstrip('/')
    return materialized_path, f'{rdm.web_url}/{attributes["resource"]}/files/dir/{attributes["provider"]}'
