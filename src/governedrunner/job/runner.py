import uuid

from traitlets.config import Application
from jupyterhub.traitlets import EntryPointType
from jupyterhub.spawner import Spawner

from ..db.models import Job
from ..api.rdm import RDMService
from .wb import (
    get_parent_folder, get_crate_folder, extract_rdm_url, extract_rdm_storage_provider,
    get_target_provider, find_file_by_name,
)
from .builders import ImageBuilder, DockerImageBuilder
from .trackers import JobTracker, DockerTracker
from .spawners import Repo2DockerSpawner
from .spawner import configure_spawner


def new_instance(klass, app):
    return klass(parent=app)

class RunnerResult:
    result_url: str = None

    def __init__(self, result_url: str):
        self.result_url = result_url

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

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    async def execute(self, job: Job, rdm: RDMService, source_url: str) -> RunnerResult:
        from ..api.settings import CRATE_FOLDER_NAME
        self.log.info(f'Executing... {source_url}')

        # Build image
        builder = new_instance(self.builder_class, self)
        optional_labels = {}
        if get_target_provider(rdm, source_url) == 'rdm':
            builder.optional_envs = {
                'RDM_HOSTS_JSON': rdm.repo2docker_hosts_json,
            }
        optional_labels.update({
            'governedrunner.opt.provider': get_target_provider(rdm, source_url),
        })
        builder.optional_labels = optional_labels
        image = await builder.build(source_url)
        self.log.info(f'Built image: {image}')

        # Run container
        spawner = new_instance(self.spawner_class, self)
        tracker = new_instance(self.tracker_class, self)
        configure_spawner(job, spawner)
        spawner.image = image
        spawner.user_options = {
            'image': image,
        }
        result_filename = f'{uuid.uuid4()}.json'
        rdm_url = extract_rdm_url(source_url)
        parent_folder_url = await get_parent_folder(rdm, rdm_url)
        self.log.debug(f'Parent folder: {parent_folder_url}')
        crate_folder_url = await get_crate_folder(rdm, parent_folder_url)
        rdm_provider = extract_rdm_storage_provider(source_url)
        self.log.debug(f'RDM storage provider: {rdm_provider}')
        spawner.cmd = ['bash', '-c', "sleep 10; echo '{\"test\": 1}' > " + f'/mnt/rdm/{rdm_provider}/{CRATE_FOLDER_NAME}/{result_filename}' + '; sleep 10']
        if get_target_provider(rdm, source_url) == 'rdm':
            try:
                spawner.rdmfs_token = rdm.access_token
            except AttributeError:
                self.log.warning('Spawner is not supported for RDMFS')
        host, port = await spawner.start()
        self.log.info(f'Started container: {host}:{port}')
        process = await tracker.track_process(spawner, host, port)
        self.log.debug(f'Waiting for process to finish...')
        await process.wait()
        self.log.info(f'Process finished')
        await spawner.stop()

        # Get result
        self.log.info(f'Getting result... {result_filename} from {crate_folder_url}')
        result = await find_file_by_name(rdm, crate_folder_url, result_filename)
        if result is None:
            raise ValueError(f'Cannot find result file: {result_filename} in {CRATE_FOLDER_NAME} folder')
        url = result['links']['download']
        self.log.info(f'WaterButler result URL: {url}')
        return RunnerResult(result_url=url)
