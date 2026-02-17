
import sqlite3
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json

load_dotenv()

SQLITE_DB = "educore.db"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("DB_NAME", "educore")

def get_sqlite_connection():
    return sqlite3.connect(SQLITE_DB)

def migrate_data():
    if not os.path.exists(SQLITE_DB):
         print(f"SQLite DB {SQLITE_DB} not found.")
         return

    print("Starting migration from SQLite to MongoDB...")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_conn.row_factory = sqlite3.Row # Access columns by name
    sqlite_cursor = sqlite_conn.cursor()

    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    
    # Clear existing collections?
    # mongo_db.organizations.drop()
    # mongo_db.users.drop()
    # mongo_db.courses.drop()
    # mongo_db.chapters.drop()
    # mongo_db.notes.drop()
    
    id_map = {
        "organizations": {},
        "users": {},
        "courses": {}
    }

    # Organizations
    try:
        sqlite_cursor.execute("SELECT * FROM organizations")
        rows = sqlite_cursor.fetchall()
        print(f"Found {len(rows)} organizations.")
        for row in rows:
            data = dict(row)
            old_id = data['id']
            del data['id']
            res = mongo_db.organizations.insert_one(data)
            id_map["organizations"][old_id] = str(res.inserted_id)
    except Exception as e:
        print(f"Error migrating organizations: {e}")

    # Users
    try:
        sqlite_cursor.execute("SELECT * FROM users")
        rows = sqlite_cursor.fetchall()
        print(f"Found {len(rows)} users.")
        for row in rows:
            data = dict(row)
            old_id = data['id']
            del data['id']
            
            if data.get('organization_id') and data['organization_id'] in id_map["organizations"]:
                data['organization_id'] = id_map["organizations"][data['organization_id']]
            else:
                data['organization_id'] = None
            
            # Helper for boolean
            data['is_active'] = bool(data['is_active'])

            res = mongo_db.users.insert_one(data)
            id_map["users"][old_id] = str(res.inserted_id)
    except Exception as e:
        print(f"Error migrating users: {e}")

    # Courses
    try:
        sqlite_cursor.execute("SELECT * FROM courses")
        rows = sqlite_cursor.fetchall()
        print(f"Found {len(rows)} courses.")
        for row in rows:
            data = dict(row)
            old_id = data['id']
            del data['id']
            
            if data.get('user_id') and data['user_id'] in id_map["users"]:
                data['user_id'] = id_map["users"][data['user_id']]
                
            if data.get('organization_id') and data['organization_id'] in id_map["organizations"]:
                data['organization_id'] = id_map["organizations"][data['organization_id']]
                
            if isinstance(data.get('roadmap_json'), str):
                 try:
                     data['roadmap_json'] = json.loads(data['roadmap_json'])
                 except:
                     pass
            
            data['is_published'] = bool(data['is_published'])

            res = mongo_db.courses.insert_one(data)
            id_map["courses"][old_id] = str(res.inserted_id)
    except Exception as e:
        print(f"Error migrating courses: {e}")

    # Chapters
    try:
        sqlite_cursor.execute("SELECT * FROM chapters")
        rows = sqlite_cursor.fetchall()
        print(f"Found {len(rows)} chapters.")
        for row in rows:
            data = dict(row)
            del data['id']
            
            if data.get('course_id') and data['course_id'] in id_map["courses"]:
                data['course_id'] = id_map["courses"][data['course_id']]
                
            if isinstance(data.get('quiz_json'), str):
                 try:
                     data['quiz_json'] = json.loads(data['quiz_json'])
                 except:
                     pass
                     
            mongo_db.chapters.insert_one(data)
    except Exception as e:
        print(f"Error migrating chapters: {e}")

    # Notes
    try:
        sqlite_cursor.execute("SELECT * FROM notes")
        rows = sqlite_cursor.fetchall()
        print(f"Found {len(rows)} notes.")
        for row in rows:
            data = dict(row)
            del data['id']
            
            if data.get('user_id') and data['user_id'] in id_map["users"]:
                data['user_id'] = id_map["users"][data['user_id']]
            if data.get('course_id') and data['course_id'] in id_map["courses"]:
                data['course_id'] = id_map["courses"][data['course_id']]
                
            mongo_db.notes.insert_one(data)
    except Exception as e:
        print(f"Error migrating notes: {e}")

    sqlite_conn.close()
    print("Migration from SQLite to MongoDB Completed.")

if __name__ == "__main__":
    migrate_data()
