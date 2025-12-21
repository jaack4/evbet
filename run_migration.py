#!/usr/bin/env python3
"""
Script to run the unique constraint migration on Railway database
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration to add unique constraint"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please check your .env file")
        return False
    
    print("Connecting to Railway database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("Connected successfully!")
        print("\n" + "="*60)
        print("Running migration: Add unique constraint to ev_bets")
        print("="*60 + "\n")
        
        # Step 1: Check for existing duplicates
        print("Step 1: Checking for existing duplicates...")
        cur.execute("""
            SELECT COUNT(*) 
            FROM (
                SELECT game_id, bookmaker, market, player, outcome, betting_line, COUNT(*) as cnt
                FROM ev_bets
                GROUP BY game_id, bookmaker, market, player, outcome, betting_line
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        duplicate_groups = cur.fetchone()[0]
        
        if duplicate_groups > 0:
            print(f"Found {duplicate_groups} duplicate bet groups that will be cleaned up")
            
            # Remove duplicates in a more thorough way
            # Keep only the record with the MAX id for each unique combination
            print("Removing duplicates (this may take a moment)...")
            cur.execute("""
                DELETE FROM ev_bets
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM ev_bets
                    GROUP BY game_id, bookmaker, market, player, outcome, betting_line
                )
            """)
            deleted_count = cur.rowcount
            print(f"Removed {deleted_count} duplicate records")
            
            # Commit the deletion before adding constraint
            conn.commit()
            print("Duplicates removed successfully")
        else:
            print("No duplicates found - database is clean!")
        
        # Step 2: Add the unique constraint
        print("\nStep 2: Adding unique constraint...")
        try:
            cur.execute("""
                ALTER TABLE ev_bets 
                ADD CONSTRAINT unique_bet_per_bookmaker 
                UNIQUE (game_id, bookmaker, market, player, outcome, betting_line)
            """)
            print("Unique constraint added successfully!")
        except psycopg2.errors.DuplicateTable as e:
            if "already exists" in str(e):
                print("Constraint already exists - skipping")
                conn.rollback()
            else:
                raise
        
        # Step 3: Verify the constraint
        print("\nStep 3: Verifying constraint...")
        cur.execute("""
            SELECT conname, contype, conrelid::regclass
            FROM pg_constraint
            WHERE conname = 'unique_bet_per_bookmaker'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"✓ Constraint verified: {result[0]} on table {result[2]}")
        else:
            print("✗ Warning: Could not verify constraint")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        
        # Close connection
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Migration failed!")
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Railway Database Migration Tool")
    print("="*60 + "\n")
    
    success = run_migration()
    
    if success:
        print("\n✓ Your database is now configured to prevent duplicate bets!")
    else:
        print("\n✗ Migration failed. Please check the error messages above.")
        exit(1)

