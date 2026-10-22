"""
IndusVision Backend - Seed Sample Data
==========================================
Creates a first admin user, sample machines, inventory items, and a supplier
so the frontend has something to show immediately.

RUN (from backend/ folder, with MongoDB running and .env configured):
    python seed_data.py
"""
import asyncio
from datetime import datetime, timezone

from app.database import users_collection, machines_collection, inventory_collection, suppliers_collection
from app.core.security import hash_password


async def seed():
    # --- Admin user ---
    if await users_collection.count_documents({}) == 0:
        await users_collection.insert_one({
            "name": "Admin User",
            "email": "admin@indusvision.local",
            "password_hash": hash_password("Admin@123"),
            "role": "admin",
            "department": "Management",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        })
        print("Created admin: admin@indusvision.local / Admin@123  (CHANGE THIS PASSWORD)")
    else:
        print("Users already exist — skipping admin creation.")

    # Remove the two extra demo machines created by earlier versions of this
    # seed script; this installation has one physical ESP32 machine.
    removed = await machines_collection.delete_many({"machine_id": {"$in": ["MACHINE_02", "MACHINE_03"]}})
    if removed.deleted_count:
        print(f"Removed {removed.deleted_count} old demo machines (MACHINE_02/03).")

    # --- The one machine connected to the ESP32 ---
    sample_machines = [
        {"machine_id": "MACHINE_01", "name": "ESP32 Monitored Machine", "location": "Bay A", "machine_type": "IoT monitored equipment"},
    ]
    for m in sample_machines:
        existing = await machines_collection.find_one({"machine_id": m["machine_id"]})
        if not existing:
            m["status"] = "offline"
            m["health_score"] = None
            m["last_seen"] = None
            m["created_at"] = datetime.now(timezone.utc)
            await machines_collection.insert_one(m)
    print(f"Ensured {len(sample_machines)} sample machines exist.")

    # --- Sample supplier ---
    supplier_doc = {"name": "SteelWorks Pvt Ltd", "contact_email": "orders@steelworks.example",
                     "contact_phone": "+91-9000000000", "address": "Industrial Area, Pune"}
    existing_supplier = await suppliers_collection.find_one({"name": supplier_doc["name"]})
    supplier_id = existing_supplier["_id"] if existing_supplier else (await suppliers_collection.insert_one(supplier_doc)).inserted_id
    print("Ensured sample supplier exists.")

    # --- Sample inventory ---
    sample_items = [
        {"item_name": "Steel Sheet 2mm", "category": "raw_material", "quantity": 120, "unit": "sheets", "threshold": 30, "supplier_id": str(supplier_id)},
        {"item_name": "Machine Oil", "category": "raw_material", "quantity": 8, "unit": "liters", "threshold": 10, "supplier_id": str(supplier_id)},
        {"item_name": "Finished Bracket A", "category": "finished_goods", "quantity": 500, "unit": "units", "threshold": 100, "supplier_id": None},
        {"item_name": "Scrap Metal", "category": "scrap", "quantity": 45, "unit": "kg", "threshold": 200, "supplier_id": None},
    ]
    for item in sample_items:
        existing = await inventory_collection.find_one({"item_name": item["item_name"]})
        if not existing:
            item["updated_at"] = datetime.now(timezone.utc)
            await inventory_collection.insert_one(item)
    print(f"Ensured {len(sample_items)} sample inventory items exist (Machine Oil is intentionally below threshold to demo low-stock alerts).")

    print("\nSeeding complete. Start the API with: uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(seed())
