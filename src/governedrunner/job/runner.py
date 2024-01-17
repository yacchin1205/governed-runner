from traitlets import Bool, Callable
from traitlets.config import Application
from jupyterhub.traitlets import EntryPointType
from jupyterhub.spawner import Spawner

from ..db.models import Job
from ..api.rdm import RDMService
from .crates import RunCrateIndex, modify_crate, insert_index
from .wb import (
    get_parent_folder, get_crate_folder, extract_rdm_url,
    extract_rdm_node_id, extract_rdm_storage_provider, extract_repo_info,
    get_target_provider, find_file_by_name, files_url_to_web_url,
)
from .builders import ImageBuilder, DockerImageBuilder
from .trackers import JobTracker, DockerTracker
from .spawners import Repo2DockerSpawner
from .spawner import configure_spawner


def new_instance(klass, app):
    return klass(parent=app)

class RunnerResult:
    status: str = None
    result_url: str = None
    notebook: str = None

    def __init__(self, notebook: str, result_url: str, status: str):
        self.notebook = notebook
        self.result_url = result_url
        self.status = status

class GovernedRunner(Application):
    builder_class = EntryPointType(
        default_value=DockerImageBuilder,
        klass=ImageBuilder,
        entry_point_group="governedrunner.imagebuilders",
        help="""The class to use for building Docker images.

        Should be a subclass of :class:`governedrunner.job.builders.ImageBuilder`.
        """,
    ).tag(config=True)

    spawner_class = EntryPointType(
        default_value=Repo2DockerSpawner,
        klass=Spawner,
        entry_point_group="jupyterhub.spawners",
        help="""The class to use for spawning single-user servers.

        Should be a subclass of :class:`jupyterhub.spawner.Spawner`.
        """,
    ).tag(config=True)

    tracker_class = EntryPointType(
        default_value=DockerTracker,
        klass=JobTracker,
        entry_point_group="governedrunner.jobtrackers",
        help="""The class to use for tracking jobs.

        Should be a subclass of :class:`governedrunner.job.trackers.JobTracker`.
        """,
    ).tag(config=True)

    use_snapshot = Bool(
        False,
        help="""Whether to use snapshot or not.

        If True, the runner will use snapshot of the repository.
        """,
    ).tag(config=True)

    status_callback = Callable(
        None,
        help="""Callback function to call when job status is changed.

        The callback function should accept two arguments: job_id and status.
        """,
    ).tag(config=True)

    log_stream_callback = Callable(
        None,
        help="""Callback function to call when log is emitted.
        """,
    ).tag(config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    async def execute(self, job: Job, rdm: RDMService, source_url: str) -> RunnerResult:
        from ..api.settings import CRATE_FOLDER_NAME
        self.log.info(f'Starting... {source_url}')

        # Build image
        notebook_filename, repo_url = await extract_repo_info(rdm, source_url)
        if self.status_callback is not None:
            self.status_callback(job.id, 'building', notebook_filename)
        builder = new_instance(self.builder_class, self)
        optional_labels = {}
        if get_target_provider(rdm, source_url) == 'rdm':
            builder.optional_envs = {
                'RDM_HOSTS_JSON': rdm.repo2docker_hosts_json,
            }
        optional_labels.update({
            'provider': get_target_provider(rdm, source_url),
            'user.rdm_node_id': extract_rdm_node_id(source_url),
            'user.rdm_api_url': rdm.api_url,
        })
        builder.optional_labels = optional_labels
        if self.use_snapshot:
            _, repo_url = await extract_repo_info(rdm, extract_rdm_url(source_url))
        builder.log_stream_callback = self.log_stream_callback
        self.log.info(f'Building image... {repo_url}')
        image = await builder.build(repo_url)
        self.log.info(f'Built image: {image}')

        # Run container
        if self.status_callback is not None:
            self.status_callback(job.id, 'running', notebook_filename)
        if self.log_stream_callback is not None:
            self.log_stream_callback('running', f'Running {notebook_filename}...')
        spawner = new_instance(self.spawner_class, self)
        tracker = new_instance(self.tracker_class, self)
        configure_spawner(job, spawner)
        spawner.image = image
        spawner.user_options = {
            'image': image,
        }
        result_filename = f'{job.id}.json'
        rdm_url = extract_rdm_url(source_url)
        parent_folder_url = await get_parent_folder(rdm, rdm_url)
        self.log.debug(f'Parent folder: {parent_folder_url}')
        crate_folder_url = await get_crate_folder(rdm, parent_folder_url)
        rdm_provider = extract_rdm_storage_provider(source_url)
        self.log.debug(f'RDM storage provider: {rdm_provider}')
        spawner.cmd = [
            'env', 'RUN_CRATE_METADATA=~/.run-crate-metadata.json', f'RUN_CRATE_ID={job.id}',
            'run-crate', notebook_filename, f'/mnt/rdm/{rdm_provider}/{CRATE_FOLDER_NAME}/{result_filename}',
        ]
        if get_target_provider(rdm, source_url) == 'rdm':
            try:
                spawner.rdmfs_token = rdm.access_token
            except AttributeError:
                self.log.warning('Spawner is not supported for RDMFS')
        host, port = await spawner.start()
        self.log.info(f'Started container: {host}:{port}')
        process = await tracker.track_process(spawner, host, port)
        self.log.debug(f'Waiting for process to finish...')
        if self.log_stream_callback is not None:
            self.log_stream_callback('running', f'Waiting for {notebook_filename} to finish...')
        await process.wait(self.log_stream_callback)
        self.log.info(f'Process finished')
        await spawner.stop()
        if self.log_stream_callback is not None:
            self.log_stream_callback('running', f'Collecting results...')

        # Get result
        self.log.info(f'Getting result... {result_filename} from {crate_folder_url}')
        result = await find_file_by_name(rdm, crate_folder_url, result_filename)
        if result is None:
            raise ValueError(f'Cannot find result file: {result_filename} in {CRATE_FOLDER_NAME} folder')
        url = result['links']['download']
        self.log.info(f'Modifying crates... {url}')
        status = await modify_crate(rdm, url, crate_folder_url)
        self.log.info(f'Inserting index... {crate_folder_url}')
        await insert_index(rdm, crate_folder_url, RunCrateIndex(
            notebook=notebook_filename,
            id=job.id,
            created_at=job.created_at.isoformat() if job.created_at is not None else '',
            updated_at=job.updated_at.isoformat() if job.updated_at is not None else '',
            name=result_filename,
            status=status,
            links=[
                dict(rel='download', href=url[:url.index('?')] if '?' in url else url),
                dict(rel='web', href=files_url_to_web_url(rdm, url)),
            ],
        ))
        self.log.info(f'WaterButler result URL: {url}')
        if self.log_stream_callback is not None:
            self.log_stream_callback(status, f'Finished: {CRATE_FOLDER_NAME}/{result_filename}')
        return RunnerResult(notebook=notebook_filename, result_url=url, status=status)
