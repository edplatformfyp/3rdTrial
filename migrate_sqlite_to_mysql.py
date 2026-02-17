
import sqlite3
import mysql.connector
import os
import json
from dotenv import load_dotenv

load_dotenv()

# MySQL Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "educore")

SQLITE_DB = "educore.db"

def get_sqlite_connection():
    return sqlite3.connect(SQLITE_DB)

def get_mysql_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME
    )

def migrate_table(sqlite_conn, mysql_conn, table_name, columns):
    print(f"Migrating table: {table_name}...")
    
    # Read from SQLite
    try:
        sqlite_cursor = sqlite_conn.cursor()
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        sqlite_cursor.execute(query)
        rows = sqlite_cursor.fetchall()
    except sqlite3.OperationalError:
         print(f"Skipping {table_name} (table not found in SQLite)")
         return

    if not rows:
        print(f"No data in {table_name}. Skipping.")
        return

    # Write to MySQL
    mysql_cursor = mysql_conn.cursor()
    
    # Prepare INSERT statement
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    # Disable foreign key checks temporarily to avoid constraint issues during bulk insert
    mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    
    try:
        # We need to handle JSON fields if any (convert strings to json strings if needed? 
        # SQLite stores JSON as TEXT. MySQL JSON column might expect proper JSON string.
        # Connector usually handles string -> JSON column fine.)
        
        mysql_cursor.executemany(insert_query, rows)
        mysql_conn.commit()
        print(f"Successfully migrated {len(rows)} rows to {table_name}.")
    except mysql.connector.Error as err:
        print(f"Error migrating {table_name}: {err}")
    finally:
        mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        mysql_cursor.close()

def create_tables_if_not_exist():
    # Use SQLAlchemy to create tables in MySQL
    print("Creating tables in MySQL using SQLAlchemy...")
    from server.database import engine
    from server import models
    models.Base.metadata.create_all(bind=engine)
    print("Tables created (if they didn't exist).")

def main():
    if not os.path.exists(SQLITE_DB):
        print(f"SQLite database {SQLITE_DB} not found.")
        return

    # 1. Create Tables
    try:
        create_tables_if_not_exist()
    except Exception as e:
        print(f"Failed to create tables: {e}")
        return

    sqlite_conn = get_sqlite_connection()
    try:
        mysql_conn = get_mysql_connection()
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        return

    # 2. Migrate Data in Order of Dependencies
    
    # Organizations
    migrate_table(sqlite_conn, mysql_conn, "organizations", ["id", "name", "code"])
    
    # Users
    migrate_table(sqlite_conn, mysql_conn, "users", ["id", "username", "email", "hashed_password", "role", "is_active", "organization_id", "parent_id"])
    
    # Courses
    # Note: roadmap_json is JSON
    migrate_table(sqlite_conn, mysql_conn, "courses", ["id", "topic", "grade_level", "roadmap_json", "description", "structure_type", "is_published", "organization_id", "user_id"])
    
    # Chapters
    # quiz_json is JSON
    migrate_table(sqlite_conn, mysql_conn, "chapters", ["id", "chapter_number", "order_index", "title", "content_markdown", "quiz_json", "video_url", "course_id"])
    
    # Notes
    migrate_table(sqlite_conn, mysql_conn, "notes", ["id", "content", "created_at", "updated_at", "user_id", "course_id"])
    
    # Enrollments
    migrate_table(sqlite_conn, mysql_conn, "enrollments", ["id", "user_id", "course_id", "progress", "joined_at"])
    
    # TestResults
    migrate_table(sqlite_conn, mysql_conn, "test_results", ["id", "score", "total_score", "timestamp", "proctor_logs", "user_id", "course_id"])

    sqlite_conn.close()
    mysql_conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    main()
