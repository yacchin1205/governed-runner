from datetime import datetime
from sqlalchemy.orm import Session

from governedrunner.db.models import User

CURRENT_USER_ID = 1

def get_current_user(db: Session):
    u = db.query(User).filter(User.id == CURRENT_USER_ID).first()
    if u is not None:
        return u
    u = User(id=CURRENT_USER_ID, name='DEMO', created_at=datetime.now())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
