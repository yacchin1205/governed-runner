from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, root_validator
from pydantic.utils import GetterDict

class State(str, Enum):
    running = 'running'
    completed = 'completed'
    failed = 'failed'


class SourceOut(BaseModel):
    url: Optional[str]


class ResultOut(BaseModel):
    url: Optional[str]


class ProgressOut(BaseModel):
    url: Optional[str]


class JobOut(BaseModel):
    id: str = Field(example='JOB_ID')
    created_at: datetime
    status: Optional[State]
    source: Optional[SourceOut]
    result: Optional[ResultOut]
    progress: Optional[ProgressOut]

    @root_validator(pre=True)
    def get_result_value(cls, values: GetterDict) -> GetterDict:
        source = None
        if values.source_url is not None:
            source = {
                'url': values.source_url,
            }
        if values.result_url is None:
            return {
                'source': source,
                'result': None,
                'progress': {
                    'url': f'/jobs/{values.id}/progress',
                },
            } | values.__dict__
        return {
            'source': source,
            'result': {
                'url': values.result_url,
            },
            'progress': None,
        } | values.__dict__

    class Config:
        orm_mode = True
