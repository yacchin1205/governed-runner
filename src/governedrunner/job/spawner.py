from jupyterhub.spawner import Spawner
from ..db.models import Job


class ContextBase:
    job: Job = None

    def __init__(self, job: Job):
        self.job = job

class User(ContextBase):
    @property
    def name(self):
        return self.job.owner.name

    @property
    def url(self):
        return self.job.owner.name

class Hub(ContextBase):
    @property
    def public_host(self):
        return '127.0.0.1'
    
    @property
    def api_url(self):
        return 'http://in-governed-runner:8081'
    
    @property
    def base_url(self):
        return 'http://in-governed-runner:8888/hub/'

class ORMSpawner(ContextBase):
    server = None

    @property
    def name(self):
        return self.job.id

def configure_spawner(job: Job, spawner: Spawner):
    spawner.user = User(job)
    spawner.hub = Hub(job)
    spawner.orm_spawner = ORMSpawner(job)
