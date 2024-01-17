from datetime import datetime, timezone
import logging
from asyncio import Queue, QueueFull, QueueEmpty

from governedrunner.db.database import SessionLocal
from governedrunner.db.models import Job
from governedrunner.api.rdm import RDMService

from ..settings import Settings
from governedrunner.job import GovernedRunner


logger = logging.getLogger(__name__)
settings = Settings()
log_streams = {}


def create_new_job_queue(job_id: str):
    log_streams[job_id] = Queue(maxsize=100)

def get_job_queue(job_id: str) -> Queue:
    return log_streams.get(job_id, None)

def remove_job_queue(job_id: str):
    return log_streams.pop(job_id, None)

async def create_new_job(job_id: str):
    with SessionLocal() as db:
        logger.info(f'Executing... {job_id}')
        job = db.query(Job).filter(Job.id == job_id).first()
        def status_callback_impl(_, status, notebook):
            job.status = status
            job.updated_at = datetime.now(timezone.utc)
            if notebook is not None:
                job.notebook = notebook
            db.commit()
        def log_stream_callback_impl(status, log):
            log_ = log.rstrip("\n")
            logger.info(f'LOG({status}, {job.id}): {log_}')
            job.status = status
            job.updated_at = datetime.now(timezone.utc)
            q = get_job_queue(job.id)
            if q is not None:
                if q.full():
                    try:
                        q.get_nowait()
                    except QueueEmpty:
                        pass
                try:
                    q.put_nowait((status, log))
                except QueueFull:
                    logger.warning(f'Queue is full: LOG({status}, {job.id}): {log_}')
            if job.log is None:
                job.log = log
            else:
                job.log = job.log + log
            db.commit()
        current_user = job.owner
        rdm = RDMService(current_user)
        try:
            runner = GovernedRunner.instance(GovernedRunner, config=settings.jupyterhub_traitlets_config)
            runner.use_snapshot = job.use_snapshot
            runner.status_callback = status_callback_impl
            runner.log_stream_callback = log_stream_callback_impl
            result = await runner.execute(job, rdm, job.source_url)

            job.status = result.status
            job.notebook = result.notebook
            job.result_url = result.result_url
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info('Executed')
            remove_job_queue(job.id)
        except:
            job.status = 'failed'
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.exception('Failed')
