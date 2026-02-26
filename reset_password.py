from pymongo import MongoClient
from passlib.context import CryptContext
import os

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "educore"

# Setup Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    username = "Rahul"
    new_password = "password123"
    hashed_password = get_password_hash(new_password)
    
    result = db.users.update_one(
        {"username": username},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    if result.modified_count > 0:
        print(f"Password for user '{username}' successfully reset to '{new_password}'.")
    else:
        print(f"User '{username}' found, but password was not updated (maybe it was same?).")
        # Check if matched
        if result.matched_count == 0:
             print(f"User '{username}' NOT FOUND.")

except Exception as e:
    print(f"Error: {e}")
