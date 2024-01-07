from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship

from ..database import Base


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), index=True)
    updated_at = Column(DateTime(timezone=True), index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, nullable=True, index=True)
    source_url = Column(String, nullable=True, index=True)
    result_url = Column(String, nullable=True, index=True)

    owner = relationship('User')
