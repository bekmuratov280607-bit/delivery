
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

app = FastAPI()


class ProductCreate(BaseModel):
    product_name: str
    price: float
    description: str


product_id = 0


@app.post("/products/")
def create_product(data: ProductCreate):
    global product_id
    product_id += 1

    return {
        "id": product_id,
        "product_name": data.product_name,
        "price": data.price,
        "description": data.description,
        "created_date": date.today().isoformat()
    }
