from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import Base


class Interaction(Base):
    """User-Product interaction tracking"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # interaction type: 'view', 'cart', 'purchase', 'wishlist', 'rating'
    interaction_type = Column(String, nullable=False, index=True)
    
    # implicit feedback (engagement strength)
    weight = Column(Float, default=1.0)  # 1.0 = view, 2.0 = cart, 5.0 = purchase
    
    # explicit feedback
    rating = Column(Float, nullable=True)  # 1-5 stars
    
    # context
    session_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # composite index for common queries
    __table_args__ = (
        Index('ix_user_product', 'user_id', 'product_id'),
        Index('ix_user_timestamp', 'user_id', 'timestamp'),
    )


class InteractionCreate(BaseModel):
    """Schema for creating interactions"""
    user_id: int
    product_id: int
    interaction_type: str  # 'view', 'cart', 'purchase', 'wishlist', 'rating'
    rating: Optional[float] = None
    session_id: Optional[str] = None


class InteractionSchema(BaseModel):
    """Schema for API responses"""
    id: int
    user_id: int
    product_id: int
    interaction_type: str
    weight: float
    rating: Optional[float]
    timestamp: datetime
    
    class Config:
        from_attributes = True