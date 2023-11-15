from pydantic import BaseModel, Field

from governedrunner import __version__

class ServerOut(BaseModel):
    version: str = Field(example=__version__)
