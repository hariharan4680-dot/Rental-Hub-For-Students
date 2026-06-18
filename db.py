import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Load .env file
load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")

print(f"🔎 Loaded MONGO_URI: {mongo_uri}")  # <--- DEBUG PRINT
print(f"🔎 Loaded DB_NAME: {db_name}")

try:
    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    db = client[db_name]
    print(f"✅ Connected to MongoDB: {db_name}")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    db = None
