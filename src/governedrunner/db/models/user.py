from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, index=True)

    rdm_tokens = relationship('RDMToken', back_populates='owner')


class RDMToken(Base):
    __tablename__ = 'rdm_tokens'
    id = Column(Integer, primary_key=True, index=True)
    service_url = Column(String, index=True)
    token = Column(String, index=True)
    created_at = Column(DateTime, index=True)
    expired_at = Column(DateTime, nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates='rdm_tokens')
