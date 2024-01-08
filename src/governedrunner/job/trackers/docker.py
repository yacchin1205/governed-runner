from aiodocker import Docker
from jupyterhub.spawner import Spawner

from .base import JobTracker, ProcessTracker


def has_name(container, name):
    return name in [name.lstrip('/') for name in container._container['Names']]


class ContainerTracker(ProcessTracker):
    container: str

    def __init__(self, container):
        self.container = container

    async def wait(self):
        async with Docker() as docker:
            container = await docker.containers.get(self.container)
            await container.wait()

class DockerTracker(JobTracker):
    async def track_process(self, spawner: Spawner, hostname: str, port: int) -> ProcessTracker:
        async with Docker() as docker:
            containers = await docker.containers.list()
            containers = [c for c in containers if has_name(c, spawner.container_name)]
            self.log.debug(f'Target: {containers}, {spawner.container_name}')
            if len(containers) == 0:
                raise RuntimeError(f'Container not found: {spawner.container_name}')
            return ContainerTracker(containers[0].id)
