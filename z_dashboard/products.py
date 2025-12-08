from fastapi import APIRouter, HTTPException, Body, Depends, Header
from typing import List, Optional
from z_dashboard.dash_models import ProductModel
# from database import get_database
from bson import ObjectId
from z_chatbot_module.db import db
from z_chatbot_module._auth_firebase import auth_user_fb
from starlette.status import HTTP_401_UNAUTHORIZED

prrouter = APIRouter(prefix="/prods")

@prrouter.get("/products", response_model=List[ProductModel])
async def get_products(user=Depends(auth_user_fb)):
    pdb = await db()
    products = await pdb["products"].   find({"uid": user["uid"]}).to_list(1000)
    return products

@prrouter.post("/products", response_model=ProductModel)
async def add_product(product: ProductModel = Body(...), user=Depends(auth_user_fb)):
    pdb = await db()
    product_dict = product.dict(by_alias=True, exclude={"id"})
    product_dict['uid'] = user['uid']
    new_product = await pdb["products"].insert_one(product_dict)
    created_product = await pdb["products"].find_one({"_id": new_product.inserted_id, "uid": user["uid"]})
    return created_product

@prrouter.delete("/products/{id}")
async def delete_product(id: str, user=Depends(auth_user_fb)):
    pdb = await db()
    delete_result = await pdb["products"].delete_one({"_id": ObjectId(id), "uid": user["uid"]})
    if delete_result.deleted_count == 1:
        return {"message": "Product deleted"}
    raise HTTPException(status_code=404, detail="Product not found")