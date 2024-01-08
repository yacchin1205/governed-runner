from datetime import datetime, timezone
import logging

from governedrunner.db.database import SessionLocal
from governedrunner.db.models import Job
from governedrunner.api.rdm import RDMService

from ..settings import Settings
from governedrunner.job import GovernedRunner


logger = logging.getLogger(__name__)
settings = Settings()
runner = GovernedRunner.instance(GovernedRunner, config=settings.jupyterhub_traitlets_config)


async def create_new_job(job_id: str):
    with SessionLocal() as db:
        logger.info(f'Executing... {job_id}')
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = 'running'
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        current_user = job.owner
        rdm = RDMService(current_user)
        try:
            result = await runner.execute(job, rdm, job.source_url)

            job.status = 'completed'
            job.result_url = result.result_url
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info('Executed')
        except:
            job.status = 'failed'
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.exception('Failed')
