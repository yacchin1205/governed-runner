from fastapi import FastAPI
from fastapi_pagination import add_pagination

from ..db.database import Base, engine
from .routers import server, user, job

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(server.router)
app.include_router(user.router)
app.include_router(job.router)

add_pagination(app)