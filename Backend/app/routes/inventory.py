"""
IndusVision Backend - Inventory Routes (Module 6)
"""
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.database import inventory_collection, suppliers_collection, orders_collection
from app.core.dependencies import get_current_user, require_roles
from app.models.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemOut,
    SupplierCreate, SupplierOut, PurchaseOrderCreate, PurchaseOrderOut,
)
from app.services.alert_service import create_alert

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def _item_out(doc: dict) -> dict:
    low_stock = doc["quantity"] <= doc["threshold"]
    return {**{k: v for k, v in doc.items() if k != "_id"}, "id": str(doc["_id"]), "low_stock": low_stock}


@router.post("/items", response_model=InventoryItemOut, status_code=201)
async def create_item(item: InventoryItemCreate, current_user: dict = Depends(require_roles("admin", "engineer", "supervisor"))):
    doc = item.model_dump()
    doc["updated_at"] = datetime.now(timezone.utc)
    result = await inventory_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _item_out(doc)


@router.get("/items", response_model=list[InventoryItemOut])
async def list_items(low_stock_only: bool = False, current_user: dict = Depends(get_current_user)):
    docs = await inventory_collection.find().to_list(1000)
    items = [_item_out(d) for d in docs]
    if low_stock_only:
        items = [i for i in items if i["low_stock"]]
    return items


@router.patch("/items/{item_id}", response_model=InventoryItemOut)
async def update_item(item_id: str, update: InventoryItemUpdate,
                       current_user: dict = Depends(require_roles("admin", "engineer", "supervisor", "operator"))):
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid item id")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)

    doc = await inventory_collection.find_one_and_update(
        {"_id": oid}, {"$set": update_data}, return_document=True
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")

    # Auto-reorder alert
    if doc["quantity"] <= doc["threshold"]:
        await create_alert(
            title=f"Low stock: {doc['item_name']}",
            message=f"Quantity {doc['quantity']} {doc['unit']} is at or below threshold {doc['threshold']} {doc['unit']}.",
            severity="warning",
            source="inventory",
        )

    return _item_out(doc)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str, current_user: dict = Depends(require_roles("admin"))):
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid item id")
    result = await inventory_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")


# ---------------- Suppliers ----------------
@router.post("/suppliers", response_model=SupplierOut, status_code=201)
async def create_supplier(supplier: SupplierCreate, current_user: dict = Depends(require_roles("admin", "engineer"))):
    doc = supplier.model_dump()
    result = await suppliers_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {**{k: v for k, v in doc.items() if k != "_id"}, "id": str(doc["_id"])}


@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(current_user: dict = Depends(get_current_user)):
    docs = await suppliers_collection.find().to_list(500)
    return [{**{k: v for k, v in d.items() if k != "_id"}, "id": str(d["_id"])} for d in docs]


# ---------------- Purchase Orders ----------------
@router.post("/orders", response_model=PurchaseOrderOut, status_code=201)
async def create_order(order: PurchaseOrderCreate, current_user: dict = Depends(require_roles("admin", "engineer", "supervisor"))):
    doc = order.model_dump()
    doc["status"] = "pending"
    doc["created_at"] = datetime.now(timezone.utc)
    result = await orders_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {**{k: v for k, v in doc.items() if k != "_id"}, "id": str(doc["_id"])}


@router.get("/orders", response_model=list[PurchaseOrderOut])
async def list_orders(current_user: dict = Depends(get_current_user)):
    docs = await orders_collection.find().sort("created_at", -1).to_list(500)
    return [{**{k: v for k, v in d.items() if k != "_id"}, "id": str(d["_id"])} for d in docs]
