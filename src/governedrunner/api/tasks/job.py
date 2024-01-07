from datetime import datetime, timezone
import logging
import time
from urllib.parse import urlparse

from governedrunner.db.database import SessionLocal
from governedrunner.db.models import Job
from governedrunner.api.rdm import RDMService


logger = logging.getLogger(__name__)
CRATE_FOLDER_NAME = '.crates'


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
    file_path = '/'.join(path_parts[3:])
    target_url = f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}/{file_path}?meta='
    resp = await rdm.get(target_url)
    file = resp['data']
    logger.info(f'Target: {file}')
    path_parts = file['attributes']['materialized'].lstrip('/').split('/')
    filename = path_parts[-1]
    path_parts = path_parts[:-1]

    resp = await rdm.get(f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}/')
    files = resp['data']
    for part in path_parts:
        part_files = [file for file in files if file['attributes']['name'] == part]
        if len(part_files) != 1:
            raise ValueError(f'File not found: {part} in {path_parts}')
        path = part_files[0]['attributes']['path']
        target_url = f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}{path}?meta='
        logger.info(f'Path: {part}, URL={target_url}')
        resp = await rdm.get(target_url)
        files = resp['data']
    return f'{rdm.files_url}/resources/{node_id}/providers/{provider_name}{path}/', filename

async def get_crate_folder(rdm: RDMService, folder_url: str):
    resp = await rdm.get(folder_url)
    files = resp['data']
    files = [file for file in files if file['attributes']['name'] == CRATE_FOLDER_NAME]
    if len(files) == 0:
        await rdm.put(f'{folder_url}?kind=folder&name={CRATE_FOLDER_NAME}')
        resp = await rdm.get(folder_url)
        files = resp['data']
        files = [file for file in files if file['attributes']['name'] == CRATE_FOLDER_NAME]
        if len(files) != 1:
            raise ValueError(f'Cannot create folder: {CRATE_FOLDER_NAME}')
    return files[0]['links']['upload']

async def create_new_job(job_id: str):
    with SessionLocal() as db:
        logger.info(f'Executing... {job_id}')
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = 'running'
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        current_user = job.owner
        rdm = RDMService(current_user)
        parent_folder_url, filename = await get_parent_folder(rdm, job.source_url)
        logger.info(f'Parent folder: {parent_folder_url}')
        crate_folder_url = await get_crate_folder(rdm, parent_folder_url)
        await rdm.put(
            f'{crate_folder_url}&name={filename}-{job_id}.json',
            {
                'test': True,
            },
        )
        time.sleep(30)

        job.status = 'completed'
        job.result_url = 'https://rdm.nii.ac.jp/result_file/'
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info('Executed')
