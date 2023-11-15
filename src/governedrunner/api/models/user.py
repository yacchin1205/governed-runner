from datetime import datetime
from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: int = Field(example='1')
    created_at: datetime
    name: str

    class Config:
        orm_mode = True
