"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Tee(BaseModel):
    """
    T-shirts collection schema
    Collection name: "tee"
    """
    title: str = Field(..., description="Product title")
    slug: str = Field(..., description="URL-friendly identifier")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    release_year: int = Field(..., ge=2000, le=2100, description="Release year")
    release_month: int = Field(..., ge=1, le=12, description="Release month (1-12)")

class Subscription(BaseModel):
    """
    Email subscriptions for new batch releases
    Collection name: "subscription"
    """
    email: EmailStr = Field(..., description="Subscriber email")
    name: Optional[str] = Field(None, description="Subscriber name")
    source: Optional[str] = Field("website", description="Signup source")
