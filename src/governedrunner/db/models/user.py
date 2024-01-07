from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), index=True)
    updated_at = Column(DateTime(timezone=True), index=True)

    rdm_token = relationship(
        'RDMToken',
        back_populates='owner',
        uselist=False,
    )

class RDMToken(Base):
    __tablename__ = 'rdm_tokens'
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, index=True)
    token = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), index=True)
    expired_at = Column(DateTime(timezone=True), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates='rdm_token')
