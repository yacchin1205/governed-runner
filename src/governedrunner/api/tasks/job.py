import logging
import time

from governedrunner.db.database import SessionLocal
from governedrunner.db.models import Job


logger = logging.getLogger(__name__)


def create_new_job(job_id: str):
    with SessionLocal() as db:
        logger.info(f'Executing... {job_id}')
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = 'running'
        db.commit()
        time.sleep(30)

        job.status = 'completed'
        job.result_url = 'https://rdm.nii.ac.jp/result_file/'
        db.commit()
        logger.info('Executed')