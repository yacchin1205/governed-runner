from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from governedrunner.db.database import get_db
from governedrunner.db.models import User
from . import demo
from .settings import Settings

settings = Settings()

def get_username(request: Request):
    if settings.demo_user:
        return demo.USERNAME
    if 'username' not in request.session:
        raise HTTPException(status_code=401)
    return request.session['username']

def get_current_user(db: Session = Depends(get_db), username: str = Depends(get_username)):
    if settings.demo_user:
        return demo.get_current_user(db)
    u = db.query(User).filter(User.name == username).first()
    if u is not None:
        return u
    u = User(
        name=username,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
