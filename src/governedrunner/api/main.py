from fastapi import FastAPI
from fastapi_pagination import add_pagination
from fastapi.middleware.cors import CORSMiddleware

from ..db.database import Base, engine
from .routers import server, user, job, rdm

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(server.router)
app.include_router(user.router)
app.include_router(job.router)
app.include_router(rdm.router)

add_pagination(app)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
