
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    product_name: str
    price: float
    description: Optional[str] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    price: float
    description: Optional[str] = None
    created_date: date
