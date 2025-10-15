from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict
from app.database import Base


class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    preferences = Column(JSON)  # stored preferences
    behavioral_profile = Column(JSON)  # computed behavioral DNA
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "preferences": self.preferences or {},
            "behavioral_profile": self.behavioral_profile or {}
        }


class UserSchema(BaseModel):
    """Pydantic schema for API responses"""
    id: int
    email: str
    name: str
    preferences: Optional[Dict] = {}
    behavioral_profile: Optional[Dict] = {}
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating users"""
    email: str
    name: str
    preferences: Dict = {}