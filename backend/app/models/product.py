from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import Base


class Product(Base):
    """Product database model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(String)
    tags = Column(JSON)  # store as JSON array
    image_url = Column(String)
    rating = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "description": self.description,
            "tags": self.tags or [],
            "image_url": self.image_url,
            "rating": self.rating,
            "stock": self.stock
        }


class ProductSchema(BaseModel):
    """Pydantic schema for API responses"""
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    tags: List[str] = []
    image_url: Optional[str] = None
    rating: float = 0.0
    stock: int = 0
    
    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Schema for creating products"""
    name: str
    category: str
    price: float
    description: Optional[str] = None
    tags: List[str] = []
    image_url: Optional[str] = None
    rating: float = 0.0
    stock: int = 0