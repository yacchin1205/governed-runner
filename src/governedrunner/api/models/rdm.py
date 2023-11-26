from enum import Enum
from pydantic import BaseModel, Field
from typing import Any

from governedrunner import __version__

class BaseRDMModel(BaseModel):
    id: str = Field(example='xxxxx')
    type: str = Field(example='nodes')
    links: list[dict[str, str]] = Field(
        example=[{'rel': 'children', 'href': 'http://localhost:8000/nodes/xxxxx/'}],
    )
    data: Any

class NodeOut(BaseRDMModel):
    title: str = Field(example='GakuNin RDM Project')

class ProviderOut(BaseRDMModel):
    name: str = Field(example='osfstorage')

class Kind(str, Enum):
    file = 'file'
    folder = 'folder'

class FileOut(BaseRDMModel):
    kind: Kind
    name: str = Field(example='file.txt')
    provider: str = Field(example='osfstorage')
    path: str = Field(example='/path/to/file.txt')
