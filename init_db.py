"""
Database initialization script
Run this once to set up your PostgreSQL database schema
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Initialize the database with the schema"""
    # Load individual connection parameters
    user = os.getenv('user')
    password = os.getenv('password')
    host = os.getenv('host')
    port = os.getenv('port')
    dbname = os.getenv('dbname')
    
    if not all([user, password, host, port, dbname]):
        print("ERROR: Missing database connection parameters!")
        print("Please add user, password, host, port, and dbname to your .env file")
        return False
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname
        )
        cur = conn.cursor()
        
        print("Reading schema.sql...")
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        print("Executing schema...")
        cur.execute(schema_sql)
        conn.commit()
        
        print("Schema created successfully!")
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verify indexes were created
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY indexname;
        """)
        
        indexes = cur.fetchall()
        print("\nCreated indexes:")
        for index in indexes:
            print(f"  - {index[0]}")
        
        cur.close()
        conn.close()
        
        print("\nDatabase initialization complete!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("Database Initialization")
    print("="*50)
    init_database()

