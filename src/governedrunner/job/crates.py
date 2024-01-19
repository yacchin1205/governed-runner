from datetime import datetime, timezone
import json

from ..api.rdm import RDMService
from .wb import find_file_by_name


class RunCrateIndex:
    notebook: str
    id: str
    created_at: str
    updated_at: str
    name: str
    status: str
    links: list[dict[str, str]]

    def __init__(self, notebook: str, id: str, created_at: str, updated_at: str, name: str, status: str, links: list[dict[str, str]]):
        self.notebook = notebook
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.name = name
        self.status = status
        self.links = links

def _to_job_status(status: str):
    if status == 'CompletedActionStatus':
        return 'completed'
    if status == 'FailedActionStatus':
        return 'failed'
    raise ValueError(f'Unexpected status: {status}')

def _create_log_entity(id: str, log: str):
    now = datetime.now(timezone.utc)
    return {
        '@type': 'File',
        '@id': f"runner-{id}.log",
        '@type': 'File',
        'dateModified': now.isoformat(),
        'text': log,
        'lineCount': len(log.splitlines()),
        'contentSize': len(log),
        'encodingFormat': 'text/plain',
        'name': 'Runner log',
    }

async def modify_crate(rdm: RDMService, id: str, crate_file_url: str, crate_folder_url: str, runner_log: str):
    crate_content = await rdm.get(crate_file_url)
    entities = crate_content['@graph']
    create_action_entities = [entity for entity in entities if entity['@type'] == 'CreateAction']
    if len(create_action_entities) == 0:
        raise ValueError(f'No CreateAction entities: {crate_content}')
    create_action_entity = create_action_entities[0]
    result_entities = create_action_entity['result']
    if len(result_entities) == 0:
        raise ValueError(f'No result entities: {crate_content}')
    result_entity = result_entities[0]
    result_name = result_entity['@id']
    result_file_entities = [entity for entity in entities if entity['@type'] == 'File' and entity['@id'] == result_name]
    if len(result_file_entities) == 0:
        raise ValueError(f'No result file entities: {crate_content}')
    result_file_entity = result_file_entities[0]
    if '?' in crate_folder_url:
        crate_folder_url = crate_folder_url[:crate_folder_url.index('?')]
    result_file_json = json.loads(result_file_entity['text'])
    result_file_resp = await rdm.put(f'{crate_folder_url}?kind=file&name={result_name}', json=result_file_json)
    result_file = result_file_resp['data']
    result_entity.update({
        'size': result_file['attributes']['size'],
        'rdmURL': result_file['links']['download'],
        'name': result_name,
    })
    candidates = ['sha1', 'sha256', 'sha512', 'md5']
    for candidate in candidates:
        if candidate in result_file['attributes']:
            result_entity[candidate] = result_file['attributes'][candidate]
    entities.append(_create_log_entity(id, runner_log))
    await rdm.put(crate_file_url, json=crate_content)
    return _to_job_status(create_action_entity['actionStatus'])

async def insert_index(rdm: RDMService, folder_url: str, entry: RunCrateIndex):
    if '?' in folder_url:
        folder_url = folder_url[:folder_url.index('?')]
    jsonentry = dict(
        notebook=entry.notebook,
        id=entry.id,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        name=entry.name,
        status=entry.status,
        links=entry.links,
    )
    file = await find_file_by_name(rdm, folder_url, 'index.json')
    if file is None:
        await rdm.put(f'{folder_url}?kind=file&name=index.json', json=[jsonentry])
        return
    index_url = file['links']['upload']
    index = await rdm.get(index_url)
    index.append(jsonentry)
    await rdm.put(index_url, json=index)
