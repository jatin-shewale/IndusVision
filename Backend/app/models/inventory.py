"""
IndusVision Backend - Inventory Models
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

ItemCategory = Literal["raw_material", "finished_goods", "scrap"]


class InventoryItemCreate(BaseModel):
    item_name: str
    category: ItemCategory = "raw_material"
    quantity: float
    unit: str = "kg"
    threshold: float = 10
    supplier_id: Optional[str] = None
    barcode: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    threshold: Optional[float] = None
    supplier_id: Optional[str] = None


class InventoryItemOut(InventoryItemCreate):
    id: str
    updated_at: datetime
    low_stock: bool = False


class SupplierCreate(BaseModel):
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class SupplierOut(SupplierCreate):
    id: str


class PurchaseOrderCreate(BaseModel):
    item_id: str
    supplier_id: str
    quantity: float
    notes: Optional[str] = None


class PurchaseOrderOut(PurchaseOrderCreate):
    id: str
    status: Literal["pending", "approved", "delivered", "cancelled"] = "pending"
    created_at: datetime
