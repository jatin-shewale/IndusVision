"""
IndusVision Backend - MongoDB Connection (Motor async driver)
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# Collections (used across routes/services)
users_collection = db["users"]
machines_collection = db["machines"]
sensor_readings_collection = db["sensor_readings"]
detections_collection = db["detections"]
inventory_collection = db["inventory"]
suppliers_collection = db["suppliers"]
orders_collection = db["orders"]
alerts_collection = db["alerts"]
maintenance_collection = db["maintenance"]
reports_collection = db["reports"]
activity_logs_collection = db["activity_logs"]


async def ensure_indexes():
    """Create indexes for performance + uniqueness. Called once on startup."""
    await users_collection.create_index("email", unique=True)
    await machines_collection.create_index("machine_id", unique=True)
    await sensor_readings_collection.create_index([("machine_id", 1), ("timestamp", -1)])
    await detections_collection.create_index([("camera_id", 1), ("timestamp", -1)])
    await inventory_collection.create_index("item_name")
    await alerts_collection.create_index([("status", 1), ("created_at", -1)])
    await maintenance_collection.create_index("machine_id")
