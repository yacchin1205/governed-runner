from datetime import datetime
from enum import Enum
import uuid
from typing import Optional, Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    File,
    Form,
    UploadFile,
)
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from governedrunner.api.auth import get_current_user
from governedrunner.api.models import JobOut
from governedrunner.api.tasks import create_new_job
from governedrunner.db.database import get_db
from governedrunner.db.models import Job, User


class FileType(str, Enum):
    run_crate = 'run-crate'
    notebook = 'notebook'


router = APIRouter()


@router.get('/jobs/', response_model=Page[JobOut])
def retrieve_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    '''
    現在のユーザーが実行した全てのジョブを取得します。
    '''
    return paginate(db, select(Job) \
        .where(Job.owner == current_user) \
        .order_by(Job.created_at))


@router.post('/jobs/', response_model=JobOut)
def create_job(
    current_user: Annotated[User, Depends(get_current_user)],
    bakcground_tasks: BackgroundTasks,
#    file: UploadFile = File(None),
    file_url: str = Form(),
    type: FileType = Form(FileType.run_crate),
#    context_url: str = Form(None),
    use_snapshot: bool = Form(False),
    db: Session = Depends(get_db),
):
    '''
    ジョブを実行します。
    '''
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, created_at=datetime.now(), owner=current_user)
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


@router.websocket('/jobs/{job_id}/progress')
async def stream_job_progress(job_id: str, websocket: WebSocket):
    '''
    ジョブの進行状況を取得します。
    '''
    # TBD
    await websocket.accept()
    await websocket.send_json({'test': True})