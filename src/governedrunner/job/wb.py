
import logging
from urllib.parse import urlparse

from ..api.rdm import RDMService


logger = logging.getLogger(__name__)


def extract_rdm_url(url: str) -> str:
    if url.startswith('crate+'):
        return url[6:]
    return url

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
    node_id = path_parts[0]
    if path_parts[1] != 'files':
        raise ValueError(f'Unexpected path: {path_parts}')
    provider_name = path_parts[2]
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
