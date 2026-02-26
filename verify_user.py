from pymongo import MongoClient
import os

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "educore"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB: {MONGO_URI}")
    print(f"Database: {DB_NAME}")
    
    user_count = db.users.count_documents({})
    print(f"Total Users: {user_count}")
    
    username = "Rahul"
    user = db.users.find_one({"username": username})
    
    if user:
        print(f"User '{username}' FOUND.")
        print(f"ID: {user['_id']}")
        print(f"Role: {user.get('role')}")
        print(f"Has Password Hash: {'Yes' if user.get('hashed_password') else 'No'}")
    else:
        print(f"User '{username}' NOT FOUND.")
        
except Exception as e:
    print(f"Error: {e}")
