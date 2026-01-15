import os
import sys

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2 is not installed. Please run 'pip install psycopg2-binary' first.")
    sys.exit(1)

# Default config
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres") # Default for many installs
DB_NAME = "saas_ai"

def get_conn(dbname=None):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=dbname
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("Please check your credentials and ensure PostgreSQL is running.")
        return None

def setup_database():
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    
    # 1. Create Database
    conn = get_conn("postgres")
    if not conn:
        sys.exit(1)
        
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if cur.fetchone():
            print(f"Database '{DB_NAME}' already exists.")
        else:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")
    finally:
        cur.close()
        conn.close()

    # 2. Init Schema
    print(f"Initializing schema for '{DB_NAME}'...")
    conn = get_conn(DB_NAME)
    if not conn:
        print(f"Could not connect to '{DB_NAME}'.")
        sys.exit(1)
        
    try:
        cur = conn.cursor()
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")
        if not os.path.exists(schema_path):
             print(f"Schema file not found at {schema_path}")
             sys.exit(1)
             
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        cur.execute(schema_sql)
        conn.commit()
        print("Schema initialized successfully (including pgvector extension).")
        
    except Exception as e:
        print(f"Error initializing schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
