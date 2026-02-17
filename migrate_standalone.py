
import sqlite3
import mysql.connector
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, text

load_dotenv()

# MySQL Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "educore")

print(f"DEBUG: Loaded credentials: User={DB_USER}, Password={DB_PASSWORD}, DB={DB_NAME}", flush=True)

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

    mysql_cursor = mysql_conn.cursor()
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    try:
        mysql_cursor.executemany(insert_query, rows)
        mysql_conn.commit()
        print(f"Successfully migrated {len(rows)} rows to {table_name}.")
    except mysql.connector.Error as err:
        print(f"Error migrating {table_name}: {err}")
    finally:
        mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        mysql_cursor.close()

def create_tables_manual():
    # Use SQLAlchemy to create tables, but define engine LOCALLY via models base
    print("Creating tables in MySQL...")
    
    database_url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(database_url, echo=True)
    
    # Import models here to register them with Base
    # We assume server.models imports server.database.Base
    from server import models
    from server.database import Base
    
    # Test connection first
    print("Testing connection before create_all...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connection test SUCCESS.")
    except Exception as e:
        print(f"Connection test FAILED: {e}")
        return

    # Bind the engine to the metadata of Base
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created.")
    except Exception as e:
        print(f"create_all FAILED: {e}")


def main():
    if not os.path.exists(SQLITE_DB):
        print(f"SQLite database {SQLITE_DB} not found.")
        return

    try:
        create_tables_manual()
    except Exception as e:
        print(f"Failed to create tables: {e}")
        print(f"DEBUG ON ERROR: User={DB_USER}, Password={DB_PASSWORD}, DB={DB_NAME}")
        return

    # 2. Migrate Data
    sqlite_conn = get_sqlite_connection()
    try:
        mysql_conn = get_mysql_connection()
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        return
    
    # Order matches previous script
    migrate_table(sqlite_conn, mysql_conn, "organizations", ["id", "name", "code"])
    migrate_table(sqlite_conn, mysql_conn, "users", ["id", "username", "email", "hashed_password", "role", "is_active", "organization_id", "parent_id"])
    migrate_table(sqlite_conn, mysql_conn, "courses", ["id", "topic", "grade_level", "roadmap_json", "description", "structure_type", "is_published", "organization_id", "user_id"])
    migrate_table(sqlite_conn, mysql_conn, "chapters", ["id", "chapter_number", "order_index", "title", "content_markdown", "quiz_json", "video_url", "course_id"])
    migrate_table(sqlite_conn, mysql_conn, "notes", ["id", "content", "created_at", "updated_at", "user_id", "course_id"])
    migrate_table(sqlite_conn, mysql_conn, "enrollments", ["id", "user_id", "course_id", "progress", "joined_at"])
    migrate_table(sqlite_conn, mysql_conn, "test_results", ["id", "score", "total_score", "timestamp", "proctor_logs", "user_id", "course_id"])

    sqlite_conn.close()
    mysql_conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    main()
