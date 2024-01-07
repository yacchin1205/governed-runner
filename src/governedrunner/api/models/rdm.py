from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional

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
    node: str = Field(example='xxxxx')
    name: str = Field(example='osfstorage')

class Kind(str, Enum):
    file = 'file'
    folder = 'folder'

class FileOut(BaseRDMModel):
    kind: Kind
    name: str = Field(example='file.txt')
    node: str = Field(example='xxxxx')
    provider: str = Field(example='osfstorage')
    path: str = Field(example='/path/to/file.txt')
    created_at: Optional[str] = Field(example='2021-01-01T00:00:00.000000+00:00')
    updated_at: Optional[str] = Field(example='2021-01-01T00:00:00.000000+00:00')
    content: Optional[Any]
