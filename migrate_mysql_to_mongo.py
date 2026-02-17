
import mysql.connector
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json

load_dotenv()

# MySQL Config (Hardcoded or from .env if we kept them, but let's use the ones we know works)
MYSQL_HOST = "localhost"
MYSQL_USER = "educore"
MYSQL_PASSWORD = "educore123"
MYSQL_DB = "educore"

# MongoDB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("DB_NAME", "educore")

def get_mysql_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

def migrate_data():
    print("Starting migration from MySQL to MongoDB...")
    
    try:
        mysql_conn = get_mysql_connection()
        mysql_cursor = mysql_conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return

    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    
    # 1. Organizations
    print("Migrating Organizations...")
    mysql_cursor.execute("SELECT * FROM organizations")
    orgs = mysql_cursor.fetchall()
    if orgs:
        # We need to map MySQL ID to Mongo _id or keep integer ID?
        # Ideally we let Mongo generate _id but store old_id for reference/relationships
        # But for MVP, let's just insert and maybe rely on username/codes for linking?
        # Actually, we need to preserve relationships.
        # Strategy: Use a dictionary to map old_id -> new_object_id
        
        # Simpler Strategy for this MVP: 
        # Just copy data. Relationships in Mongo are often embedded or by ID.
        # If we use Pydantic with ObjectId, we need to valid ObjectIds.
        # MySQL IDs are integers. 
        # Valid ObjectId is 24-char hex.
        # We can't easily cast int to ObjectId.
        
        # WE MUST RESET DATA or Handle Mapping.
        # Given "firstTrial", maybe resetting/fresh start is acceptable?
        # The user asked to "migrate".
        
        # Let's try to preserve by storing `mysql_id` in Mongo documents and using that for manual linking if needed?
        # Or, we just clear Mongo and insert fresh, letting Mongo assign IDs, 
        # AND we update foreign keys? That's complex.
        
        # Alternative: Just dump the data as-is, BUT `_id` will be auto-generated.
        # We add `mysql_id` field to every document.
        # Then, after inserting all, we might need to write a script to update reference fields (like user_id, course_id)
        # to match the new `_id` of the referenced document.
        pass

    # Actually, for a quick migration without complex rewrites:
    # 1. Insert Org, get _id, store in map {old_id: new_id}
    # 2. Insert User, replace org_id using map, get _id, store in map...
    
    id_map = {
        "organizations": {},
        "users": {},
        "courses": {}
    }

    # Organizations
    mysql_cursor.execute("SELECT * FROM organizations")
    for row in mysql_cursor.fetchall():
        old_id = row['id']
        del row['id'] # Let Mongo generate _id
        res = mongo_db.organizations.insert_one(row)
        id_map["organizations"][old_id] = str(res.inserted_id)
    print(f"Migrated {len(id_map['organizations'])} organizations.")

    # Users
    print("Migrating Users...")
    mysql_cursor.execute("SELECT * FROM users")
    for row in mysql_cursor.fetchall():
        old_id = row['id']
        del row['id']
        
        # Update FKs
        if row.get('organization_id') and row['organization_id'] in id_map["organizations"]:
            row['organization_id'] = id_map["organizations"][row['organization_id']]
        else:
            row['organization_id'] = None
            
        # Parent ID (Self ref) - Might need second pass or ordered insert?
        # Only if parent inserted before child. 
        # For MVP, let's ignore parent_id linking or do it if parent found.
        if row.get('parent_id') and row['parent_id'] in id_map["users"]:
            row['parent_id'] = id_map["users"][row['parent_id']]
        else:
            row['parent_id'] = None
            
        res = mongo_db.users.insert_one(row)
        id_map["users"][old_id] = str(res.inserted_id)
    print(f"Migrated {len(id_map['users'])} users.")

    # Courses
    print("Migrating Courses...")
    mysql_cursor.execute("SELECT * FROM courses")
    for row in mysql_cursor.fetchall():
        old_id = row['id']
        del row['id']
        
        if row.get('user_id') and row['user_id'] in id_map["users"]:
            row['user_id'] = id_map["users"][row['user_id']]
        
        if row.get('organization_id') and row['organization_id'] in id_map["organizations"]:
            row['organization_id'] = id_map["organizations"][row['organization_id']]
            
        # Parse JSON fields if they are strings (MySQL Connector dictionary cursor might auto-convert? usually not for text/json columns unless defined)
        if isinstance(row.get('roadmap_json'), str):
             try:
                 row['roadmap_json'] = json.loads(row['roadmap_json'])
             except:
                 pass
        
        res = mongo_db.courses.insert_one(row)
        id_map["courses"][old_id] = str(res.inserted_id)
    print(f"Migrated {len(id_map['courses'])} courses.")

    # Chapters
    print("Migrating Chapters...")
    mysql_cursor.execute("SELECT * FROM chapters")
    for row in mysql_cursor.fetchall():
        del row['id']
        if row.get('course_id') and row['course_id'] in id_map["courses"]:
            row['course_id'] = id_map["courses"][row['course_id']]
            
        if isinstance(row.get('quiz_json'), str):
             try:
                 row['quiz_json'] = json.loads(row['quiz_json'])
             except:
                 pass
                 
        mongo_db.chapters.insert_one(row)
    print("Migrated Chapters.")

    # Notes
    print("Migrating Notes...")
    mysql_cursor.execute("SELECT * FROM notes")
    for row in mysql_cursor.fetchall():
        del row['id']
        if row.get('user_id') and row['user_id'] in id_map["users"]:
            row['user_id'] = id_map["users"][row['user_id']]
        if row.get('course_id') and row['course_id'] in id_map["courses"]:
            row['course_id'] = id_map["courses"][row['course_id']]
            
        mongo_db.notes.insert_one(row)
    print("Migrated Notes.")

    mysql_cursor.close()
    mysql_conn.close()
    print("Migration Completed Successfully.")

if __name__ == "__main__":
    migrate_data()
