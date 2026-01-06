#!/usr/bin/env python3
"""
Run database migrations against Supabase PostgreSQL.

Usage:
    python scripts/run_migrations.py
"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

def run_migrations():
    """Run all migration files."""
    import asyncio
    import asyncpg
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory not found: {migrations_dir}")
        return False
    
    # Get all SQL files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found")
        return True
    
    print(f"Found {len(migration_files)} migration file(s)")
    
    async def execute_migrations():
        # Connect to database
        print(f"Connecting to database...")
        
        try:
            conn = await asyncpg.connect(database_url)
            print("Connected successfully")
        except Exception as e:
            print(f"ERROR: Failed to connect: {e}")
            return False
        
        try:
            for migration_file in migration_files:
                print(f"\nRunning: {migration_file.name}")
                
                # Read SQL
                sql = migration_file.read_text(encoding="utf-8")
                
                # Split into statements (simple split by semicolon)
                # Note: This is basic - doesn't handle semicolons in strings
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                
                success_count = 0
                error_count = 0
                
                for i, statement in enumerate(statements):
                    if not statement or statement.startswith("--"):
                        continue
                    
                    try:
                        await conn.execute(statement)
                        success_count += 1
                    except asyncpg.exceptions.DuplicateObjectError as e:
                        # Object already exists - that's OK for idempotent migrations
                        print(f"  [SKIP] Already exists: {str(e)[:60]}...")
                    except asyncpg.exceptions.DuplicateTableError:
                        print(f"  [SKIP] Table already exists")
                    except Exception as e:
                        error_str = str(e)
                        if "already exists" in error_str.lower():
                            print(f"  [SKIP] {error_str[:60]}...")
                        else:
                            print(f"  [ERROR] Statement {i+1}: {error_str[:80]}")
                            error_count += 1
                
                print(f"  Completed: {success_count} statements, {error_count} errors")
            
            return True
            
        finally:
            await conn.close()
    
    return asyncio.run(execute_migrations())


if __name__ == "__main__":
    print("=" * 50)
    print("DCAI Intelligence Platform - Database Migrations")
    print("=" * 50)
    print()
    
    success = run_migrations()
    
    print()
    print("=" * 50)
    if success:
        print("Migrations completed!")
    else:
        print("Migrations failed!")
    
    sys.exit(0 if success else 1)
