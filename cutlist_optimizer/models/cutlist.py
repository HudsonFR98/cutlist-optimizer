import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship

from cutlist_optimizer.lib.database import Base, DBSession

log = logging.getLogger(__name__)


class Cutlist(Base):
    """Cutlist model linked to a user"""
    __tablename__ = 'cutlists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='cutlists')
    surfaces = relationship('Surface', back_populates='cutlist', cascade='all, delete-orphan')
    
    def __init__(self, user_id, name=None):
        self.user_id = user_id
        self.name = name
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def __str__(self):
        return f"Cutlist {self.id} - {self.name or 'Unnamed'}"
    
    def to_dict(self):
        """Convert cutlist to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'surfaces': [surface.to_dict() for surface in self.surfaces]
        }


class Surface(Base):
    """2D surface model with height and width in mm"""
    __tablename__ = 'surfaces'
    
    id = Column(Integer, primary_key=True)
    cutlist_id = Column(Integer, ForeignKey('cutlists.id'), nullable=False, index=True)
    width = Column(Numeric(10, 2), nullable=False)  # Width in mm
    height = Column(Numeric(10, 2), nullable=False)  # Height in mm
    quantity = Column(Integer, nullable=False, default=1)  # Number of pieces needed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    cutlist = relationship('Cutlist', back_populates='surfaces')
    
    def __init__(self, cutlist_id, width, height, quantity=1):
        self.cutlist_id = cutlist_id
        self.width = float(width)
        self.height = float(height)
        self.quantity = int(quantity)
        self.created_at = datetime.utcnow()
    
    def __str__(self):
        return f"Surface {self.width}x{self.height}mm (x{self.quantity})"
    
    def to_dict(self):
        """Convert surface to dictionary"""
        return {
            'id': self.id,
            'cutlist_id': self.cutlist_id,
            'width': float(self.width),
            'height': float(self.height),
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def area(self):
        """Calculate surface area in mm²"""
        return float(self.width) * float(self.height)


# Add query properties to models
Cutlist.query = DBSession.query_property()
Surface.query = DBSession.query_property()

# Ensure models are exported
__all__ = ['Cutlist', 'Surface']
