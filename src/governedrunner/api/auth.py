from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from governedrunner.db.database import get_db

# DEMO
from governedrunner import demo


def get_current_user(db: Session = Depends(get_db)):
    return demo.get_current_user(db)
