from traitlets.config import LoggingConfigurable
from jupyterhub.spawner import Spawner


class ProcessTracker:
    async def wait(self):
        """
        Wait for the process to finish.
        """
        raise NotImplementedError()


class JobTracker(LoggingConfigurable):
    async def track_process(self, spawner: Spawner, hostname: str, port: int) -> ProcessTracker:
        """
        Get a tracker for the given spawner.

        Args:
            spawner: The spawner
            hostname: The hostname of the process
            port: The port of the process

        Returns:
            The tracker
        """
        raise NotImplementedError()