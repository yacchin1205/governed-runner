from datetime import datetime, timezone
from enum import Enum
import logging
import uuid
from typing import Optional, Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Form,
)
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from governedrunner.api.auth import get_current_user
from governedrunner.api.models import JobOut
from governedrunner.api.models.job import State
from governedrunner.api.tasks import create_new_job
from governedrunner.api.tasks.job import create_new_job_queue
from governedrunner.db.database import get_db
from governedrunner.db.models import Job, User


class FileType(str, Enum):
    run_crate = 'run-crate'
    notebook = 'notebook'


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/jobs/', response_model=Page[JobOut])
def retrieve_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    state: Optional[State] = None,
    notebook: Optional[str] = None,
    db: Session = Depends(get_db),
):
    '''
    現在のユーザーが実行した全てのジョブを取得します。
    '''
    query = select(Job).where(Job.owner == current_user)
    if state is not None:
        query = query.filter(Job.status == state)
    if notebook is not None:
        query = query.filter(Job.notebook == notebook)
    return paginate(db, query.order_by(Job.updated_at))


@router.post('/jobs/', response_model=JobOut)
def create_job(
    current_user: Annotated[User, Depends(get_current_user)],
    bakcground_tasks: BackgroundTasks,
    file_url: str = Form(),
    type: FileType = Form(FileType.run_crate),
    use_snapshot: bool = Form(False),
    db: Session = Depends(get_db),
):
    '''
    ジョブを実行します。
    '''
    job_id = str(uuid.uuid4())
    if type == FileType.run_crate:
        file_url = f'crate+{file_url}'
    create_new_job_queue(job_id)
    job = Job(
        id=job_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        owner=current_user,
        source_url=file_url,
        use_snapshot=use_snapshot,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    bakcground_tasks.add_task(create_new_job, job_id)
    return job


@router.get('/jobs/{job_id}', response_model=JobOut)
def retrieve_job(
    current_user: Annotated[User, Depends(get_current_user)],
    job_id: str,
    db: Session = Depends(get_db),
):
    '''
    指定されたジョブ情報を取得します。
    '''
    job = db.query(Job).filter(Job.id == job_id and Job.owner == current_user).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
