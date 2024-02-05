from datetime import datetime, timezone
import os
import subprocess

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, RedirectResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.routing import WebSocketRoute

from governedrunner.config import config
from governedrunner.api.tasks.job import get_job_queue
from governedrunner.db.database import SessionLocal
from governedrunner.db.models import RDMToken
from . import auth
from .routes import routes

FORCE_BUILD_FRONTEND = config('FORCE_BUILD_FRONTEND', cast=bool, default=False)

def _ensure_frontend():
    ui_path, _ = os.path.split(__file__)
    root_path, _ = os.path.split(ui_path)
    frontend_path = os.path.join(root_path, 'frontend')
    build_path = os.path.join(frontend_path, 'out')
    if not FORCE_BUILD_FRONTEND and os.path.exists(build_path):
        return build_path
    subprocess.check_call(
        ['npm', 'install'],
        cwd=frontend_path,
    )
    subprocess.check_call(
        ['npm', 'run', 'build'],
        cwd=frontend_path,
    )
    return build_path

def _update_rdm_token(user, request, db):
    token = request.query_params.get('token', None)
    if token is None:
        return False
    service = request.query_params.get('service', None)
    if service is None:
        raise HTTPException(status_code=400)
    if user.rdm_token is not None:
        db.delete(user.rdm_token)
        db.commit()
        db.refresh(user)
    rdm_token = RDMToken(
        owner=user,
        token=token,
        created_at=datetime.now(timezone.utc),
        expired_at=None,
        service_id=service,
    )
    db.add(rdm_token)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return True

async def homepage(request):
    db = SessionLocal()
    try:
        user = await auth.get_user(request, db)
        if user is None:
            return RedirectResponse(url=request.url_for('login'))
        updated = _update_rdm_token(user, request, db)
        if updated:
            return RedirectResponse(url=request.url_for('homepage'))
        if user.rdm_token is None:
            raise HTTPException(status_code=403, detail="RDM token not defined")
        return FileResponse(
            path=f'{build_path}/index.html',
            media_type='text/html',
        )
    finally:
        db.close()

async def websocket_log(websocket):
    job_id = websocket.path_params["job_id"]
    await websocket.accept()
    q = get_job_queue(job_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Job not found")
    while True:
        status, log = await q.get()
        await websocket.send_json({'status': status, 'log': log})
        if status == 'completed' or status == 'failed':
            break
    await websocket.close()

build_path = _ensure_frontend()

app = Starlette(routes=routes + [
    Route('/', endpoint=homepage),
    WebSocketRoute('/ws/jobs/{job_id}/progress', endpoint=websocket_log),
    Mount('/', StaticFiles(directory=build_path, html=True), name='static'),
])
